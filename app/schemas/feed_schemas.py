"""Schemas for serializing and deserializing feed-related data."""

from typing import List
from marshmallow import Schema, fields, post_load, post_dump
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
