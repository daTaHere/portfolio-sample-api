"""This module defines helper functions for handling exceptions consistently."""

from app.logging import logger
from typing import Any, Optional, Type


def handle_service_error(
    exc: Exception,
    exc_message: str,
    log_message: str,
    *,
    exc_type: Type[Exception],
    url: Optional[str] = "",
    method: Optional[str] = "",
    service_method: str = "",
    event_key: str = "ERROR",
    **extra: Any,
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


def handle_route_error(
    exc: Exception,
    log_message: str,
    *,
    route: str,
    service_method: str,
    **extra: Any,
) -> None:
    """Helper function to log route-level exceptions consistently."""

    logger.error(
        log_message,
        extra={
            "event_key": "ERROR",
            "route": route,
            "service_method": service_method,
            "endpoint": getattr(exc, "endpoint", None),
            "method": getattr(exc, "method", None),
            **extra,
        },
    )


def raise_error(
    exc_message: str,
    log_message: str,
    *,
    exc_type: Type[Exception],
    url: Optional[str] = "",
    method: Optional[str] = "",
    service_method: str = "",
    event_key: str = "ERROR",
    **extra: Any,
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
