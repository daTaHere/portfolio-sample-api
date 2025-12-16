from app.models.feed_model import PostWithComments


class FeedCache:
    __slots__ = ("start", "end", "data")

    def __init__(self, start: int, feeds: list[PostWithComments]):
        self.start = start
        self.end = start + len(feeds)
        self.data = feeds
