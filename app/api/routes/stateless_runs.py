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
from typing import Union, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from pydantic import ValidationError, BaseModel, Field

from agent_workflow_server.generated.models.content import Content as SrvContent
from agent_workflow_server.generated.models.message import Message as SrvMessage
from agent_workflow_server.generated.models.run_create_stateless import (
    RunCreateStateless as SrvRunCreateStateless,
)
from agent_workflow_server.generated.models.run_output import RunOutput as SrvRunOutput
from agent_workflow_server.generated.models.run_result import RunResult as SrvRunResult
from agent_workflow_server.generated.models.run_stateless import (
    RunStateless as SrvRunStateless,
)
from agent_workflow_server.generated.models.run_status import RunStatus as SrvRunStatus
from agent_workflow_server.generated.models.run_wait_response_stateless import (
    RunWaitResponseStateless as SrvRunWaitResponseStateless,
)
from app.core.config import settings
from app.models.models import (
    ErrorResponse,
    ReviewComments,
    ReviewRequest,
    ReviewResponse,
    RunCreateStateless,
)
from app.utils.wrap_prompt import wrap_prompt

router = APIRouter(tags=["Stateless Runs"])
logger = logging.getLogger(__name__)  # This will be "app.api.routes.<name>"
# Error messages
INTERNAL_ERROR_MESSAGE = "An unexpected error occurred. Please try again later."


class codeReviewInput(BaseModel):
    files: Optional[list[dict]] = Field(default_factory=list,
                                        description="""receive all the Terraform files from the user in the "FILES" list..""")
    changes: list[dict] = Field(
        description="""
        List of code changes across Terraform files. The changes have the following format:
            - filename: the name of the file where the change was done
            - start_line: the line number where the change was added
            - changed_code: the code that was removed/added after the start line, there's a + or - sign at the beginning of every change line, it indicates if it was added or removed, ignore this sign.
            - status: indicates if the changed_code was added/removed
            - Changes with "removed" status mean that the code in that change was deleted from the codebase, it's not part of the code anymore.
            - Changes with "added" status mean that the code in that change was added the codebase.
            - Always focus on whether a change was added or removed from the codebase. If it was removed then that code is not part of the codebase anymore.
            - Sometimes the changes are in pairs, one change with a 'removed' status and one with 'added', but they belong together, even when their line numbers are far apart.
            Identify these pairs and DO NOT add the same comment to the removed and added part twice!
            """)
    static_analyzer_output: list[str] = Field(
        description="""
        - A list of multiple static code analyzers (tflint, tfsec, etc.) on the new code.
        - The static_analyzer_output could be useful for understanding the potential issues introduced by the user, like missing references, undefined or unused variables etc.
        - The static_analyzer_output could have issues which are not related to the current code changes, you MUST ignore these issues as they weren't introduced by this PR.
        """
    )


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


@staticmethod
def get_model_dump_with_metadata(model_instance):
    data = model_instance.model_dump()
    metadata = model_instance.model_fields

    result = {}
    for field_name, value in data.items():
        description = metadata[field_name].description
        result[field_name] = {
            f"{field_name}value": value,
            f"{field_name}_description": description
        }
    return result


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

        logger.debug(f"Received request: {body.model_dump()}")

        if isinstance(body.input, dict) and "messages" in body.input:
            messages = body.input["messages"]
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid input format: 'messages' field is missing or input is not a dictionary.",
            )
        first_message = messages[0]

        review_request_data = json.loads(first_message.content)
        logger.info(f"Received review request: {review_request_data}")
        # Convert to `ReviewRequest` model
        try:
            review_request = ReviewRequest.model_validate(review_request_data)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e}",
            ) from e
        # Extract fields
        context_files = review_request.context_files
        changes = review_request.changes
        static_analyzer_output = review_request.static_analyzer_output

        # if not context_files or not changes or not static_analyzer_output:
        #     raise HTTPException(
        #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        #         detail="Missing required fields: context_files, changes, or static_analyzer_output.",
        #     )

        logger.info("Received valid request. Processing code review.")

        # ---- Code Reviewer Logic ----
        # Construct LLM prompt
        code_review = codeReviewInput(files=review_request.context_files, changes=review_request.changes,
                                     static_analyzer_output=[review_request.static_analyzer_output])

        print("The final value of code_review" , get_model_dump_with_metadata(code_review).items())

        response: ReviewComments = code_reviewer_chain.invoke(get_model_dump_with_metadata(code_review).items())

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
        ) from exc

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

    logger.debug(f"Returning review response: {payload.model_dump()}")

    return payload


# ACP Endpoint
@router.post(
    "/runs/wait",
    responses={
        200: {"model": SrvRunWaitResponseStateless, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Create a stateless run and wait for its output",
    response_model_by_alias=True,
)
async def create_and_wait_for_stateless_run_output(
        body: SrvRunCreateStateless, request: Request
) -> SrvRunWaitResponseStateless:
    """
    Create Run, Wait for Output
    """
    try:
        app = request.app
        code_reviewer_chain = get_code_reviewer_chain(app)

        # Extract `ReviewRequest` structured input

        logger.debug(f"Received request: {body.model_dump()}")

        if isinstance(body.input, dict) and "messages" in body.input:
            messages = body.input["messages"]
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid input format: 'messages' field is missing or input is not a dictionary.",
            )
        first_message = messages[0]

        review_request_data = json.loads(first_message["content"])
        logger.info(f"Received review request: {review_request_data}")
        # Convert to `ReviewRequest` model
        try:
            review_request = ReviewRequest.model_validate(review_request_data)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {e}",
            ) from e
        # Extract fields

        logger.info("Received valid request. Processing code review.")

        # ---- Code Reviewer Logic ----
        # Construct LLM prompt
        code_review = codeReviewInput(files=review_request.context_files, changes=review_request.changes,
                                      static_analyzer_output=[review_request.static_analyzer_output])

        print("The final value of code_review", get_model_dump_with_metadata(code_review).items())

        response: ReviewComments = code_reviewer_chain.invoke(get_model_dump_with_metadata(code_review).items())
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
        ) from exc

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
        model="gpt-4o",
        metadata={
            "id": (
                body.metadata.get("id", "default-id") if body.metadata else "default-id"
            )
        },
    )

    logger.debug(f"Returning review response: {payload.model_dump()}")

    try:
        # Build WrkFlow Srv Run Output
        message = SrvMessage(
            role="ai", content=SrvContent(json.dumps(filtered_comments))
        )
        run_result = SrvRunResult(type="result", messages=[message])
        run_output = SrvRunOutput(run_result)
        logger.info(run_output.model_dump_json(indent=2))
    except HTTPException as http_exc:
        logger.error(
            "HTTP error during run processing: %s", http_exc.detail, exc_info=True
        )
        raise http_exc
    except Exception as exc:
        logger.error("Internal error during run processing: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=INTERNAL_ERROR_MESSAGE,
        ) from exc
    current_datetime = datetime.now(tz=timezone.utc)
    run_stateless = SrvRunStateless(
        run_id=str(body.metadata.get("id", "")) if body.metadata else "",
        agent_id=body.agent_id or "",
        created_at=current_datetime,
        updated_at=current_datetime,
        status=SrvRunStatus.SUCCESS,
        creation=body,
    )
    return SrvRunWaitResponseStateless(run=run_stateless, output=run_output)
