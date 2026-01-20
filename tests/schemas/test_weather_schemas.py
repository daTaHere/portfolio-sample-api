import json
import pytest
from marshmallow import ValidationError
from app.schemas.weather_schemas import OpenWeatherSchema, WeatherSchema

# -------------------------------------------
#   Payloads for OpenWeahterSchema testing
# -------------------------------------------

OPENWEATHER_VALID_FULL_PAYLOAD = {
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

# -------------------------------------------
#     Payloads for WeahterSchema testing
# -------------------------------------------

WEATHER_VALID_FULL_PAYLOAD = {
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

WEATHER_VALID_MINIMAL_PAYLOAD = {
    "id": 5368361,
    "name": "Los Angeles",
    "country": "US",
    "coord": {"lon": -118.24, "lat": 34.05},
    "temperature": {"current": 292.2, "temp_high": 294.14, "temp_low": 290.06},
    "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}],
}

EXPECTED_WEATHER_SERIALIZED_PAYLOAD = {
    "id": 5368361,
    "name": "Los Angeles",
    "country": "US",
    "coord": {"lat": 34.05, "lon": -118.24},
    "temperature": {"current": 292.2, "temp_high": 294.14, "temp_low": 290.06},
    "weather": [
        {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01n"}
    ],
}


class TestOpenWeatherSchemas:
    def test_load_full_payload(self):
        loaded = OpenWeatherSchema().load(OPENWEATHER_VALID_FULL_PAYLOAD)
        # Extra fields are preserved
        assert loaded["top_level_extra"] == "kept"
        assert loaded["coord"]["coord_extra"] == "kept"
        assert loaded["main"]["main_extra"] == 123
        assert loaded["weather"][0]["desc_extra"] == {"nested": True}

    def test_load_minimal_payload(self):
        loaded = OpenWeatherSchema().load(OPENWEATHER_MINIMAL_VALID_PAYLOAD)
        # Minimal payload has no extra fields
        assert "coord_extra" not in loaded["coord"]
        assert "main_extra" not in loaded["main"]

    def test_dump_removes_unknown_fields(self):
        dumped = OpenWeatherSchema().dump(OPENWEATHER_VALID_FULL_PAYLOAD)
        assert "coord_extra" not in dumped["coord"]
        assert "main_extra" not in dumped["main"]

    def test_load_invalid_missing_fields(self):
        invalid_payload = {"name": "LA", "dt": 1, "coord": {"lat": 0, "lon": 0}}
        with pytest.raises(ValidationError) as exc:
            OpenWeatherSchema().load(invalid_payload)
        assert "id" in exc.value.messages


class TestWeatherSchemas:
    def test_load_full_payload(self):
        loaded = WeatherSchema().load(WEATHER_VALID_FULL_PAYLOAD)
        assert loaded["coord"]["lat"] == 34.05
        assert loaded["coord"]["lon"] == -118.24
        # Extra fields removed
        assert "coord_extra" not in loaded["coord"]
        assert loaded["conditions"]["wind"]["speed"] == 0.0

    def test_load_minimal_payload(self):
        loaded = WeatherSchema().load(WEATHER_VALID_MINIMAL_PAYLOAD)
        assert loaded["coord"]["lat"] == 34.05
        assert loaded["coord"]["lon"] == -118.24
        assert "conditions" not in loaded

    def test_dump_removes_none_or_empty_optionals(self):
        payload = WEATHER_VALID_FULL_PAYLOAD.copy()
        payload["conditions"] = {}
        dumped = WeatherSchema().dump(payload)
        assert "conditions" not in dumped

    def test_dump_and_dumps_json_equivalence(self):
        payload = WEATHER_VALID_FULL_PAYLOAD.copy()
        del payload["dt"]
        payload["conditions"] = {}
        dumped_json = WeatherSchema().dumps(payload)
        assert json.loads(dumped_json) == EXPECTED_WEATHER_SERIALIZED_PAYLOAD

    @pytest.mark.parametrize(
        "invalid_payload,missing_field",
        [
            # Missing top-level required fields
            (
                {
                    "name": "LA",
                    "coord": {"lat": 0, "lon": 0},
                    "temperature": {"current": 1, "temp_high": 1, "temp_low": 1},
                    "weather": [{"id": 1, "main": "Clear", "description": "desc"}],
                },
                "id",
            ),
            (
                {
                    "id": 1,
                    "coord": {"lat": 0, "lon": 0},
                    "temperature": {"current": 1, "temp_high": 1, "temp_low": 1},
                    "weather": [{"id": 1, "main": "Clear", "description": "desc"}],
                },
                "name",
            ),
            (
                {
                    "id": 1,
                    "name": "LA",
                    "temperature": {"current": 1, "temp_high": 1, "temp_low": 1},
                    "weather": [{"id": 1, "main": "Clear", "description": "desc"}],
                },
                "coord",
            ),
            (
                {
                    "id": 1,
                    "name": "LA",
                    "coord": {"lat": 0, "lon": 0},
                    "weather": [{"id": 1, "main": "Clear", "description": "desc"}],
                },
                "temperature",
            ),
            (
                {
                    "id": 1,
                    "name": "LA",
                    "coord": {"lat": 0, "lon": 0},
                    "temperature": {"current": 1, "temp_high": 1, "temp_low": 1},
                },
                "weather",
            ),
            # Empty list for required weather
            (
                {
                    "id": 1,
                    "name": "LA",
                    "coord": {"lat": 0, "lon": 0},
                    "temperature": {"current": 1, "temp_high": 1, "temp_low": 1},
                    "weather": [],
                },
                "weather",
            ),
            # Invalid type
            (
                {
                    "id": 1,
                    "name": "LA",
                    "coord": {"lat": "not_float", "lon": -118.0},
                    "temperature": {"current": 1, "temp_high": 1, "temp_low": 1},
                    "weather": [{"id": 1, "main": "Clear", "description": "desc"}],
                },
                "coord",
            ),
        ],
    )
    def test_load_invalid_payloads(self, invalid_payload, missing_field):
        with pytest.raises(ValidationError) as exc:
            WeatherSchema().load(invalid_payload)
        assert missing_field in exc.value.messages

    def test_optional_fields_behavior(self):
        # conditions = None or empty dict/list → should be dropped
        for payload in [
            {"conditions": None},
            {"conditions": {}},
            {"conditions": []},
        ]:
            full_payload = WEATHER_VALID_MINIMAL_PAYLOAD.copy()
            full_payload.update(payload)
            dumped = WeatherSchema().dump(full_payload)
            assert "conditions" not in dumped
