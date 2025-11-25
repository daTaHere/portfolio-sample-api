"""
Feed service layer.
Business logic for user operations.
"""

from collections import defaultdict
from typing import Any, Dict, List, Type, TypeVar, Optional
import asyncio
import time

import httpx

from app import logger
from app.models import Post, Comment, PostWithComments
from app.exceptions.base_exceptions import (
    APIException,
    ServiceException,
)

JSONPLACEHOLDER_BASE_URL = "https://jsonplaceholder.typicode.com/"
POST_ENDPOINT = "posts"
COMMENT_ENDPOINT = "comments"
HTTP_TIMEOUT_SECONDS = 5.0
RETRY_BACKOFF_BASE = 0.2  # seconds

T = TypeVar("T", bound=Post | Comment)


async def send_request(endpoint: str) -> List[Dict[str, Any]]:
    """
    Send HTTP request to 3rd party API and return JSON list.
    Handles network, HTTP status, and JSON decoding errors.
    """
    url = endpoint
    logger.debug(f"Request Sent", extra={"endpoint": url, "method": "send_request"})
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            res = await client.get(url)
            res.raise_for_status()
            data = res.json()
            logger.debug(
                "Response received", extra={"endpoint": url, "records": len(data)}
            )
            if not isinstance(data, list):
                raise ServiceException(
                    f"Unexpected response type, expected list",
                    service_method="send_request",
                    model=endpoint.upper(),
                )
            return data
    except httpx.RequestError as e:
        logger.error(
            "Request failed",
            extra={"endpoint": url, "error": str(e)},
        )
        raise APIException(
            "Failed JsonPlaceHolder request ", endpoint=url, method="GET"
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Bad status code",
            extra={"path": url, "status_code": e.response.status_code, "error": str(e)},
        )
        raise APIException(
            f"Bad status code: {e.response.status_code}",
            endpoint=url,
            method="GET",
        ) from e
    except httpx.DecodingError as e:
        logger.error(f"Invalid JSON response", extra={"path": url, "error": str(e)})
        raise APIException(
            "Invalid JSON response from JsonPlaceholder", endpoint=url, method="GET"
        ) from e
    except Exception as e:
        logger.error(f"Unexpected request error", extra={"path": url, "error": str(e)})
        raise APIException("Failed to send request", endpoint=url, method="GET") from e


async def get_data(endpoint: str, start: int, limit: int) -> List[Dict[str, Any]]:
    """
    Fetch records from a specific endpoint and return as list of dicts.
    Only validates type; content validation deferred to marshmallow.
    """
    url = f"{JSONPLACEHOLDER_BASE_URL}/{endpoint}?_start={start}&_limit={limit}"
    logger.info(f" Fetch data ", extra={"endpoint": url, "method": "get_data"})
    try:
        data = await send_request(url)  # All HTTP errors already handled
        logger.info(
            f" Data fetch successful ",
            extra={"service_method": "get_data", "model": endpoint.upper()},
        )
        if len(data) != limit:
            logger.error(
                f"Missing or incomplete return",
                extra={
                    "method": "get_data",
                    "model": endpoint.upper(),
                    "count": len(data),
                },
            )
            raise ServiceException(
                f"Expected {limit} items, received {len(data)}",
                service_method="get_data",
                model=endpoint.upper(),
            )
        return data
    except Exception as e:
        logger.error("Unexpected error in get_data", extra={"error": str(e)})
        raise ServiceException(
            f"Failed to fetch {url} data",
            service_method="get_data",
            model=endpoint.upper(),
        ) from e


def create_feed_input(input_data: List[Dict[str, any]], model: Type[T]) -> List[T]:
    """
    Instantiate Post or Comment objects from raw data.
    Logging included for success/failure.
    """
    try:
        items = [model(d) for d in input_data]
        logger.info(
            "Model instances created",
            extra={"model": model.__name__, "count": len(items)},
        )
        return items
    except Exception as e:
        logger.exception(
            "Failed creating model instances", extra={"model": model.__name__}
        )
        raise ServiceException(
            f"Failed to create {model.__name__} instances",
            service_method="create_feed_input",
            model=model.__name__,
        ) from e


async def get_10_feeds(start: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Orchestrates fetching posts and comments, builds feed objects.
    """

    posts_coro = get_data(POST_ENDPOINT, start, limit)
    comments_coro = get_data(COMMENT_ENDPOINT, start, limit)
    post_data, comment_data = await asyncio.gather(posts_coro, comments_coro)

    posts = create_feed_input(post_data, Post)
    comments = create_feed_input(comment_data, Comment)

    logger.info(f"Post_Cnt: {len(posts)}, Comment_Cnt: {len(comments)}")

    # Organize comments by post_id
    comments_by_post: Dict[int, List[Comment]] = defaultdict(list)
    for c in comments:
        comments_by_post[c._postId].append(c)

    try:
        feeds = [
            PostWithComments(post, comments_by_post[post._id]).to_dict()
            for post in posts
        ]
        logger.info(f"Successfully created {len(feeds)} feed items")
        return feeds

    except Exception as e:
        logger.exception(
            "Unexpected error",
            extra={"service_method": "get_10_feeds", "error": str(e)},
        )  # includes stack trace
        raise ServiceException(
            "Unexpected error fail to fetch feeds", model="PostWithComments"
        ) from e
