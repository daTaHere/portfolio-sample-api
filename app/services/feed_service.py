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

JSONPLACEHOLDER_BASE_URL = "https://jsonplaceholder.typicode.com"
HTTP_TIMEOUT_SECONDS = 5.0
RETRY_BACKOFF_BASE = 0.2  # seconds

T = TypeVar("T", bound=Post | Comment)

"""
    Sends request to JsonPlaceholder API.
    Args:
        endpoint -> url of api for request
    Return:
        Json object response
    example:
        send_request(endpoint = 'www.myendpoint.com/{endpoint})
    
"""


async def send_request(endpoint: str) -> List[Dict[str, Any]]:
    url = endpoint
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            res = await client.get(url)
            res.raise_for_status()
            return res.json()
    except httpx.RequestError as e:
        raise APIException(
            "Failed request JsonPlaceHolder ", endpoint=url, method="GET"
        ) from e
    except httpx.HTTPStatusError as e:
        raise APIException(
            f"Bad status code from JsonPlaceholder: {e.response.status_code}",
            endpoint=url,
            method="GET",
        ) from e
    except httpx.DecodingError as e:
        raise APIException(
            "Invalid JSON response from JsonPlaceholder", endpoint=url, method="GET"
        ) from e
    except Exception as e:
        raise APIException("Failed to send request", endpoint=url, method="GET") from e


"""
    Fetch 10 post records 
    Args:
        start -> beginning query index
        limit -> number of records
    return:
        dict object of 10 Post items
    example:
        url -> api endpoint url
        send_request(url)
"""


async def get_posts(start: int, limit: int) -> List[Dict[str, Any]]:
    url = f"{JSONPLACEHOLDER_BASE_URL}/posts?_start={start}&_limit={limit}"
    try:
        res = await send_request(url)  # All HTTP errors already handled
        if not isinstance(res, list):
            raise ServiceException(
                "Unexpected Post response format",
                service_method="get_posts",
                model="Post",
            )
        if len(res) != limit:
            raise ServiceException(
                f"Expected {limit} Post records, received {len(res)}",
                service_method="get_posts",
                model="Post",
            )
        return res  # Only JSON decode problems left
    except Exception as e:
        raise ServiceException(
            "Failed to parse Post response", service_method="get_posts", model="Post"
        ) from e


"""
    Fetch 10 comment records 
    Args:
        start -> beginning query index
        limit -> number of records
    return:
        List of dict objects of 10 Comment items
    example:
        url -> api endpoint url
        send_request(url)
"""


async def get_comments(start: int, limit: int) -> List[Dict[str, Any]]:
    url = f"{JSONPLACEHOLDER_BASE_URL}/comments?_start={start}&_limit={limit}"
    try:
        res = await send_request(url)  # All HTTP errors already handled
        if not isinstance(res, list):
            raise ServiceException(
                "Unexpected Comment response format",
                service_method="get_comments",
                model="Comment",
            )
        if len(res) != limit:
            raise ServiceException(
                f"Expected {limit} Comment records, received {len(res)}",
                service_method="get_comments",
                model="Comment",
            )
        return res  # Only JSON decode problems left
    except Exception as e:
        raise ServiceException(
            "Failed to parse Comment response",
            service_method="get_comments",
            model="Comment",
        ) from e


"""
    Create a List of Posts/Comments for feed
    Raise expection on corrupt, malformed, miss data.

    Args:
        input_data -> Coroute object
        model -> class of Type Post or Comment
    Return:
        List of Models
    Example:
        def create_feed_input(Post_data, Post)
"""


def create_feed_input(input_data: List[Dict[str, any]], model: Type[T]) -> List[T]:
    try:
        return [model(data) for data in input_data]
    except KeyError as e:
        raise ServiceException(
            "Failed to create feed inputs",
            service_method="create_feed_input",
            model=model.__name__,
        ) from e


"""
    Service fetches Post and Comment from 3rd party API.
    ETL respones and hydrates 10 Feed objects.

    Args:
        start -> Query start index : default 0
        limit -> Number of records: default 10
    Return:
        List of 10 feed objects
    Example:
        get_10_feeds(start=0,limit=10)

"""


async def get_10_feeds(start: int = 0, limit: int = 10) -> List[Dict[str, Any]]:

    posts_coro = get_posts(start, limit)
    comments_coro = get_comments(start, limit)
    post_data, comment_data = await asyncio.gather(posts_coro, comments_coro)

    posts = create_feed_input(post_data, Post)
    comments = create_feed_input(comment_data, Comment)

    logger.info(f"Post_Cnt: {len(posts)}, Comment_Cnt: {len(comments)}")

    sorted_comments: Dict[int, List[Comment]] = defaultdict(list)
    for c in comments:
        sorted_comments[c._postId].append(c)

    try:
        feeds = [
            PostWithComments(post, sorted_comments[post._id]).to_dict()
            for post in posts
        ]
        return feeds
    except KeyError as e:
        raise ServiceException(
            "Failed to return feed Key Error", model="PostWithComments"
        ) from e

    except Exception as e:
        logger.exception("Failed to fetch feeds")  # includes stack trace
        raise ServiceException("Failed to fetch feeds", model="PostWithComments") from e
