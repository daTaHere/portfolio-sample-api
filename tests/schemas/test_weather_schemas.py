import json
import pytest
from marshmallow import ValidationError
from app.schemas.weather_schemas import OpenWeatherSchema, WeatherSchema

OPENWEATHER_VALID_PAYLOAD = {
    "id": 5368361,
    "name": "Los Angeles",
    "dt": 1768706508,
    "coord": {"lon": -118.24, "lat": 34.05, "coord_extra": "kept"},
    "main": {"temp": 292.2, "feels_like": 291.21, "main_extra": 123},
    "weather": [
        {"main": "Clear", "description": "clear sky", "desc_extra": {"nested": True}}
    ],
    "top_level_extra": "kept",
}

OPENWEATHER_MINIMAL_VALID_PAYLOAD = {
    "id": 5368361,
    "name": "Los Angeles",
    "dt": 1768706508,
    "coord": {"lon": -118.24, "lat": 34.05},
    "main": {"temp": 292.2, "feels_like": 291.21},
    "weather": [{"main": "Clear", "description": "clear sky"}],
}


WEATHER_VALID_PAYLOAD = {
    "id": 5368361,
    "name": "Los Angeles",
    "country": "US",
    "coord": {"lon": -118.24, "lat": 34.05, "coord_extra": "kept"},
    "dt": 1768706508,
    "temperature": {"current": 292.2, "temp_high": 294.14, "temp_low": 290.06},
    "weather": [
        {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01n"}
    ],
    "conditions": {
        "wind": {"speed": 0.0, "deg": 0, "gust": 1.2},
        "visibility": 10000,
        "clouds": {"all": 0},
        "extra_details": {
            "pressure": 1019,
            "humidity": 40,
            "feels_like": 291.21,
            "sunrise": 1768661857,
            "sunset": 1768698490,
        },
    },
}


class TestOpenWeatherSchemas:
    def test_openweather_schema_deserialize_object_success(self):
        test_payload = OPENWEATHER_VALID_PAYLOAD
        loaded = OpenWeatherSchema().load(test_payload)

        assert loaded["id"] == test_payload["id"]
        assert loaded["name"] == test_payload["name"]
        assert loaded["dt"] == test_payload["dt"]
        assert loaded["top_level_extra"] == "kept"
        assert loaded["coord"]["coord_extra"] == "kept"
        assert loaded["main"]["main_extra"] == 123
        assert loaded["weather"][0]["desc_extra"] == {"nested": True}

    def test_openweather_schema_deserialize_json_success(self):
        test_payload = json.dumps(OPENWEATHER_VALID_PAYLOAD)
        loaded = OpenWeatherSchema().loads(test_payload)

        assert loaded["id"] == OPENWEATHER_VALID_PAYLOAD["id"]
        assert loaded["name"] == OPENWEATHER_VALID_PAYLOAD["name"]
        assert loaded["dt"] == OPENWEATHER_VALID_PAYLOAD["dt"]
        assert loaded["top_level_extra"] == "kept"
        assert loaded["coord"]["coord_extra"] == "kept"
        assert loaded["main"]["main_extra"] == 123
        assert loaded["weather"][0]["desc_extra"] == {"nested": True}

    def test_openweather_schema_serialize_to_dict(self):

        test_data = OPENWEATHER_VALID_PAYLOAD
        dumped = OpenWeatherSchema().dump(test_data)

        assert isinstance(dumped, dict)
        assert dumped["id"] == test_data["id"]
        assert dumped["coord"]["lon"] == -118.24
        assert dumped["weather"][0]["main"] == "Clear"

    def test_openweather_schema_serialize_to_json(self):

        test_data = OPENWEATHER_VALID_PAYLOAD
        dumped = OpenWeatherSchema().dumps(test_data)

        assert isinstance(dumped, str)
        assert OPENWEATHER_MINIMAL_VALID_PAYLOAD == json.loads(dumped)

    @pytest.mark.parametrize(
        "invalid_payload,missing_field",
        [
            (
                {
                    "name": "Los Angeles",
                    "dt": 1,
                    "coord": {"lon": 0.0, "lat": 0.0},
                    "main": {"temp": 1.0},
                    "weather": [{"main": "Clear"}],
                },
                "id",
            ),
            (
                {
                    "id": 1,
                    "dt": 1,
                    "coord": {"lon": 0.0, "lat": 0.0},
                    "main": {"temp": 1.0},
                    "weather": [{"main": "Clear"}],
                },
                "name",
            ),
            (
                {
                    "id": 1,
                    "name": "Los Angeles",
                    "coord": {"lon": 0.0, "lat": 0.0},
                    "main": {"temp": 1.0},
                    "weather": [{"main": "Clear"}],
                },
                "dt",
            ),
            (
                {
                    "id": 1,
                    "name": "Los Angeles",
                    "dt": 1,
                    "main": {"temp": 1.0},
                    "weather": [{"main": "Clear"}],
                },
                "coord",
            ),
            (
                {
                    "id": 1,
                    "name": "Los Angeles",
                    "dt": 1,
                    "coord": {"lon": 0.0, "lat": 0.0},
                    "weather": [{"main": "Clear"}],
                },
                "main",
            ),
            (
                {
                    "id": 1,
                    "name": "Los Angeles",
                    "dt": 1,
                    "coord": {"lon": 0.0, "lat": 0.0},
                    "main": {"temp": 1.0},
                },
                "weather",
            ),
            (
                {
                    "id": 1,
                    "name": "Los Angeles",
                    "dt": 1,
                    "coord": {"lon": 0.0, "lat": 0.0},
                    "main": {"temp": 1.0},
                    "weather": [],
                },
                "weather",
            ),
        ],
    )
    def test_openweather_schema_missing_required_fields(
        self, invalid_payload, missing_field
    ):

        with pytest.raises(ValidationError) as exc:
            OpenWeatherSchema().load(invalid_payload)

        assert missing_field in exc.value.messages


# class TestWeatherSchemas:
#     def test_weather_schema_load_full_payload_success(self):
#         loaded = WeatherSchema().load(WEATHER_VALID_PAYLOAD)

#         assert loaded["id"] == WEATHER_VALID_PAYLOAD["id"]
#         assert loaded["name"] == WEATHER_VALID_PAYLOAD["name"]
#         assert loaded["country"] == WEATHER_VALID_PAYLOAD["country"]
#         assert loaded["dt"] == WEATHER_VALID_PAYLOAD["dt"]

#         # coord uses OpenWeatherCoordSchema (Meta.unknown = INCLUDE)
#         assert loaded["coord"]["lon"] == -118.24
#         assert loaded["coord"]["lat"] == 34.05
#         assert loaded["coord"]["coord_extra"] == "kept"

#         assert loaded["temperature"] == WEATHER_VALID_PAYLOAD["temperature"]
#         assert loaded["weather"][0]["id"] == 800
#         assert loaded["conditions"]["wind"]["speed"] == 0.0
#         assert loaded["conditions"]["extra_details"]["pressure"] == 1019

#     def test_weather_schema_load_allows_missing_optional_conditions(self):
#         loaded = WeatherSchema().load(WEATHER_MINIMAL_VALID_PAYLOAD)

#         assert loaded["id"] == WEATHER_MINIMAL_VALID_PAYLOAD["id"]
#         assert loaded["temperature"] == WEATHER_MINIMAL_VALID_PAYLOAD["temperature"]
#         assert loaded["weather"][0]["description"] == "clear sky"
#         assert "conditions" not in loaded

#     def test_weather_schema_rejects_unknown_top_level_fields_by_default(self):
#         payload = dict(WEATHER_MINIMAL_VALID_PAYLOAD)
#         payload["unexpected"] = "nope"

#         with pytest.raises(ValidationError) as exc:
#             WeatherSchema().load(payload)

#         assert "unexpected" in exc.value.messages


#     @pytest.mark.parametrize(
#         "bad_patch,expected_field",
#         [
#             ({"dt": None}, "dt"),
#             ({"temperature": {"current": 1.0, "temp_high": 2.0}}, "temperature"),
#             ({"weather": [{"id": 1, "main": "Clear"}]}, "weather"),
#             ({"coord": {"lon": -118.24}}, "coord"),
#         ],
#     )
#     def test_weather_schema_requires_required_fields_and_nested_requirements(
#         self, bad_patch, expected_field
#     ):
#         payload = dict(WEATHER_MINIMAL_VALID_PAYLOAD)
#         payload.update(bad_patch)

#         with pytest.raises(ValidationError) as exc:
#             WeatherSchema().load(payload)

#         assert expected_field in exc.value.messages

#     def test_weather_schema_roundtrip_dump_shape_is_stable(self):
#         loaded = WeatherSchema().load(WEATHER_VALID_PAYLOAD)
#         dumped = WeatherSchema().dump(loaded)

#         # Dumped output should contain the public API fields (no top-level unknowns).
#         for key in (
#             "id",
#             "name",
#             "country",
#             "coord",
#             "dt",
#             "temperature",
#             "weather",
#         ):
#             assert key in dumped

#         assert dumped["id"] == WEATHER_VALID_PAYLOAD["id"]
#         assert dumped["coord"]["lon"] == -118.24
#         assert dumped["weather"][0]["main"] == "Clear"


# import unittest
# import pytest
# from marshmallow import ValidationError
# from app.schemas.weather_schemas import OpenWeatherSchema, WeatherSchema

# OPENWEATHER_VALID_PAYLOAD = {
#     "id": 5368361,
#     "name": "Los Angeles",
#     "dt": 1768706508,
#     "coord": {"lon": -118.24, "lat": 34.05, "coord_extra": "kept"},
#     "main": {"temp": 292.2, "feels_like": 291.21, "main_extra": 123},
#     "weather": [
#         {
#             "main": "Clear",
#             "description": "clear sky",
#             "desc_extra": {"nested": True},
#         }
#     ],
#     "top_level_extra": "kept",
# }

# OPENWEATHER_MINIMAL_VALID_PAYLOAD = {
#     "id": 1,
#     "name": "X",
#     "dt": 1,
#     "coord": {"lon": 0.0, "lat": 0.0},
#     "main": {"temp": 1.0},
#     "weather": [{"main": "Clear"}],
# }

# WEATHER_VALID_PAYLOAD = {
#     "id": 5368361,
#     "name": "Los Angeles",
#     "country": "US",
#     "coord": {"lon": -118.24, "lat": 34.05, "coord_extra": "kept"},
#     "dt": 1768706508,
#     "temperature": {"current": 292.2, "temp_high": 294.14, "temp_low": 290.06},
#     "weather": [
#         {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01n"}
#     ],
#     "conditions": {
#         "wind": {"speed": 0.0, "deg": 0, "gust": 1.2},
#         "visibility": 10000,
#         "clouds": {"all": 0},
#         "extra_details": {
#             "pressure": 1019,
#             "humidity": 40,
#             "feels_like": 291.21,
#             "sunrise": 1768661857,
#             "sunset": 1768698490,
#         },
#     },
# }

# WEATHER_MINIMAL_VALID_PAYLOAD = {
#     "id": 5368361,
#     "name": "Los Angeles",
#     "country": "US",
#     "coord": {"lon": -118.24, "lat": 34.05},
#     "dt": 1768706508,
#     "temperature": {"current": 292.2, "temp_high": 294.14, "temp_low": 290.06},
#     "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}],
#     # conditions intentionally omitted (optional)
# }


# class TestOpenWeatherSchemas(unittest.TestCase):
#     def test_openweather_schema_load_allows_unknown_fields_and_includes_them(self):
#         loaded = OpenWeatherSchema().load(OPENWEATHER_VALID_PAYLOAD)

#         assert loaded["id"] == OPENWEATHER_VALID_PAYLOAD["id"]
#         assert loaded["name"] == OPENWEATHER_VALID_PAYLOAD["name"]
#         assert loaded["dt"] == OPENWEATHER_VALID_PAYLOAD["dt"]

#         # Meta.unknown = INCLUDE should keep unknown fields at all levels.
#         assert loaded["top_level_extra"] == "kept"
#         assert loaded["coord"]["coord_extra"] == "kept"
#         assert loaded["main"]["main_extra"] == 123
#         assert loaded["weather"][0]["desc_extra"] == {"nested": True}

#     def test_openweather_schema_load_minimal_valid_payload(self):
#         loaded = OpenWeatherSchema().load(OPENWEATHER_MINIMAL_VALID_PAYLOAD)

#         assert loaded["id"] == 1
#         assert loaded["name"] == "X"
#         assert loaded["dt"] == 1
#         assert loaded["coord"] == {"lon": 0.0, "lat": 0.0}
#         assert loaded["main"]["temp"] == 1.0
#         assert loaded["weather"][0]["main"] == "Clear"

#     @pytest.mark.parametrize(
#         "invalid_payload,missing_field",
#         [
#             (
#                 {
#                     "name": "Los Angeles",
#                     "dt": 1,
#                     "coord": {"lon": 0.0, "lat": 0.0},
#                     "main": {"temp": 1.0},
#                     "weather": [{"main": "Clear"}],
#                 },
#                 "id",
#             ),
#             (
#                 {
#                     "id": 1,
#                     "dt": 1,
#                     "coord": {"lon": 0.0, "lat": 0.0},
#                     "main": {"temp": 1.0},
#                     "weather": [{"main": "Clear"}],
#                 },
#                 "name",
#             ),
#             (
#                 {
#                     "id": 1,
#                     "name": "Los Angeles",
#                     "coord": {"lon": 0.0, "lat": 0.0},
#                     "main": {"temp": 1.0},
#                     "weather": [{"main": "Clear"}],
#                 },
#                 "dt",
#             ),
#             (
#                 {
#                     "id": 1,
#                     "name": "Los Angeles",
#                     "dt": 1,
#                     "main": {"temp": 1.0},
#                     "weather": [{"main": "Clear"}],
#                 },
#                 "coord",
#             ),
#             (
#                 {
#                     "id": 1,
#                     "name": "Los Angeles",
#                     "dt": 1,
#                     "coord": {"lon": 0.0, "lat": 0.0},
#                     "weather": [{"main": "Clear"}],
#                 },
#                 "main",
#             ),
#             (
#                 {
#                     "id": 1,
#                     "name": "Los Angeles",
#                     "dt": 1,
#                     "coord": {"lon": 0.0, "lat": 0.0},
#                     "main": {"temp": 1.0},
#                 },
#                 "weather",
#             ),
#         ],
#     )
#     def test_openweather_schema_requires_top_level_fields(self, invalid_payload, missing_field):
#         with pytest.raises(ValidationError) as exc:
#             OpenWeatherSchema().load(invalid_payload)

#         assert missing_field in exc.value.messages

#     def test_openweather_schema_rejects_empty_weather_list(self):
#         payload = {
#             "id": 1,
#             "name": "Los Angeles",
#             "dt": 1,
#             "coord": {"lon": 0.0, "lat": 0.0},
#             "main": {"temp": 1.0},
#             "weather": [],
#         }

#         with pytest.raises(ValidationError) as exc:
#             OpenWeatherSchema().load(payload)

#         assert "weather" in exc.value.messages


# class TestWeatherSchemas(unittest.TestCase):
#     def test_weather_schema_load_full_payload(self):
#         loaded = WeatherSchema().load(WEATHER_VALID_PAYLOAD)

#         assert loaded["id"] == WEATHER_VALID_PAYLOAD["id"]
#         assert loaded["name"] == WEATHER_VALID_PAYLOAD["name"]
#         assert loaded["country"] == WEATHER_VALID_PAYLOAD["country"]
#         assert loaded["dt"] == WEATHER_VALID_PAYLOAD["dt"]

#         # coord uses OpenWeatherCoordSchema (Meta.unknown = INCLUDE)
#         assert loaded["coord"]["lon"] == -118.24
#         assert loaded["coord"]["lat"] == 34.05
#         assert loaded["coord"]["coord_extra"] == "kept"

#         assert loaded["temperature"] == WEATHER_VALID_PAYLOAD["temperature"]
#         assert loaded["weather"][0]["id"] == 800
#         assert loaded["conditions"]["wind"]["speed"] == 0.0
#         assert loaded["conditions"]["extra_details"]["pressure"] == 1019

#     def test_weather_schema_load_allows_missing_optional_conditions(self):
#         loaded = WeatherSchema().load(WEATHER_MINIMAL_VALID_PAYLOAD)

#         assert loaded["id"] == WEATHER_MINIMAL_VALID_PAYLOAD["id"]
#         assert loaded["temperature"] == WEATHER_MINIMAL_VALID_PAYLOAD["temperature"]
#         assert loaded["weather"][0]["description"] == "clear sky"
#         assert "conditions" not in loaded

#     def test_weather_schema_rejects_unknown_top_level_fields_by_default(self):
#         payload = dict(WEATHER_MINIMAL_VALID_PAYLOAD)
#         payload["unexpected"] = "nope"

#         with pytest.raises(ValidationError) as exc:
#             WeatherSchema().load(payload)

#         assert "unexpected" in exc.value.messages

#     @pytest.mark.parametrize(
#         "bad_patch,expected_field",
#         [
#             ({"dt": None}, "dt"),
#             ({"temperature": {"current": 1.0, "temp_high": 2.0}}, "temperature"),
#             ({"weather": [{"id": 1, "main": "Clear"}]}, "weather"),
#             ({"coord": {"lon": -118.24}}, "coord"),
#         ],
#     )
#     def test_weather_schema_requires_required_fields_and_nested_requirements(
#         self, bad_patch, expected_field
#     ):
#         payload = dict(WEATHER_MINIMAL_VALID_PAYLOAD)
#         payload.update(bad_patch)

#         with pytest.raises(ValidationError) as exc:
#             WeatherSchema().load(payload)

#         assert expected_field in exc.value.messages

#     def test_weather_schema_roundtrip_dump_shape_is_stable(self):
#         loaded = WeatherSchema().load(WEATHER_VALID_PAYLOAD)
#         dumped = WeatherSchema().dump(loaded)

#         # Dumped output should contain the public API fields (no top-level unknowns).
#         for key in (
#             "id",
#             "name",
#             "country",
#             "coord",
#             "dt",
#             "temperature",
#             "weather",
#         ):
#             assert key in dumped

#         assert dumped["id"] == WEATHER_VALID_PAYLOAD["id"]
#         assert dumped["coord"]["lon"] == -118.24
#         assert dumped["weather"][0]["main"] == "Clear"
