from typing import Any, Dict, List, Tuple

from app.services.feeds.feed_fetchers import send_request

from app.exceptions.base import ServiceException
from app.exceptions.service import ServiceInternalException
from app.exceptions.exception_handlers import handle_service_errorV2, raise_error

from app.utils.logger_helper import handle_log


JSONPLACEHOLDER_BASE_URL = "https://jsonplaceholder.typicode.com"


def normalize_pagination(params: Tuple[int, int]) -> Tuple[int, int]:
    """Validates and normalizes pagination parameters."""
    start, limit = params
    if start < 0 or limit <= 0 or limit > 100:
        handle_log(
            "Invalid search parameters",
            log_level="error",
            event_key="INVALID__ERROR",
            service_method="normalize_pagination",
        )
        return None
    return (start, limit)


async def get_data(endpoint: str, limit: int) -> List[Dict[str, Any]]:

    prefetch_limit = limit * 2
    data = await send_request(endpoint)

    if not isinstance(data, list) or (len(data) > 0 and not isinstance(data[0], dict)):
        raise_error(
            f"Internal Server Error: expected List of objects got {type(data).__name__}",
            f"Unexpected response type expected List of objects got {type(data).__name__}",
            exc_type=ServiceException,
            url=endpoint,
            method="GET",
            service_method="get_data",
            model=endpoint.upper(),
            received_type=type(data).__name__,
        )
    if len(data) > prefetch_limit:  # guard against unexpected large queries
        raise_error(
            f"Internal Server Error Received: {len(data)} items, Expected: up to {prefetch_limit} items.",
            f"Response item count mismatch",
            exc_type=ServiceException,
            url=endpoint,
            method="GET",
            service_method="get_data",
            model=endpoint.upper(),
        )
    handle_log(
        "Successful response received",
        event_key="SUCCESS",
        log_level="info",
        service_method="get_data",
        endpoint=endpoint,
        items=len(data),
        model=endpoint.upper(),
    )

    return data


def check_cache(
    cache_data: Dict[str, Any], start: int, limit: int
) -> List[Dict[str, Any]] | None:
    """
    Returns a subset of cached data if the requested range is valid.
    Raises ValueError if start/limit are outside cached bounds.
    """

    _start, _data = cache_data["start"], cache_data["data"]
    offset = start - _start
    if start < _start or offset + limit > len(_data):
        handle_log(
            "Requested range out of bounds cache data incomplete.",
            method="GET",
            event_key="CACHE_RANGE_ERROR",
            log_level="warning",
            service_method="check_cache",
            model="PostWithComments",
        )
        return None

    return _data[offset : offset + limit]
