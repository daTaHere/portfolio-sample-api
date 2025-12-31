"""This module defines schemas for validating and (de)serializing feed-related data."""

from marshmallow import Schema, fields, INCLUDE


class CoordSchema(Schema):
    class Meta:
        unknown = INCLUDE

    lat = fields.Float(required=True)
    lon = fields.Float(required=True)


class MainSchema(Schema):
    class Meta:
        unknown = INCLUDE

    temp = fields.Float(required=True)
    feels_like = fields.Float(required=False)


class WeatherDescSchema(Schema):
    class Meta:
        unknown = INCLUDE

    main = fields.Str(required=True)
    description = fields.Str(required=False)


class OpenWeatherSchema(Schema):
    class Meta:
        unknown = INCLUDE

    id = fields.Int(required=True)
    name = fields.Str(required=True)
    dt = fields.Int(required=True)

    coord = fields.Nested(CoordSchema, required=True)
    main = fields.Nested(MainSchema, required=True)
    weather = fields.List(
        fields.Nested(WeatherDescSchema),
        required=True,
        validate=lambda x: len(x) > 0,
    )
