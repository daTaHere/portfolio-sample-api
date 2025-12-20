"""This module defines data models for the feed service API."""

from typing import List


class Post:
    """
    This class defines the internal Post data model.
    """

    __slots__ = ("_id", "title", "body")

    def __init__(self, post_data: dict):
        self._id: int = post_data.get("id")
        self.title: str = post_data.get("title", "")
        self.body: str = post_data.get("body", "")

    # id property read-only
    @property
    def id(self) -> int:
        return self._id


class Comment:
    """This class defines the internal Comment data model."""

    __slots__ = ("_id", "_postId", "name", "email", "body")

    def __init__(self, comment_data: dict):
        self._id: int = comment_data.get("id")
        self._postId: int = comment_data.get("post_id", None)
        self.name: str = comment_data.get("name", "")
        self.email: str = comment_data.get("email", "")
        self.body: str = comment_data.get("body", "")

    # id property read-only
    @property
    def id(self) -> int:
        return self._id

    # postId property read-only
    @property
    def post_id(self):
        return self._postId


class PostWithComments(Post):
    """
    This class defines the internal feed object returned by the feed service.
    It extends the Post model to include a list of associated comments.

    """

    __slots__ = ("comments",)

    def __init__(self, post: Post, comments: List[Comment]):
        self._id = post.id
        self.title = post.title
        self.body = post.body
        self.comments = comments
