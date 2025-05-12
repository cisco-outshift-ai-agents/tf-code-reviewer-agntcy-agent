# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from agp_api.agent.agent_container import AgentContainer
from agp_api.gateway.gateway_container import GatewayContainer
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute
from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pydantic import SecretStr
from starlette.middleware.cors import CORSMiddleware
from app.utils.chain import create_code_reviewer_chain

from app.api.routes.stateless_runs import router as stateless_runs_router
from app.core.config import settings
from app.core.logging_config import configure_logging

# Initialize logger
logger = logging.getLogger("app")


class Config:
    """Configuration class for AGP (Agent Gateway Protocol) client.
    This class manages configuration settings for the AGP system, containing container
    instances for gateway and agent management, as well as remote agent specification.
    Attributes:
        gateway_container (GatewayContainer): Container instance for gateway management
        agent_container (AgentContainer): Container instance for agent management
        remote_agent (str): Specification of remote agent, defaults to "server"
    """

    remote_agent = "tf_code_reviewer"
    gateway_container = GatewayContainer()
    agent_container = AgentContainer(local_agent=remote_agent)


def load_environment_variables(env_file: str | None = None) -> None:
    """
    Load environment variables from a .env file safely.

    This function loads environment variables from a `.env` file, ensuring
    that critical configurations are set before the application starts.

    Args:
        env_file (str | None): Path to a specific `.env` file. If None,
                               it searches for a `.env` file automatically.

    Behavior:
    - If `env_file` is provided, it loads the specified file.
    - If `env_file` is not provided, it attempts to locate a `.env` file in the project directory.
    - Logs a warning if no `.env` file is found.

    Returns:
        None
    """
    env_path = env_file or find_dotenv()

    if env_path:
        load_dotenv(env_path, override=True)
        logging.info(f".env file loaded from {env_path}")
    else:
        logging.warning("No .env file found. Ensure environment variables are set.")


def initialize_chain() -> BaseChatModel:
    """
    Initializes the LLM chain based on the available OpenAI or Azure OpenAI credentials.

    Returns:
        BaseChatModel: Initialized LLM chain instance.
    """
    USE_AZURE = all(
        [
            settings.AZURE_OPENAI_API_KEY,
            settings.AZURE_OPENAI_ENDPOINT,
            settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            settings.AZURE_OPENAI_API_VERSION,
            settings.AZURE_OPENAI_TEMPERATURE,
        ]
    )

    if USE_AZURE:
        logging.info("Using Azure OpenAI GPT-4o for Code Review.")
        # Initialize Azure OpenAI model
        llm_chain: BaseChatModel = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            temperature=settings.AZURE_OPENAI_TEMPERATURE,
        )
    else:
        logging.info("Using OpenAI GPT-4o for Code Review.")
        # Initialize OpenAI GPT model
        llm_chain = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"),
            api_key=(
                SecretStr(os.getenv("OPENAI_API_KEY", "gpt-4o"))
                if os.getenv("OPENAI_API_KEY")
                else None
            ),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", 0.7)),
        )

    return create_code_reviewer_chain(llm_chain)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Defines startup and shutdown logic for the FastAPI application.

    This function follows the `lifespan` approach, allowing resource initialization
    before the server starts and cleanup after it shuts down.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: The application runs while `yield` is active.

    Behavior:
    - On startup: Logs a startup message.
    - On shutdown: Logs a shutdown message.
    - Can be extended to initialize resources (e.g., database connections).
    """
    logging.info("Starting TF Code Reviewer Agent...")

    # Example: Attach database connection to app state (if needed)
    # app.state.db = await init_db_connection()

    # Initialize the LLM Chain and store it in app state
    app.state.code_reviewer_chain = initialize_chain()

    # Start AGP server now that app.state is initialized
    asyncio.create_task(start_agp_server(app))

    yield  # Application runs while 'yield' is in effect.

    logging.info("Application shutdown")

    # Example: Close database connection (if needed)
    # await app.state.db.close()


def custom_generate_unique_id(route: APIRoute) -> str:
    """
    Generates a unique identifier for API routes.

    Args:
        route (APIRoute): The FastAPI route object.

    Returns:
        str: A unique string identifier for the route.

    Behavior:
    - If the route has tags, the ID is formatted as `{tag}-{route_name}`.
    - If no tags exist, the route name is used as the ID.
    """
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    return route.name


def add_handlers(app: FastAPI) -> None:
    """
    Adds global route handlers to the FastAPI application.

    This function registers common endpoints, such as the root message
    and the favicon.

    Args:
        app (FastAPI): The FastAPI application instance.

    Returns:
        None
    """

    @app.get(
        "/",
        summary="Root endpoint",
        description="Returns a welcome message for the API.",
        tags=["General"],
    )
    async def root() -> dict:
        """
        Root endpoint that provides a welcome message.

        Returns:
            dict: A JSON response with a greeting message.
        """
        return {"message": "Gateway of the App"}

    @app.get("/favicon.png", include_in_schema=False)
    async def favicon() -> FileResponse:
        """
        Serves the favicon as a PNG file.

        This prevents the browser from repeatedly requesting a missing
        favicon when accessing the API.

        Returns:
            FileResponse: A response serving the `favicon.png` file.

        Raises:
            FileNotFoundError: If the favicon file is missing.
        """
        file_name = "favicon.png"
        file_path = os.path.join(app.root_path, "", file_name)
        return FileResponse(
            path=file_path, media_type="image/png"  # Ensures it's served inline
        )


def create_fastapi_app() -> FastAPI:
    """
    Creates and configures the FastAPI application instance.

    This function sets up:
    - The API metadata (title, version, OpenAPI URL).
    - CORS middleware to allow cross-origin requests.
    - Route handlers for API endpoints.
    - A custom unique ID generator for API routes.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        generate_unique_id_function=custom_generate_unique_id,
        version="0.1.0",
        description=settings.PROJECT_NAME,
        lifespan=lifespan,  # Use the new lifespan approach for startup/shutdown
    )

    add_handlers(app)
    app.include_router(stateless_runs_router, prefix=settings.API_V1_STR)

    # Set all CORS enabled origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    return app


async def start_agp_server(app: FastAPI) -> None:
    """
    Initializes and starts the AGP Gateway server.
    """
    logger.info("Starting AGP application...")

    Config.gateway_container.set_config(
        endpoint=settings.AGP_GATEWAY_URL, insecure=True
    )
    Config.gateway_container.set_fastapi_app(app)

    _ = await Config.gateway_container.connect_with_retry(
        agent_container=Config.agent_container,
        max_duration=10,
        initial_delay=1,
        remote_agent=Config.remote_agent,
    )

    try:
        await Config.gateway_container.start_server(
            agent_container=Config.agent_container
        )
    except RuntimeError as e:
        logger.error("Runtime error: %s", e)
    except Exception as e:
        logger.info("Unhandled error: %s", e)


async def main() -> None:
    """
    Runs both FastAPI and AGP servers.
    """

    load_environment_variables()

    _ = configure_logging()

    logger.info("Starting FastAPI application...")

    # Determine port number from environment variables or use the default
    port = int(os.getenv("TF_CODE_REVIEWER_PORT", "8123"))
    host = os.getenv("TF_CODE_REVIEWER_HOST", "0.0.0.0")

    # Start the FastAPI application using Uvicorn
    uvicorn_config = uvicorn.Config(
        create_fastapi_app(),
        host=host,
        port=port,
        log_level="info",
    )

    server = uvicorn.Server(uvicorn_config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())