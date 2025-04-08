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
import os
import sys
from pathlib import Path
from pydantic import AnyUrl
from agntcy_acp.manifest import (
    AgentManifest,
    AgentDeployment,
    DeploymentOptions,
    LangGraphConfig,
    EnvVar,
    AgentMetadata,
    AgentACPSpec,
    AgentRef,
    Capabilities,
    SourceCodeDeployment,
    AgentDependency
)
# Get the absolute path of the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "./.."))
sys.path.insert(0, parent_dir)
from app.models.models import ReviewRequest, ReviewResponse, Config


manifest = AgentManifest(
    metadata=AgentMetadata(
        ref=AgentRef(name="org.agntcy.code-reviewer", version="0.0.1", url=None),
        description="Terraform Code Reviewer Agent automatically analyzes Terraform pull requests using static analysis and LLMs to generate high-quality, inline review suggestions. It supports both REST and AGP protocols for integration."),
    specs=AgentACPSpec(
        input=ReviewRequest.model_json_schema(),
        output=ReviewResponse.model_json_schema(),
        config=Config.model_json_schema(),
        capabilities=Capabilities(
            threads=None,
            callbacks=None,
            interrupts=None,
            streaming=None
        ),
        custom_streaming_update=None,
        thread_state=None,
        interrupts=None
    ),
    deployment=AgentDeployment(
        deployment_options=[
            DeploymentOptions(
                root = SourceCodeDeployment(
                    type="source_code",
                    name="src",
                    url="https://github.com/cisco-outshift-ai-agents/tf-code-reviewer-agntcy-agent",
                    framework_config=LangGraphConfig(
                        framework_type="langgraph",
                        graph="client.agp_client:build_graph"
                    )
                )
            )
        ],
        env_vars=[EnvVar(name="OPENAI_API_KEY", desc="Open AI API Key"),
                EnvVar(name="OPENAI_MODEL_NAME", desc="Open AI Model Name"),
                EnvVar(name="OPENAI_TEMPERATURE", desc="Open AI Temperature"),
                EnvVar(name="AZURE_OPENAI_API_KEY", desc="AZURE Open AI API Key"),
                EnvVar(name="AZURE_OPENAI_ENDPOINT", desc="AZURE Open AI Endpoint"),
                EnvVar(name="AZURE_OPENAI_DEPLOYMENT_NAME", desc="AZURE Open AI Deployment Name"),
                EnvVar(name="AZURE_OPENAI_API_VERSION", desc="AZURE Open AI API Version"),
                EnvVar(name="AZURE_OPENAI_TEMPERATURE", desc="AZURE Open AI Temperature"),
                EnvVar(name="AGP_GATEWAY_ENDPOINT", desc="AGP Gateway Endpoint"),]            
                ,
        dependencies=[
            AgentDependency(
                name="code-analyzer",
                ref=AgentRef(name="org.agntcy.code-analyzer", version="0.0.1", url="https://github.com/cisco-outshift-ai-agents/tf-code-analyzer-agntcy-agent"),
                deployment_option = None,
                env_var_values = None
            )
        ]
    )
)

with open(f"{Path(__file__).parent}/code_reviewer_manifest.json", "w") as f:
    f.write(manifest.model_dump_json(
        exclude_unset=True,
        exclude_none=True,
        indent=2
    ))
