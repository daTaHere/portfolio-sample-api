"""
Feed service layer.
Business logic for user operations.
"""

import httpx
import asyncio

from collections import defaultdict
from typing import Any, Dict, List, Type, TypeVar

from app.logging import logger
from app.models import Post, Comment, PostWithComments
from app.exceptions.base import (
    APIException,
    ServiceException,
)

from app.exceptions.exception_handlers import handle_error, raise_error

JSONPLACEHOLDER_BASE_URL = "https://jsonplaceholder.typicode.com"
POST_ENDPOINT = "posts"
COMMENT_ENDPOINT = "comments"
MAX_RETRIES = 3
HTTP_TIMEOUT_SECONDS = 5.0
RETRY_BACKOFF_BASE = 0.2  # seconds

T = TypeVar("T", bound=Post | Comment)


async def send_request(endpoint: str) -> List[Dict[str, Any]]:
    """
    Send HTTP request to 3rd party API and return JSON list.
    Handles network, HTTP status, and JSON decoding errors.
    """
    url = endpoint
    data = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "Attempting request",
                extra={
                    "event_key": "ATTEMPTS",
                    "endpoint": url,
                    "method": "GET",
                    "service_method": "send_request",
                    "request_attempt": attempt,
                },
            )
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
                res = await client.get(url)
                res.raise_for_status()

                try:
                    data = res.json()
                    break  # exit retry loop on success
                except httpx.DecodingError as e:
                    handle_error(
                        e,
                        "External API Error: Invalid JSON response.",
                        "Request returned invalid JSON.",
                        exc_type=APIException,
                        url=url,
                        service_method="send_request",
                    )
        except (httpx.RequestError, httpx.ConnectTimeout) as e:
            wait_time = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))

            if attempt == MAX_RETRIES:
                handle_error(
                    e,
                    "External API Error: Unreachable",
                    "Request failed. Exhausted all retries.",
                    exc_type=APIException,
                    url=url,
                    service_method="send_request",
                )
            logger.warning(
                f"Request attempt failed, retrying in {wait_time:.2f}s",
                extra={
                    "event_key": "RETRIES",
                    "endpoint": url,
                    "request_attempt": attempt,
                    "service_method": "send_request",
                    "error": str(e),
                },
            )
            await asyncio.sleep(wait_time)
        except httpx.HTTPStatusError as e:
            handle_error(
                e,
                f"External API Error: Bad status code: {e.response.status_code}",
                "Request returned bad status code.",
                exc_type=APIException,
                url=url,
                service_method="send_request",
            )
        except (TypeError, ValueError) as e:
            logger.debug(
                f"Response JSON decoding error: {str(e)}",
                extra={
                    "endpoint": url,
                    "method": "GET",
                    "service_method": "send_request",
                },
            )
    if not isinstance(data, list):
        raise_error(
            f"Internal server error: expected type List got {type(data).__name__}",
            f"Unexpected response type expected List got {type(data).__name__}",
            exc_type=ServiceException,
            url=url,
            method="GET",
            service_method="send_request",
            event_key="ERROR",
            model=endpoint.upper(),
            received_type=type(data).__name__,
        )
    logger.info(
        "Successful response received",
        extra={
            "event_key": "SUCCESS",
            "endpoint": url,
            "method": "GET",
            "service_method": "send_request",
            "items": len(data),
        },
    )

    return data


async def get_data(endpoint: str, start: int, limit: int) -> List[Dict[str, Any]]:
    """
    Fetch records from a specific endpoint and return as list of dicts.
    Only validates type; content validation deferred to marshmallow.
    """
    url = f"{JSONPLACEHOLDER_BASE_URL}/{endpoint}?_start={start}&_limit={limit}"
    logger.info(
        f"Constructing endpoint URL",
        extra={
            "event_key": "ENDPOINT_URL",
            "endpoint": url,
            "service_method": "get_data",
        },
    )

    logger.info(
        f"Attempt request for {endpoint.upper()}",
        extra={
            "event_key": "REQUEST_ATTEMPT",
            "endpoint": url,
            "service_method": "get_data",
        },
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
    if len(data) > limit:
        raise_error(
            f"Internal Server Error Received: {len(data)} items, Expected: up to {limit} items.",
            f"Response item count mismatch",
            exc_type=ServiceException,
            url=url,
            method="GET",
            service_method="get_data",
        )
    logger.info(
        f"Successful response received",
        extra={
            "event_key": "SUCCESS",
            "service_method": "get_data",
            "items": len(data),
            "model": endpoint.upper(),
        },
    )
    return data


def create_model_list(input_data: List[Dict[str, Any]], model: Type[T]) -> List[T]:
    """
    Instantiate Post or Comment objects from raw data.
    """
    try:
        items = [model(d) for d in input_data]
        logger.info(
            "Created List of model instances",
            extra={
                "event_key": "CREATE_MODEL_LIST",
                "model": model.__name__,
                "service_method": "create_model_list",
                "count": len(items),
            },
        )
    except (TypeError, ValueError) as e:
        handle_error(
            e,
            f"Internal Server Error: Failed to create {model.__name__} instances.",
            f"Error creating {model.__name__} instances",
            exc_type=ServiceException,
            service_method="create_model_list",
            model=model.__name__,
            method="create_model_list",
        )
    logger.info(
        "Success List of model instances created",
        extra={
            "event_key": "SUCCESS",
            "service_method": "create_model_list",
            "model": model.__name__,
            "count": len(items),
        },
    )
    return items


async def get_10_feeds(start: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Orchestrates fetching posts and comments, builds feed objects.
    """

    posts_coro = get_data(POST_ENDPOINT, start, limit)
    comments_coro = get_data(COMMENT_ENDPOINT, start, limit)
    post_data, comment_data = await asyncio.gather(posts_coro, comments_coro)

    posts = create_model_list(post_data, Post)
    comments = create_model_list(comment_data, Comment)

    logger.info(
        f"Post_Cnt: {len(posts)}, Comment_Cnt: {len(comments)}",
        extra={
            "event_key": "FETCH_COUNTS",
            "service_method": "get_10_feeds",
            "model": f"{Post.__name__}, {Comment.__name__}",
            "post_count": len(posts),
            "comment_count": len(comments),
        },
    )

    # Organize comments by post_id
    comments_by_post: Dict[int, List[Comment]] = defaultdict(list)
    for c in comments:
        comments_by_post[c._postId].append(c)
    logger.info(
        "Filtered comments by post",
        extra={
            "event_key": "FILTERED_COMMENTS",
            "service_method": "get_10_feeds",
            "post_count": len(comments_by_post),
        },
    )
    try:
        feeds = [
            PostWithComments(post, comments_by_post[post._id]).to_dict()
            for post in posts
        ]
    except (TypeError, ValueError) as e:
        handle_error(
            e,
            "Internal Server Error: Unexpected error failed to fetch feeds.",
            "Error creating PostWithComments instances",
            exc_type=ServiceException,
            service_method="get_10_feeds",
            model="PostWithComments",
            event_key="ERROR",
        )
    logger.info(
        f"Successfully created {len(feeds)} feed items",
        extra={
            "event_key": "SUCCESS",
            "service_method": "get_10_feeds",
            "model": "PostWithComments",
            "feed_count": len(feeds),
        },
    )

    return feeds
