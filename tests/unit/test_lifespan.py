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
import pytest
from fastapi import FastAPI
from main import lifespan


@pytest.mark.asyncio
async def test_lifespan_initializes_chain(monkeypatch):
    """
    Ensures that the FastAPI `lifespan()` function sets the chain on app startup.
    """
    app = FastAPI()

    monkeypatch.setattr("main.initialize_chain", lambda: "mock_chain")

    async with lifespan(app):
        assert app.state.code_reviewer_chain == "mock_chain"