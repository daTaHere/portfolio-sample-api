from typing import Any, Dict, List

from app.exceptions.base import ServiceException
from app.exceptions.exception_handlers import raise_error
from app.utils.logger_helper import handle_log

from app.services.feeds.feed_fetchers import send_request
from app.services.cache_service import cache_get

JSONPLACEHOLDER_BASE_URL = "https://jsonplaceholder.typicode.com"


async def get_data(endpoint: str, start: int, limit: int) -> List[Dict[str, Any]]:
    """
    Fetch records from a specific endpoint and return as list of dicts.
    Handles URL construction, logging, and response validation.
    """
    cache_limit = limit * 2
    url = f"{JSONPLACEHOLDER_BASE_URL}/{endpoint}?_start={start}&_limit={cache_limit}"

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
    if len(data) > cache_limit:
        raise_error(
            f"Internal Server Error Received: {len(data)} items, Expected: up to {limit} items.",
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


def check_cache(key: str, start: int, limit: int):
    """
    Check if prefetched data is available in cache and
    if the requested range is within the cached range.
    """
    data = cache_get(key)
    cached: List[Dict[str, Any]] | None = None
    if data:
        _start, _end, _data = data.values()
        offset = start - _start
        if _start <= start and (start + limit - 1) <= _end:
            cached = _data[offset : offset + limit]
    return cached
