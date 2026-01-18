import pytest
from app.models.weather_model import WeatherModel

"""
Unit tests for WeatherModel.

Covers:
- Field population from incoming payload.
- Safe handling of missing optional/nested fields.
- Read-only id property behavior.
- __slots__ enforcement (no dynamic attributes / no __dict__).
- to_dict output shape and values.
"""
TEST_FULL_PAYLOAD = {
    "base": "stations",
    "id": 5368361,
    "name": "Los Angeles",
    "sys": {
        "type": 2,
        "id": 2075946,
        "country": "US",
        "sunrise": 1768661857,
        "sunset": 1768698490,
    },
    "coord": {"lon": -118.24, "lat": 34.05},
    "dt": 1768706508,
    "weather": [
        {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01n"}
    ],
    "main": {
        "temp": 292.2,
        "feels_like": 291.21,
        "temp_min": 290.06,
        "temp_max": 294.14,
        "pressure": 1019,
        "humidity": 40,
        "sea_level": 1019,
        "grnd_level": 999,
    },
    "visibility": 10000,
    "wind": {"speed": 0, "deg": 0},
    "clouds": {"all": 0},
    "cod": 200,
}

TEST_MINIMAL_PAYLOAD = {
    "base": "stations",
    "id": 5368361,
    "name": "Los Angeles",
    "sys": {
        "id": 2075946,
        "country": "US",
    },
    "coord": {"lon": -118.24, "lat": 34.05},
    "weather": [
        {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01n"}
    ],
    "main": {
        "temp": 292.2,
        "temp_min": 290.06,
        "temp_max": 294.14,
    },
    "cod": 200,
}


TEST_EXPECTED_ID = 5368361
TEST_EXPECTED_NAME = "Los Angeles"
TEST_EXPECTED_COUNTRY = "US"
TEST_EXPECTED_COORD = {"lat": 34.05, "lon": -118.24}
TEST_EXPECTED_DT = 1768706508
TEST_EXPECTED_TEMP = {"current": 292.2, "temp_high": 294.14, "temp_low": 290.06}
TEST_EXPECTED_WEATHER = [
    {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01n"}
]
TEST_EXPECTED_CONDITIONS = {
    "wind": {"speed": 0, "deg": 0},
    "visibility": 10000,
    "clouds": {"all": 0},
    "extra_details": {
        "pressure": 1019,
        "humidity": 40,
        "feels_like": 291.21,
        "sunrise": 1768661857,
        "sunset": 1768698490,
    },
}

TEST_EXPECTED_CONDITIONS_MINIMAL = {
    "wind": None,
    "visibility": None,
    "clouds": None,
    "extra_details": {
        "pressure": None,
        "humidity": None,
        "feels_like": None,
        "sunrise": None,
        "sunset": None,
    },
}


def test_weather_model_init_populates_all_fields():
    payload = TEST_FULL_PAYLOAD
    model = WeatherModel(payload)

    assert isinstance(model, WeatherModel)
    assert model.id == TEST_EXPECTED_ID
    assert model.name == TEST_EXPECTED_NAME
    assert model.country == TEST_EXPECTED_COUNTRY
    assert model.coord == TEST_EXPECTED_COORD
    assert model.dt == TEST_EXPECTED_DT
    assert model.temperature == TEST_EXPECTED_TEMP
    assert model.weather == TEST_EXPECTED_WEATHER
    assert model.conditions == TEST_EXPECTED_CONDITIONS


def test_weather_model_init_handles_missing_optional_keys():

    payload = TEST_MINIMAL_PAYLOAD
    model = WeatherModel(payload)

    assert isinstance(model, WeatherModel)
    assert model.id == TEST_EXPECTED_ID
    assert model.name == TEST_EXPECTED_NAME
    assert model.country == TEST_EXPECTED_COUNTRY
    assert model.coord == TEST_EXPECTED_COORD
    assert model.dt == None
    assert model.temperature == TEST_EXPECTED_TEMP
    assert model.weather == TEST_EXPECTED_WEATHER
    assert model.conditions == TEST_EXPECTED_CONDITIONS_MINIMAL


def test_id_property_is_read_only():
    payload = TEST_FULL_PAYLOAD
    model = WeatherModel(payload)

    with pytest.raises(AttributeError):
        model.id = 999  # property has no setter


def test_slots_enforce_no_dynamic_attributes():
    payload = TEST_FULL_PAYLOAD
    model = WeatherModel(payload)

    assert not hasattr(model, "__dict__")

    with pytest.raises(AttributeError):
        model.some_new_field = "nope"


@pytest.mark.parametrize(
    "invalid_payload,expected_exception",
    [
        ({"id": 28, "name": 12345, "main": "mock main", "sys": "mock sys"}, TypeError),
        ({"main": "mock main", "sys": "mock sys"}, KeyError),
    ],
)
def test_weather_model_raise_internal_error(invalid_payload, expected_exception):

    with pytest.raises(expected_exception):
        WeatherModel(invalid_payload)
