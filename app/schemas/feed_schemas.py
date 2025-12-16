"""Schemas for serializing and deserializing feed-related data."""

from typing import List
from marshmallow import Schema, fields, post_load
from app.models import Comment, Post, PostWithComments


class CommentSchema(Schema):
    id = fields.Int(required=True)
    post_id = fields.Int(required=True, data_key="postId")
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    body = fields.Str(required=True)


class PostSchema(Schema):
    id = fields.Int(required=True)
    userId = fields.Int(required=True)
    title = fields.Str(required=True)
    body = fields.Str(required=True)


class PostWithCommentsSchema(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)
    body = fields.Str(required=True)
    comments = fields.List(fields.Nested(CommentSchema), required=True)

    @post_load
    def make_post_with_comments(self, data, **kwargs) -> List[PostWithComments]:
        """Converts the deserialized data into a PostWithComments object."""
        post = Post(
            {
                "id": data["id"],
                "title": data["title"],
                "body": data["body"],
            }
        )
        comments = [Comment(c) for c in data["comments"]]
        return PostWithComments(post, comments)
