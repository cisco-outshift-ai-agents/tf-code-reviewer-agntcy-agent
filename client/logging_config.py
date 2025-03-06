import json
import logging
import logging.config
import os
from pathlib import Path
import traceback
from typing import Dict


class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs logs in structured JSON format.

    - Includes timestamp, log level, message, module, function, and line number.
    - Captures exceptions with stack trace when applicable.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),  # ISO 8601 format
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "logger": record.name,
            "pid": record.process,
        }

        if record.exc_info:
            log_data["error"] = {
                "type": str(record.exc_info[0]),
                "message": str(record.exc_info[1]),
                "stack_trace": traceback.format_exc(),
            }

        return json.dumps(log_data)


def get_log_dir() -> Path:
    """Returns the log directory path and ensures it exists."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_file() -> Path:
    """Returns the log file path and ensures it is removed on every startup."""
    log_file = get_log_dir() / "graph_client.log"

    # Remove old log file on startup to ensure fresh logs
    try:
        if log_file.exists():
            log_file.unlink()
    except PermissionError as e:
        logging.error(f"{e}: {log_file}")
        raise

    return log_file


def get_log_level() -> str:
    """Retrieves the log level from environment variables (defaults to INFO)."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_logging_config(log_file: Path, log_level: str) -> Dict:
    """Generates logging configuration dictionary with JSON formatting."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,  # Use custom JSON formatter
            },
        },
        "handlers": {
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "json",
            },
            "file": {
                "level": log_level,
                "class": "logging.FileHandler",
                "filename": str(log_file),
                "formatter": "json",
            },
        },
        "loggers": {
            "graph_client": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
        },
        "root": {"handlers": ["console", "file"], "level": log_level},
    }


def configure_logging() -> logging.Logger:
    """Configures structured JSON logging for the client."""
    log_file = get_log_file()
    log_level = get_log_level()
    logging_config = get_logging_config(log_file, log_level)
    logging.config.dictConfig(logging_config)

    logger = logging.getLogger("graph_client")
    logger.info("Client logging is initialized.")
    return logger
