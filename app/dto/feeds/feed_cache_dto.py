"""This module defines the caching DTO for feed service."""

from app.models.feed_model import PostWithComments


# DTO feed cache model
class FeedCache:
    __slots__ = ("start", "end", "data")

    def __init__(self, start: int, feeds: list[PostWithComments]):
        self.start = start
        self.end = start + len(feeds)
        self.data = feeds
