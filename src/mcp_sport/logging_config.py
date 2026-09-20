"""Centralized logging configuration for mcp-sport.

Rules (see docs/Logging_Strategy.md):
- stdio transport: logs ALWAYS go to stderr (stdout is the JSON-RPC channel).
- Level set via MCP_SPORT_LOG_LEVEL env var (default: INFO).
- Root logger: "mcp_sport", with hierarchical children per subsystem.
"""

import logging
import os
import sys

ROOT_LOGGER_NAME = "mcp_sport"
_DEFAULT_LEVEL = "INFO"
_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def setup_logging() -> None:
    """Configure the project root logger with a stderr handler.

    Idempotent: repeated calls do not add duplicate handlers.
    """
    level_name = os.environ.get("MCP_SPORT_LOG_LEVEL", _DEFAULT_LEVEL).upper()
    level = logging.getLevelNamesMapping().get(level_name, logging.INFO)

    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.setLevel(level)

    if not root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(handler)

    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a child logger of 'mcp_sport' (e.g., get_logger('tools'))."""
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")
