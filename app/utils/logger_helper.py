from app.logging import logger
from typing import Any

allowed_log_levels = {"debug", "info", "warning", "error", "critical"}


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
