"""
Feed service layer.
Business logic for feed operations.
"""

import asyncio

from collections import defaultdict
from typing import Dict, List, TypeVar

from app.logging import logger
from app.models import Post, Comment, PostWithComments

from app.exceptions.base import ServiceException
from app.exceptions.exception_handlers import handle_service_error

from app.services.feeds.feed_validators import get_data
from app.services.feeds.feed_builders import create_model_list

from app.utils.logger_helper import handle_log


POST_ENDPOINT = "posts"
COMMENT_ENDPOINT = "comments"


T = TypeVar("T", bound=Post | Comment)


async def get_10_feeds(start: int = 0, limit: int = 10) -> List[PostWithComments]:
    """
    Orchestrates fetching posts and comments, builds feed objects.
    """

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
            PostWithComments(post, comments_by_post.get(post._id, [])) for post in posts
        ]

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
