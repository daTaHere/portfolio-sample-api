from marshmallow import Schema, fields
from app.schemas.feed_schemas import PostWithCommentsSchema


class FeedCacheSchema(Schema):
    start = fields.Int(required=True)
    end = fields.Int(required=True)
    data = fields.List(fields.Nested(PostWithCommentsSchema), required=True)
