"""This module defines schemas for validating and (de)serializing feed-related data."""

from marshmallow import Schema, fields, INCLUDE
from marshmallow.validate import Length


# Schemas for OpenWeatherMap API response validation
class OpenWeatherCoordSchema(Schema):
    class Meta:
        unknown = INCLUDE

    lat = fields.Float(required=True)
    lon = fields.Float(required=True)


class OpenWeatherMainSchema(Schema):
    class Meta:
        unknown = INCLUDE

    temp = fields.Float(required=True)
    feels_like = fields.Float(required=False)


class OpenWeatherDescSchema(Schema):
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

    coord = fields.Nested(OpenWeatherCoordSchema, required=True)
    main = fields.Nested(OpenWeatherMainSchema, required=True)
    weather = fields.List(
        fields.Nested(OpenWeatherDescSchema),
        required=True,
        validate=Length(min=1),
    )


# Schemas for internal WeatherModel validation
class WeatherTempSchema(Schema):
    current = fields.Float(required=True)
    temp_high = fields.Float(required=True)
    temp_low = fields.Float(required=True)


class WeatherDescSchema(Schema):
    id = fields.Int(required=True)
    main = fields.Str(required=True)
    description = fields.Str(required=True)
    icon = fields.Str(required=False)


class WindSchema(Schema):
    speed = fields.Float(required=True)
    deg = fields.Int(required=True)
    gust = fields.Float(required=False)


class WeatherExtraDetailsSchema(Schema):
    pressure = fields.Int(required=False)
    humidity = fields.Int(required=False)
    feels_like = fields.Float(required=False)
    sunrise = fields.Int(required=False)
    sunset = fields.Int(required=False)


class WeatherConditionsSchema(Schema):
    wind = fields.Nested(WindSchema, required=False)
    visibility = fields.Int(required=False)
    clouds = fields.Dict(keys=fields.Str(), values=fields.Int(), required=False)
    extra_details = fields.Nested(WeatherExtraDetailsSchema, required=False)


class WeatherSchema(Schema):
    id = fields.Int(required=True)
    name = fields.Str(required=True)
    country = fields.Str(required=True)
    coord = fields.Nested(OpenWeatherCoordSchema, required=True)
    dt = fields.Int(required=True)
    temperature = fields.Nested(WeatherTempSchema, required=True)
    weather = fields.List(
        fields.Nested(WeatherDescSchema),
        required=True,
    )
    conditions = fields.Nested(WeatherConditionsSchema, required=False)
