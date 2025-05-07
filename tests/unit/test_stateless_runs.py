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
from fastapi.testclient import TestClient
from app.main import create_fastapi_app


def test_run_stateless_runs_valid(monkeypatch):
    """
    Happy-path test for the `/api/v1/runs` endpoint using a dummy chain.
    Verifies that valid payload results in 200 response and proper format.
    """
    app = create_fastapi_app()

    # Patch the app state with a fake chain that returns dummy results
    class DummyChain:
        def invoke(self, _):
            from models.models import ReviewComments, ReviewComment
            return ReviewComments(
                issues=[
                    ReviewComment(
                        filename="x.tf",
                        line_number=1,
                        comment="test comment",
                        status="added"
                    )
                ]
            )

    app.state.code_reviewer_chain = DummyChain()
    client = TestClient(app)

    payload = {
        "agent_id": "test-agent",
        "model": "gpt-4",
        "route": "/api/v1/runs",
        "metadata": {"id": "req-1"},
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps({
                        "context_files": [{"path": "main.tf", "content": "resource"}],
                        "changes": [{"file": "main.tf", "content": "change"}],
                        "static_analyzer_output": "some warning"
                    }),
                }
            ]
        }
    }

    response = client.post("/api/v1/runs", json=payload)
    print("Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 200
    assert response.json()["agent_id"] == "test-agent"


def test_run_missing_fields(monkeypatch):
    """
    Test to verify 422 or 500 is returned when required fields are missing.
    Helps verify request validation and fallback error handling.
    """
    app = create_fastapi_app()

    # Patch with dummy reviewer chain to prevent 500 during startup
    class DummyChain:
        def invoke(self, _):
            return None

    app.state.code_reviewer_chain = DummyChain()
    client = TestClient(app)

    # Send empty payload — should fail with 422 (validation) or 500 (internal failure)
    response = client.post("/api/v1/runs", json={})

    assert response.status_code in (422, 500)
