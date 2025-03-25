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

import json
import logging
from typing import Any, Union

from core.config import settings
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from models.models import (
    ErrorResponse,
    ReviewComments,
    ReviewRequest,
    ReviewResponse,
    RunCreateStateless,
)
from utils.wrap_prompt import wrap_prompt

router = APIRouter(tags=["Stateless Runs"])
logger = logging.getLogger(__name__)  # This will be "app.api.routes.<name>"


def get_code_reviewer_chain(app: FastAPI):
    """
    Retrieves the initialized CodeReviewer instance from FastAPI app state.

    Args:
        app (FastAPI): The FastAPI application instance.

    Returns:
        CodeReviewer: The initialized CodeReviewer instance.
    """
    code_reviewer_chain = app.state.code_reviewer_chain
    if code_reviewer_chain is None:
        raise HTTPException(status_code=500, detail="CodeReviewer not initialized")
    return code_reviewer_chain


@router.post(
    "/runs",
    response_model=ReviewResponse,
    responses={
        "404": {"model": ErrorResponse},
        "409": {"model": ErrorResponse},
        "422": {"model": ErrorResponse},
    },
    tags=["Stateless Runs"],
)
def run_stateless_runs_post(
    body: RunCreateStateless, request: Request
) -> Union[ReviewResponse, ErrorResponse]:
    """
    Create Background Run
    """
    try:
        app = request.app
        code_reviewer_chain = get_code_reviewer_chain(app)

        # Extract `ReviewRequest` structured input
        agent_id = body.agent_id
        logging.debug("Agent id: %s", agent_id)
        message_id = body.metadata.get("id", "default-id")
        logging.debug("Message id: %s", message_id)

        logger.info(f"Received request: {body.model_dump()}")

        messages = body.input["messages"]
        first_message = messages[0]

        review_request_data = json.loads(first_message.content)
        logger.info(f"Received review request: {review_request_data}")
        # Convert to `ReviewRequest` model
        review_request = ReviewRequest.model_validate(review_request_data)
        # Extract fields
        context_files = review_request.context_files
        changes = review_request.changes
        static_analyzer_output = review_request.static_analyzer_output

        if not context_files or not changes or not static_analyzer_output:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Missing required fields: context_files, changes, or static_analyzer_output.",
            )

        logger.info("Received valid request. Processing code review.")

        # ---- Code Reviewer Logic ----
        # Construct LLM prompt

        response: ReviewComments = code_reviewer_chain.invoke(
            {
                "question": wrap_prompt(
                    "FILES:",
                    f"{'\n'.join(map(str, context_files))}",
                    "",
                    "CHANGES:" f"{changes}",
                    "",
                    "STATIC_ANALYZER_OUTPUT:",
                    f"{static_analyzer_output}",
                )
            }
        )

    except HTTPException as http_exc:
        # Log HTTP exceptions and re-raise them so that FastAPI can generate the appropriate response.
        logging.error("HTTP error during run processing: %s", http_exc.detail)
        raise http_exc

    except Exception as exc:
        # Catch unexpected exceptions, log them, and return a 500 Internal Server Error.
        logging.exception("An unexpected error occurred while processing the run.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc,
        )

    # Construct structured response from the code review comments
    filtered_comments = [
        comment.model_dump() for comment in response.issues if comment.line_number != 0
    ]

    payload = ReviewResponse(
        agent_id=body.agent_id or "default-agent",
        output={
            "messages": [
                {"role": "assistant", "content": json.dumps(filtered_comments)}
            ]
        },
        model=body.model or "gpt-4o",
        metadata={
            "id": (
                body.metadata.get("id", "default-id") if body.metadata else "default-id"
            )
        },
    )

    logger.info(f"Returning review response: {payload.model_dump()}")

    return payload


@router.post(
    "/runs/stream",
    response_model=str,
    responses={
        "404": {"model": ErrorResponse},
        "409": {"model": ErrorResponse},
        "422": {"model": ErrorResponse},
    },
    tags=["Stateless Runs"],
)
def stream_run_stateless_runs_stream_post(
    body: RunCreateStateless,
) -> Union[str, ErrorResponse]:
    """
    Create Run, Stream Output
    """
    pass


@router.post(
    "/runs/wait",
    response_model=Any,
    responses={
        "404": {"model": ErrorResponse},
        "409": {"model": ErrorResponse},
        "422": {"model": ErrorResponse},
    },
    tags=["Stateless Runs"],
)
def wait_run_stateless_runs_wait_post(
    body: RunCreateStateless,
) -> Union[Any, ErrorResponse]:
    """
    Create Run, Wait for Output
    """
    pass
