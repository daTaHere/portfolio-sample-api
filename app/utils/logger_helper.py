import logging
import structlog
from app.logging import logger
from typing import Any

allowed_log_levels = {"debug", "info", "warning", "error", "critical"}


def debug_logger(name: str, level=logging.DEBUG):
    """
    Scoped logger that uses structlog’s Processor framework but outputs to a Python logger

    Args:
        name (str): The name of the logger.
        level (int): The logging level (default: logging.DEBUG).
    """
    py_logger = logging.getLogger(name)
    py_logger.setLevel(level)

    # Only attach a StreamHandler if it doesn’t already have one
    if not py_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        py_logger.addHandler(console_handler)

    # Return the structlog logger bound to the same Python logger
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
    """Logs a message with standardized structure and dynamic log level."""
    if log_level not in allowed_log_levels:
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
