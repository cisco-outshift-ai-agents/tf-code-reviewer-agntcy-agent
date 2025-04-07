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
from main import initialize_chain

def test_initialize_chain_openai(monkeypatch):
    """
    Test OpenAI fallback path when Azure env vars are not set.
    Verifies that initialize_chain() returns a valid chain.
    """
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    os.environ["OPENAI_API_KEY"] = "fake-key"
    chain = initialize_chain()
    assert chain is not None


def test_initialize_chain_azure(monkeypatch):
    """
    Test Azure path when Azure-related environment variables are present.
    """
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://fake-endpoint")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "test-deploy")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    monkeypatch.setenv("AZURE_OPENAI_TEMPERATURE", "0.7")

    chain = initialize_chain()
    assert chain is not None