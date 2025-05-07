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
import tempfile
from app.main import load_environment_variables


def test_load_env_from_custom_file(monkeypatch):
    """
    Verify that environment variables are loaded from a custom .env file.
    """
    # Create a temp .env file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_env:
        temp_env.write("MY_VAR=123\n")
        temp_env.flush()

        monkeypatch.delenv("MY_VAR", raising=False)
        load_environment_variables(env_file=temp_env.name)

        assert os.getenv("MY_VAR") == "123"

def test_load_env_without_file(monkeypatch):
    """
    Simulate a case where no .env file exists — should not crash.
    """
    # Simulate no .env found
    monkeypatch.setattr("main.find_dotenv", lambda: "")
    result = load_environment_variables()
    assert result is None  # No crash