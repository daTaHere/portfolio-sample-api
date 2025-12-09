"""Schemas for serializing and deserializing feed-related data."""

from marshmallow import Schema, fields


class CommentSchema(Schema):
    id = fields.Int(required=True)
    postId = fields.Int(required=True)
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
