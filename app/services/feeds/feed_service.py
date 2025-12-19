"""
Feed service layer.
Business logic for feed operations.
"""

import asyncio

from collections import defaultdict
from typing import Any, Dict, List
from marshmallow import ValidationError

from app.models import Post, Comment, PostWithComments
from app.schemas.feed_schemas import PostWithCommentsSchema
from app.dto.feeds.feed_cache_dto import FeedCache
from app.dto.feeds.feed_cache_schema import FeedCacheSchema

from app.services.feeds.feed_builders import create_model_list
from app.services.feeds.feed_validators import get_data, check_cache
from app.services.cache_service import cache_get, cache_set

from app.exceptions.base import ServiceException
from app.exceptions.exception_handlers import handle_service_error

from app.logging import logger
from app.utils.logger_helper import handle_log, debug_logger


POST_ENDPOINT = "posts"
COMMENT_ENDPOINT = "comments"

feed_logger = debug_logger("get_10_feeds")
feeds_schema = PostWithCommentsSchema(many=True)


async def get_10_feeds(start: int = 0, limit: int = 10) -> List[PostWithComments]:
    """
    Main feed service function to get posts with comments.
    Orchestrates data fetching, model creation, caching, and error handling.
    """

    if start < 0 or limit <= 0 or limit > 100:
        handle_log(
            f"Invalid start or limit values. Start: {start}, Limit: {limit}",
            method="GET",
            event_key="VALUE_ERROR",
            log_level="error",
            service_method="get_10_feeds",
        )
        raise ValueError(
            "Invalid arguments: Expect non-negative values within range 1-100"
        )

    posts: List[Post] = []
    comments_by_post: Dict[int, List[Comment]] = defaultdict(list)
    feeds: List[PostWithComments] | List[Dict[str, Any]] = []

    # Check cache first
    cache_hit = cache_get("feeds")
    if cache_hit:
        try:
            data = FeedCacheSchema().load(cache_hit)
            feeds = check_cache(data, start, limit)
            handle_log(
                f"Cached feeds loaded successfully. Returning subset.",
                method="GET",
                event_key="CACHE_SUCCESS",
                log_level="info",
                service_method="get_10_feeds",
                model="PostWithComments",
            )
            return feeds

        except (ValidationError, ValueError) as e:
            feed_logger.error(
                "Failed to load cached feeds with PostWithCommentsSchema().",
                extra={
                    "service_method": "get_10_feeds",
                    "error": e,
                    "block": "cache_get",
                },
            )
            handle_log(
                f"Failed to load cached feeds: Validation Error.",
                method="GET",
                event_key="CACHE_FAILURE",
                log_level="error",
                service_method="get_10_feeds",
                model="PostWithComments",
            )
    else:
        handle_log(
            f"Cache miss. Fetching data from API.",
            method="GET",
            event_key="CACHE_MISSED",
            log_level="info",
            service_method="get_10_feeds",
            model="PostWithComments",
        )

    # Fallthrough: Fetch data and build feeds
    posts_coro = get_data(POST_ENDPOINT, start, limit)
    comments_coro = get_data(COMMENT_ENDPOINT, start, limit)
    post_data, comment_data = await asyncio.gather(posts_coro, comments_coro)

    posts = create_model_list(post_data, Post)
    comments = create_model_list(comment_data, Comment)

    handle_log(
        f"Post_Cnt: {len(posts)}, Comment_Cnt: {len(comments)}",
        method="GET",
        event_key="FETCH_COUNTS",
        log_level="info",
        service_method="get_10_feeds",
        model=f"{Post.__name__}, {Comment.__name__}",
    )

    # Organize comments by post_id
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
        feed_data = [
            PostWithComments(post, comments_by_post.get(post._id, [])) for post in posts
        ]

        cache_model = FeedCache(start=start, feeds=feed_data)
        cache_data = FeedCacheSchema().dump(cache_model)
        # Cache for 10 seconds
        cache_set("feeds", cache_data, 10)

        feeds = feed_data[:limit]

    except (TypeError, ValueError) as e:
        handle_service_error(
            e,
            "Internal Server Error: Unexpected error failed to fetch feeds.",
            "Error creating PostWithComments instances",
            exc_type=ServiceException,
            service_method="get_10_feeds",
            model="PostWithComments",
        )
    handle_log(
        "Successfully created feed items",
        event_key="SUCCESS",
        log_level="info",
        service_method="get_10_feeds",
        model="PostWithComments",
        feed_count=len(feeds),
    )
    return feeds
