from app.logging import logger
from typing import Any, Optional


def handle_error(
    exc: Exception,
    exc_message: str,
    log_message: str,
    *,
    exc_type: type[Exception],
    url: Optional[str] = "",
    method: Optional[str] = "",
    service_method: str = "",
    event_key: str = "ERROR",
    **extra: Optional[Any],
) -> None:
    """Helper function to log and raise low-level exceptions consistently."""
    logger.error(
        log_message,
        extra={
            "event_key": event_key,
            "endpoint": url,
            "method": method,
            "service_method": service_method,
            "error": str(exc),
            **extra,
        },
    )
    raise exc_type(exc_message, endpoint=url, method=method) from exc


def raise_error(
    exc_message: str,
    log_message: str,
    *,
    exc_type: type[Exception],
    url: Optional[str] = "",
    method: Optional[str] = "",
    service_method: str = "",
    event_key: str = "ERROR",
    **extra: Optional[Any],
) -> None:
    """Helper function to log and raise general exceptions consistently."""
    logger.error(
        log_message,
        extra={
            "event_key": event_key,
            "endpoint": url,
            "method": method,
            "service_method": service_method,
            **extra,
        },
    )
    raise exc_type(exc_message, endpoint=url, method=method)
