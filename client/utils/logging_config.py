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

"""
This module provides logging configuration for the remote graphs client.
It sets up structured JSON logging with rotation and supports logging to both console and file.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter


def get_log_dir() -> Path:
    """Returns the log directory path and ensures it exists."""
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_level() -> str:
    """Retrieves the log level from environment variables (defaults to INFO)."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def configure_logging(log_filename: str = "ap_rest_client.log") -> logging.Logger:
    """
    Configures structured JSON logging with rotation.

    Logs to both console and a rotating file handler.
    The log level is determined by the LOG_LEVEL environment variable.
    
    Parameters:
        log_filename (str): Name of the log file.
    """
    log_dir = get_log_dir()
    log_file = log_dir / log_filename
    log_level: str = get_log_level()

    logger = logging.getLogger()
    logger.setLevel(log_level)

    formatter = JsonFormatter(
        "{asctime} {levelname} {pathname} {module} {funcName} {message} {exc_info}",
        style="{",
    )

    # ✅ Log to Console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # ✅ Log to File with Rotation
    file_handler = RotatingFileHandler(
        log_file, mode="a", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(
        "Logging initialized with rotation.", extra={"log_destination": str(log_file)}
    )

    return logger
