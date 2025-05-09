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

import json
import pytest
from agp_client import build_graph
from langchain_core.messages import HumanMessage
from langsmith import testing as t

@pytest.mark.langsmith(test_suite_name="TF Code Reviewer AGP Integration Test")
@pytest.mark.asyncio
async def test_agp_integration():
    CONTEXT_FILES = [
        {
            "path": "example.tf",
            "content": """
            resource "aws_s3_bucket" "example" {
              bucket = "my-public-bucket"
              acl    = "public-read"
            }
            """
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
            """
        }
    ]

    ANALYSIS_REPORTS = (
        "Security Warning: The security group allows unrestricted ingress (0.0.0.0/0)."
    )

    tf_input = {
        "context_files": CONTEXT_FILES,
        "changes": CHANGES,
        "static_analyzer_output": ANALYSIS_REPORTS
    }

    expected_output = "The security group allows unrestricted ingress"

    t.log_inputs({"query":tf_input})
    t.log_reference_outputs({"reference_outputs":expected_output})

    graph = await build_graph()
    inputs = {"messages": [HumanMessage(content=json.dumps(tf_input))]}
    result = await graph.ainvoke(inputs)


    response = result["messages"][-1].content
    t.log_outputs({"response":response})

    # Add validation scores
    t.log_feedback(key="contains_expected_text", score='unrestricted ingress' in response.lower())
    t.log_feedback(key="response_is_not_empty", score=bool(response))
    assert "messages" in result