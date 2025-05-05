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

"""
stateless_client.py

This modules contains a sample graph client that makes a stateless
ACP request to the Remote Graph Server.

Usage: python stateless_client.py

The resource URL at /runs/wait will be invoked on the Remote Graph Server.
"""

import json
import os
import traceback
import uuid
from typing import Any, Dict, TypedDict

from agntcy_acp import ACPClient, ApiClientConfiguration
from agntcy_acp.acp_v0.sync_client.api_client import ApiClient
from agntcy_acp.acp_v0.models import RunCreateStateless, RunError, RunResult
from langgraph.graph import END, START, StateGraph

from dotenv import find_dotenv, load_dotenv
from client.utils.logging_config import configure_logging
from app.models.models import ReviewRequest


logger = configure_logging(log_filename=__file__.replace(".py", ".log"))


def fetch_github_environment_variables() -> Dict[str, str | None]:
    """
    Fetches the GitHub environment variables from the system.

    Returns:
        Dict[str, str]: A dictionary containing the GitHub environment variables.
    """
    github_details = {
        "repo_url": os.getenv("GH_REPO_URL"),
        "github_token": os.getenv("GH_TOKEN"),
        "branch": os.getenv("GH_BRANCH", "main"),
    }
    return github_details


# Define the graph state
class GraphState(TypedDict):
    """Represents the state of the graph, containing the file_path."""

    review_request: Dict[str, str]
    code_reviewer_output: str


def node_remote_request_stateless(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles a stateless request to the Remote Graph Server.

    Args:
        state (Dict[str, Any]): The current state of the graph.

    Returns:
        Dict[str, Any]: The updated state of the graph after processing the request.
    """
    if "review_request" not in state or not state["review_request"]:
        error_msg = "GraphState is missing 'review_request' key"
        logger.error(json.dumps({"error": error_msg}))
        return {"error": error_msg}

    # ACP
    remote_agent_id = "remote_agent"
    client_config = ApiClientConfiguration.fromEnvPrefix("ACP_TF_CODE_REVIEWER_")
    run_create = RunCreateStateless(
        agent_id=remote_agent_id,
        input={"github_details": state["github_details"]},
        metadata={"id": str(uuid.uuid4())},
    )

    with ApiClient(configuration=client_config) as api_client:
        acp_client = ACPClient(api_client=api_client)
        try:
            run_output = acp_client.create_and_wait_for_stateless_run_output(run_create)
            if run_output.output is None:
                raise ValueError("Run output is None")
            actual_output = run_output.output.actual_instance
            if isinstance(actual_output, RunResult):
                run_result: RunResult = actual_output
                sao = (
                    run_result.values.get("static_analyzer_output", "")
                    if run_result.values
                    else ""
                )
            elif isinstance(actual_output, RunError):
                run_error: RunError = actual_output
                raise Warning(f"Run Failed: {run_error}")
            else:
                raise ValueError(
                    f"ACP Server returned a unsupported response: {run_output}"
                )
            return {"static_analyzer_output": sao}

        except Exception as e:
            error_msg = "Unexpected failure"
            logger.error(
                json.dumps(
                    {
                        "error": error_msg,
                        "exception": str(e),
                        "stack_trace": traceback.format_exc(),
                    }
                )
            )
            return {"error": error_msg}


def build_graph() -> Any:
    """
    Constructs the state graph for handling request with the Remote Graph Server.

    Returns:
        StateGraph: A compiled LangGraph state graph.
    """
    builder = StateGraph(GraphState)
    builder.add_node("node_remote_request_stateless", node_remote_request_stateless)
    builder.add_edge(START, "node_remote_request_stateless")
    builder.add_edge("node_remote_request_stateless", END)
    return builder.compile()


def main():
    """Main function to set up and invoke the graph."""
    env_path = find_dotenv()

    if env_path:
        load_dotenv(env_path, override=True)
        logger.info(f".env file loaded from {env_path}")
    else:
        raise ValueError("No .env file found. Ensure environment variables are set.")

    graph = build_graph()

    CONTEXT_FILES = [
        {
            "path": "example.tf",
            "content": """
        resource "aws_s3_bucket" "example" {
        bucket = "my-public-bucket"
        acl    = "public-read"
        """,
        }
    ]

    CHANGES = [
        {
            "file": "example.tf",
            "content": """
    resource "aws_security_group" "example" {
    name        = "example-sg"
    description = "Security group with open ingress"

    ingress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
    }
    """,
        }
    ]

    ANALYSIS_REPORTS = (
        "Security Warning: The security group allows unrestricted ingress (0.0.0.0/0)."
    )

    review_request = ReviewRequest(
        context_files=CONTEXT_FILES,
        changes=CHANGES,
        static_analyzer_output=ANALYSIS_REPORTS,
    )
    logger.info({"event": "invoking_graph", "input": review_request.model_dump_json()})

    result = graph.invoke({"review_request": review_request.model_dump()})

    logger.info(
        {
            "event": "final_result",
            "result": result.get("code_reviewer_output", result),
        }
    )


if __name__ == "__main__":
    main()
