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
from fastapi.routing import APIRoute
from app.main import custom_generate_unique_id


def test_custom_generate_unique_id_with_tags():
    """
    Verify that route IDs are generated using tag prefix.
    """
    route = APIRoute(
        path="/example",
        endpoint=lambda: None,
        methods=["GET"],
        name="example",
        tags=["test"]
    )
    result = custom_generate_unique_id(route)
    assert result == "test-example"

def test_custom_generate_unique_id_without_tags():
    """
    Verify that route ID falls back to route name when tags are absent.
    """
    route = APIRoute(
        path="/no-tags",
        endpoint=lambda: None,
        methods=["GET"],
        name="no_tags"
    )
    route.tags = []
    result = custom_generate_unique_id(route)
    assert result == "no_tags"