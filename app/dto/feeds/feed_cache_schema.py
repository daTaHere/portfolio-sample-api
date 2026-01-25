"""This module defines the caching schema for feed service."""

from marshmallow import Schema, fields
from app.schemas.feed_schemas import PostWithCommentsSchema


# DTO feed prefetch cache schema
class FeedCacheSchema(Schema):
    start = fields.Int(required=True)
    data = fields.List(fields.Nested(PostWithCommentsSchema), required=True)
