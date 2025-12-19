"""This module provides helper functions for logging with structured logs and dynamic log levels."""

import logging
import structlog
from app.logging import logger
from typing import Any

allowed_log_levels = {
    "debug",
    "info",
    "warning",
    "error",
    "critical",
}  # Define allowed log levels


def debug_logger(name: str, level=logging.DEBUG):
    """
    Helper function to create and return an isolated logger instance with the specified name and level.

    Args:
        name (str): The name of the logger.
        level (int): The logging level (default: logging.DEBUG).
    """
    # Override default logger configuration to create isolated logger and emit level
    py_logger = logging.getLogger(name)
    py_logger.setLevel(level)

    # Ensure logger has handlers attached for console output
    if not py_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        py_logger.addHandler(console_handler)

    return structlog.get_logger(name)


def handle_log(
    log_message: str,
    method: str = "GET",
    *,
    log_level: str,
    event_key: str,
    service_method: str,
    **extra: Any,
) -> None:
    """Helper function returns a structured log with dynamic log level."""

    if log_level not in allowed_log_levels:  # Ensure valid log level
        raise ValueError(
            f"Invalid log_level '{log_level}'. Must be one of {allowed_log_levels}.",
            service_method={service_method},
        )

    log_method = getattr(logger, log_level)

    log_method(
        log_message,
        extra={
            "event_key": event_key,
            "method": method,
            "service_method": service_method,
            **extra,
        },
    )
