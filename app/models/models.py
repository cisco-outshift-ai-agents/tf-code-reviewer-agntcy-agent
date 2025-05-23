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

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import (
    AnyUrl,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    conint,
)


class ReviewComment(BaseModel):
    filename: str
    line_number: int
    comment: str
    status: str


class ReviewComments(BaseModel):
    issues: List[ReviewComment] = Field(description="List of code review issues found")


class ReviewRequest(BaseModel):
    """Expected input format for code reviewer"""

    context_files: List[Dict[str, Any]]
    changes: List[Dict[str, Any]]
    static_analyzer_output: Optional[str]


class ReviewResponse(BaseModel):
    agent_id: str = Field(..., description="The agent that generated the response")
    output: Dict[str, Any] = Field(..., description="List of review comments")
    model: str = Field(..., description="Model used for code review")
    metadata: Dict[str, Any] = Field(
        ..., description="Additional metadata related to the response"
    )


class Agent(BaseModel):
    agent_id: str = Field(..., description="The ID of the agent.", title="Agent Id")
    name: str = Field(..., description="The name of the agent", title="Agent Name")
    description: Optional[str] = Field(
        None, description="The description of the agent.", title="Description"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="The agent metadata.", title="Metadata"
    )


class AgentSchemas(BaseModel):
    agent_id: str = Field(..., description="The ID of the agent.", title="Agent Id")
    input_schema: Dict[str, Any] = Field(
        ...,
        description="The schema for the agent input. In JSON Schema format.",
        title="Input Schema",
    )
    output_schema: Dict[str, Any] = Field(
        ...,
        description="The schema for the agent output. In JSON Schema format.",
        title="Output Schema",
    )
    state_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="The schema for the agent's internal state. In JSON Schema format.",
        title="State Schema",
    )
    config_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="The schema for the agent config. In JSON Schema format.",
        title="Config Schema",
    )


class Status(Enum):
    pending = "pending"
    error = "error"
    success = "success"
    timeout = "timeout"
    interrupted = "interrupted"


class MultitaskStrategy(Enum):
    reject = "reject"
    rollback = "rollback"
    interrupt = "interrupt"
    enqueue = "enqueue"


class Run(BaseModel):
    run_id: UUID = Field(..., description="The ID of the run.", title="Run Id")
    thread_id: UUID = Field(..., description="The ID of the thread.", title="Thread Id")
    agent_id: Optional[str] = Field(
        None, description="The agent that was used for this run.", title="Agent Id"
    )
    created_at: AwareDatetime = Field(
        ..., description="The time the run was created.", title="Created At"
    )
    updated_at: AwareDatetime = Field(
        ..., description="The last time the run was updated.", title="Updated At"
    )
    status: Status = Field(
        ...,
        description="The status of the run. One of 'pending', 'error', 'success', 'timeout', 'interrupted'.",
        title="Status",
    )
    metadata: Dict[str, Any] = Field(
        ..., description="The run metadata.", title="Metadata"
    )
    kwargs: Dict[str, Any] = Field(..., title="Kwargs")
    multitask_strategy: MultitaskStrategy = Field(
        ...,
        description="Strategy to handle concurrent runs on the same thread.",
        title="Multitask Strategy",
    )


class Config(BaseModel):
    tags: Optional[List[str]] = Field(None, title="Tags")
    recursion_limit: Optional[int] = Field(None, title="Recursion Limit")
    configurable: Optional[Dict[str, Any]] = Field(None, title="Configurable")


class StreamModeEnum(Enum):
    values = "values"
    messages_tuple = "messages-tuple"
    updates = "updates"
    debug = "debug"
    custom = "custom"


class StreamMode(Enum):
    values = "values"
    messages_tuple = "messages-tuple"
    updates = "updates"
    debug = "debug"
    custom = "custom"


class OnDisconnect(Enum):
    cancel = "cancel"
    continue_ = "continue"


class IfNotExists(Enum):
    create = "create"
    reject = "reject"


class RunCreateStateful(BaseModel):
    agent_id: Optional[str] = Field(
        None,
        description="The agent ID to run. If not provided will use the default agent for this service.",
        title="Agent Id",
    )
    input: Optional[Union[Dict[str, Any], List, str, float, bool]] = Field(
        None, description="The input to the graph.", title="Input"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Metadata to assign to the run.", title="Metadata"
    )
    config: Optional[Config] = Field(
        None, description="The configuration for the agent.", title="Config"
    )
    webhook: Optional[AnyUrl] = Field(
        None, description="Webhook to call after run finishes.", title="Webhook"
    )
    stream_mode: Optional[Union[List[StreamModeEnum], StreamMode]] = Field(
        ["values"], description="The stream mode(s) to use.", title="Stream Mode"
    )
    stream_subgraphs: Optional[bool] = Field(
        False,
        description="Whether to stream output from subgraphs.",
        title="Stream Subgraphs",
    )
    on_disconnect: Optional[OnDisconnect] = Field(
        "cancel",
        description="The disconnect mode to use. Must be one of 'cancel' or 'continue'.",
        title="On Disconnect",
    )
    multitask_strategy: Optional[MultitaskStrategy] = Field(
        "reject",
        description="Multitask strategy to use. Must be one of 'reject', 'interrupt', 'rollback', or 'enqueue'.",
        title="Multitask Strategy",
    )
    if_not_exists: Optional[IfNotExists] = Field(
        "reject",
        description="How to handle missing thread. Must be either 'reject' (raise error if missing), or 'create' (create new thread).",
        title="If Not Exists",
    )
    after_seconds: Optional[int] = Field(
        None,
        description="The number of seconds to wait before starting the run. Use to schedule future runs.",
        title="After Seconds",
    )


class OnCompletion(Enum):
    delete = "delete"
    keep = "keep"


# Duplicated definition of Message class.
class Message(BaseModel):
    """Represents an AI conversation message"""

    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(
        ...,
        description="Message content, which could be a string or a structured ReviewRequest",
    )


class RunCreateStateless(BaseModel):
    agent_id: Optional[str] = Field(
        None,
        description="The agent ID to run. If not provided will use the default agent for this service.",
        title="Agent Id",
    )
    # RP: It seems like the input is always a list of messages, so we can use that directly.
    # input: Union[ReviewRequest, Dict[str, List[Message]]] = Field(
    #     ...,
    #     description="Structured input for the agent (either ReviewRequest or messages)",
    # )
    input: Dict[str, List[Message]] = Field(
        ...,
        description="Structured input for the agent (either ReviewRequest or messages)",
    )
    model: str = Field(..., description="Model used for the response (e.g., gpt-4o).")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Metadata to assign to the run.", title="Metadata"
    )
    route: str = Field(
        ...,  # This makes the field required
        description="The API route where the request should be sent.",
        title="Route",
    )
    config: Optional[Config] = Field(
        None, description="The configuration for the agent.", title="Config"
    )
    webhook: Optional[AnyUrl] = Field(
        None, description="Webhook to call after run finishes.", title="Webhook"
    )
    stream_mode: Optional[Union[List[StreamModeEnum], StreamMode]] = Field(
        ["values"], description="The stream mode(s) to use.", title="Stream Mode"
    )
    on_completion: Optional[OnCompletion] = Field(
        "delete",
        description="Whether to delete or keep the thread created for a stateless run. Must be one of 'delete' or 'keep'.",
        title="On Completion",
    )
    on_disconnect: Optional[OnDisconnect] = Field(
        "cancel",
        description="The disconnect mode to use. Must be one of 'cancel' or 'continue'.",
        title="On Disconnect",
    )
    multitask_strategy: Optional[MultitaskStrategy] = Field(
        "reject",
        description="Multitask strategy to use. Must be one of 'reject', 'interrupt', 'rollback', or 'enqueue'.",
        title="Multitask Strategy",
    )
    after_seconds: Optional[int] = Field(
        None,
        description="The number of seconds to wait before starting the run. Use to schedule future runs.",
        title="After Seconds",
    )


class Status1(Enum):
    idle = "idle"
    busy = "busy"
    interrupted = "interrupted"
    error = "error"


class ThreadSearchRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Thread metadata to filter on.", title="Metadata"
    )
    values: Optional[Dict[str, Any]] = Field(
        None, description="State values to filter on.", title="Values"
    )
    status: Optional[Status1] = Field(
        None, description="Thread status to filter on.", title="Status"
    )
    limit: Optional[conint(ge=1, le=1000)] = Field(
        10, description="Maximum number to return.", title="Limit"
    )
    offset: Optional[conint(ge=0)] = Field(
        0, description="Offset to start from.", title="Offset"
    )


class ThreadCheckpoint(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    checkpoint_id: UUID = Field(
        ..., description="The ID of the checkpoint.", title="Checkpoint Id"
    )


class IfExists(Enum):
    raise_ = "raise"
    do_nothing = "do_nothing"


class ThreadCreate(BaseModel):
    thread_id: Optional[UUID] = Field(
        None,
        description="The ID of the thread. If not provided, a random UUID will be generated.",
        title="Thread Id",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Metadata to add to thread.", title="Metadata"
    )
    if_exists: Optional[IfExists] = Field(
        "raise",
        description="How to handle duplicate creation. Must be either 'raise' (raise error if duplicate), or 'do_nothing' (return existing thread).",
        title="If Exists",
    )


class StorePutRequest(BaseModel):
    namespace: List[str] = Field(
        ...,
        description="A list of strings representing the namespace path.",
        title="Namespace",
    )
    key: str = Field(
        ...,
        description="The unique identifier for the item within the namespace.",
        title="Key",
    )
    value: Dict[str, Any] = Field(
        ..., description="A dictionary containing the item's data.", title="Value"
    )


class StoreDeleteRequest(BaseModel):
    namespace: Optional[List[str]] = Field(
        None,
        description="A list of strings representing the namespace path.",
        title="Namespace",
    )
    key: str = Field(
        ..., description="The unique identifier for the item.", title="Key"
    )


class StoreSearchRequest(BaseModel):
    namespace_prefix: Optional[List[str]] = Field(
        None,
        description="List of strings representing the namespace prefix.",
        title="Namespace Prefix",
    )
    filter: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional dictionary of key-value pairs to filter results.",
        title="Filter",
    )
    limit: Optional[int] = Field(
        10,
        description="Maximum number of items to return (default is 10).",
        title="Limit",
    )
    offset: Optional[int] = Field(
        0,
        description="Number of items to skip before returning results (default is 0).",
        title="Offset",
    )


class StoreListNamespacesRequest(BaseModel):
    prefix: Optional[List[str]] = Field(
        None,
        description="Optional list of strings representing the prefix to filter namespaces.",
        title="Prefix",
    )
    suffix: Optional[List[str]] = Field(
        None,
        description="Optional list of strings representing the suffix to filter namespaces.",
        title="Suffix",
    )
    max_depth: Optional[int] = Field(
        None,
        description="Optional integer specifying the maximum depth of namespaces to return.",
        title="Max Depth",
    )
    limit: Optional[int] = Field(
        100,
        description="Maximum number of namespaces to return (default is 100).",
        title="Limit",
    )
    offset: Optional[int] = Field(
        0,
        description="Number of namespaces to skip before returning results (default is 0).",
        title="Offset",
    )


class Item(BaseModel):
    namespace: List[str] = Field(
        ...,
        description="The namespace of the item. A namespace is analogous to a document's directory.",
    )
    key: str = Field(
        ...,
        description="The unique identifier of the item within its namespace. In general, keys needn't be globally unique.",
    )
    value: Dict[str, Any] = Field(
        ..., description="The value stored in the item. This is the document itself."
    )
    created_at: AwareDatetime = Field(
        ..., description="The timestamp when the item was created."
    )
    updated_at: AwareDatetime = Field(
        ..., description="The timestamp when the item was last updated."
    )


class Content(BaseModel):
    text: str
    type: Literal["text"]
    metadata: Optional[Dict[str, Any]] = None


class Content1(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    type: str
    metadata: Optional[Dict[str, Any]] = None


# class Message(BaseModel):
#     model_config = ConfigDict(
#         extra="allow",
#     )
#     role: str = Field(..., description="The role of the message.", title="Role")
#     content: Union[str, List[Union[Content, Content1]]] = Field(
#         ..., description="The content of the message.", title="Content"
#     )
#     id: Optional[str] = Field(None, description="The ID of the message.", title="Id")
#     metadata: Optional[Dict[str, Any]] = Field(
#         None, description="The metadata of the message.", title="Metadata"
#     )


class SearchItemsResponse(BaseModel):
    items: List[Item]


class ListNamespaceResponse(RootModel[List[List[str]]]):
    root: List[List[str]]


class ErrorResponse(RootModel[str]):
    root: str = Field(
        ..., description="Error message returned from the server", title="ErrorResponse"
    )


class AgentsSearchPostRequest(BaseModel):
    name: Optional[str] = Field(None, description="Name of the agent to search.")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Metadata of the agent to search."
    )
    limit: Optional[conint(ge=1, le=1000)] = Field(
        10, description="Maximum number to return.", title="Limit"
    )
    offset: Optional[conint(ge=0)] = Field(
        0, description="Offset to start from.", title="Offset"
    )


class AgentsSearchPostResponse(RootModel[List[Agent]]):
    root: List[Agent] = Field(..., title="Response List Agents")


class ThreadsThreadIdRunsGetResponse(RootModel[List[Run]]):
    root: List[Run]


class Action(Enum):
    interrupt = "interrupt"
    rollback = "rollback"


class Namespace(RootModel[List[str]]):
    root: List[str]


class Thread(BaseModel):
    thread_id: UUID = Field(..., description="The ID of the thread.", title="Thread Id")
    created_at: AwareDatetime = Field(
        ..., description="The time the thread was created.", title="Created At"
    )
    updated_at: AwareDatetime = Field(
        ..., description="The last time the thread was updated.", title="Updated At"
    )
    metadata: Dict[str, Any] = Field(
        ..., description="The thread metadata.", title="Metadata"
    )
    status: Status1 = Field(
        ..., description="The status of the thread.", title="Status"
    )
    values: Optional[Dict[str, Any]] = Field(
        None, description="The current state of the thread.", title="Values"
    )
    messages: Optional[List[Message]] = Field(
        None,
        description="The current Messages of the thread. If messages are contained in Thread.values, implementations should remove them from values when returning messages. When this key isn't present it means the thread/agent doesn't support messages.",
        title="Messages",
    )


class ThreadState(BaseModel):
    checkpoint: ThreadCheckpoint = Field(
        ..., description="The identifier for this checkpoint.", title="Checkpoint"
    )
    values: Dict[str, Any] = Field(
        ..., description="The current state of the thread.", title="Values"
    )
    messages: Optional[List[Message]] = Field(
        None,
        description="The current messages of the thread. If messages are contained in Thread.values, implementations should remove them from values when returning messages. When this key isn't present it means the thread/agent doesn't support messages.",
        title="Messages",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="The checkpoint metadata.", title="Metadata"
    )


class ThreadPatch(BaseModel):
    checkpoint: Optional[ThreadCheckpoint] = Field(
        None,
        description="The identifier of the checkpoint to branch from. Ignored for metadata-only patches. If not provided, defaults to the latest checkpoint.",
        title="Checkpoint",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata to merge with existing thread metadata.",
        title="Metadata",
    )
    values: Optional[Dict[str, Any]] = Field(
        None, description="Values to merge with existing thread values.", title="Values"
    )
    messages: Optional[List[Message]] = Field(
        None,
        description="The current Messages of the thread. If messages are contained in Thread.values, implementations should remove them from values when returning messages. When this key isn't present it means the thread/agent doesn't support messages.",
        title="Messages",
    )


class ThreadsSearchPostResponse(RootModel[List[Thread]]):
    root: List[Thread] = Field(..., title="Response Search Threads Threads Search Post")


class ThreadsThreadIdHistoryGetResponse(RootModel[List[ThreadState]]):
    root: List[ThreadState]
