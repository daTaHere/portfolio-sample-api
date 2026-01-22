from marshmallow import Schema, fields


class WeatherCoordsCacheSchema(Schema):
    coords = fields.List(fields.Tuple((fields.Float(), fields.Float())), required=True)
