from typing import List


class Post:
    """
    Represents a blog post fetched from an API.

    Attributes:
        id (int): Post ID (read-only).
        title (str): Post title.
        body (str): Post content.
    """

    __slots__ = ("_id", "title", "body")

    def __init__(self, post_data: dict):
        self._id: int = post_data.get("id")
        self.title: str = post_data.get("title", "")
        self.body: str = post_data.get("body", "")

    @property
    def id(self) -> int:
        return self._id


class Comment:
    __slots__ = ("_id", "_postId", "name", "email", "body")

    def __init__(self, comment_data: dict):
        self._id: int = comment_data.get("id")
        self._postId: int = comment_data.get("post_id", "")
        self.name: str = comment_data.get("name", "")
        self.email: str = comment_data.get("email", "")
        self.body: str = comment_data.get("body", "")

    @property
    def id(self) -> int:
        return self._id

    @property
    def post_id(self):
        return self._postId


class PostWithComments(Post):
    __slots__ = ("comments",)

    def __init__(self, posts: Post, comments: List[Comment]):
        self._id = posts.id
        self.title = posts.title
        self.body = posts.body
        self.comments = comments
