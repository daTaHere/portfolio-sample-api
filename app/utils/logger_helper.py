from app.logging import logger
from typing import Any, Optional, Type


def handle_log(
    log_message: str,
    method: str = "GET",
    *,
    log_level: str,
    event_key: str,
    service_method: str,
    **extra: Optional[Any]
) -> None:

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
