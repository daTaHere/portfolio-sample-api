from marshmallow import Schema, fields


class WeatherCoordsCacheSchema(Schema):
    data = fields.List(fields.Tuple((fields.Float(), fields.Float())), required=True)
