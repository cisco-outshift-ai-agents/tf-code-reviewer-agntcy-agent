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

from utils.wrap_prompt import wrap_prompt

def test_wrap_prompt():
    """
    Test that `wrap_prompt()` preserves content order and normalizes indentation
    while still maintaining readability across prompt sections.
    """
    result = wrap_prompt("SECTION", "  some content", "", "CHANGES", "  change data")
    assert "SECTION" in result
    assert "some content" in result
    assert "CHANGES" in result
    assert "change data" in result
    # Ensure lines are correctly normalized
    lines = result.split("\n")
    assert lines[1].startswith("  ")  # 'some content' kept 2 spaces indent
    assert lines[4].startswith("  ")  # 'change data'