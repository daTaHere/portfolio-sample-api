from typing import Any, Dict, List, Tuple

from app.services.feeds.feed_fetchers import send_request

from app.exceptions.base import ServiceException
from app.exceptions.service import ServiceInternalException
from app.exceptions.exception_handlers import handle_service_errorV2, raise_error

from app.utils.logger_helper import handle_log


JSONPLACEHOLDER_BASE_URL = "https://jsonplaceholder.typicode.com"


def normalize_pagination(
    start: int,
    limit: int,
) -> Tuple[int, int]:
    """Validates and normalizes pagination parameters."""
    if start < 0 or limit <= 0 or limit > 100:
        handle_log(
            "Invalid search parameters",
            method="GET",
            event_key="VALUE_ERROR",
            log_level="error",
            service_method="normalize_pagination",
        )
        return None
    return (start, limit)


async def get_data(endpoint: str, start: int, limit: int) -> List[Dict[str, Any]]:
    """
    Construct the endpoint URL for prefetching data from the JSONPlaceholder API,
    send the request, validate the response, and return the list of items.
    """
    prefetch_limit = limit * 2
    url = (
        f"{JSONPLACEHOLDER_BASE_URL}/{endpoint}?_start={start}&_limit={prefetch_limit}"
    )

    handle_log(
        "Constructing endpoint URL",
        log_level="info",
        event_key="ENDPOINT_URL",
        service_method="get_data",
        endpoint=url,
    )
    handle_log(
        f"Attempt request for {endpoint.upper()}",
        method="GET",
        event_key="REQUEST_ATTEMPT",
        log_level="info",
        service_method="get_data",
        endpoint=url,
    )

    data = await send_request(url)

    if not isinstance(data, list) or (len(data) > 0 and not isinstance(data[0], dict)):
        raise_error(
            f"Internal Server Error: expected List of objects got {type(data).__name__}",
            f"Unexpected response type expected List of objects got {type(data).__name__}",
            exc_type=ServiceException,
            url=url,
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
            url=url,
            method="GET",
            service_method="get_data",
            model=endpoint.upper(),
        )
    handle_log(
        "Successful response received",
        event_key="SUCCESS",
        log_level="info",
        service_method="get_data",
        endpoint=url,
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
    _start, _end, _data = cache_data.values()
    if start < _start or (start + limit - 1) > _end:
        handle_log(
            "Requested range out of bounds cache data incomplete.",
            method="GET",
            event_key="CACHE_RANGE_ERROR",
            log_level="warning",
            service_method="check_cache",
            model="PostWithComments",
        )
        return None

    offset = start - _start

    return _data[offset : offset + limit]
