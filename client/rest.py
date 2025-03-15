# SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# Description: This file contains a sample graph client that makes a stateless request to the Remote Graph Server.
# Usage: python3 client/rest.py

"""
This module contains the main function to invoke the graph with given context files, changes, 
and static analyzer output.

It logs the process and handles any exceptions that occur during the invocation.
"""

import json
from typing import List, Dict, Any

from langchain_core.messages import HumanMessage
from logging_config import configure_logging

from ap_rest_client.ap_protocol import invoke_graph  # type: ignore

logger = configure_logging()


def main() -> None:
    """
    Main function to invoke the graph with given context files, changes, and static analyzer output.
    Logs the process and handles any exceptions that occur.
    """
    context_files = [
        """
        resource "aws_s3_bucket" "example" {
            bucket = "my-public-bucket"
            acl    = "public-read"
        }
        """
    ]

    changes = """
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

    analysis_reports = (
        "Security Warning: The security group allows unrestricted ingress (0.0.0.0/0)."
    )

    tf_input: Dict[str, Any] = {
        "context_files": [{"path": "example.py", "content": context_files[0]}],
        "changes": [{"file": "example.py", "diff": changes}],
        "static_analyzer_output": analysis_reports,
    }

    messages: List[HumanMessage] = [HumanMessage(content=json.dumps(tf_input))]

    logger.info({"event": "invoking_graph", "inputs": tf_input})

    try:
        result = invoke_graph(messages=messages)
        output = result[-1].get("content")
        logger.info({"event": "final_result", "result": output})
    except Exception as e:
        logger.error({"event": "error_invoking_graph", "error": str(e)})


if __name__ == "__main__":
    main()
