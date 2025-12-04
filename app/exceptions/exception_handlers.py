from app.logging import logger
from typing import TypeVar, Optional
from app.models import Post, Comment

T = TypeVar("T", bound=Post | Comment)


def handle_error(
    exc: Exception,
    exc_message: str,
    log_message: str,
    *,
    exc_type: type[Exception],
    url: Optional[str] = None,
    method: str = "GET",
    service_method: str = "",
    event_key: str = "ERROR",
    **extra: Optional[str],
) -> None:
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
