"""
Comprehensive unit tests for the request_weather function.
Covers:
- Successful data retrieval.
- Handling transport layer errors with retries.
- Correct exception raising for various failure scenarios.
- Asynchronous HTTP request mocking with respx.
"""

from unittest.mock import patch
from typing import List, Tuple

from app.models.weather_model import WeatherModel
from app.services.weather.weather_builders import (
    create_fetch_list,
    process_from_cache,
    create_weather_model,
)
from tests.utils import count_log_events
from tests.services.weathers.test_mock_weather_data import (
    DEFAULT_WEATHER_CITIES,
    mock_weather_input_test_data,
    mock_weather_expected_data,
)

from app.schemas.weather_schemas import WeatherSchema

MOCK_CREATE_MODEL_INPUT = [
    mock_weather_input_test_data("Los Angeles"),
    mock_weather_input_test_data("New York"),
]


EXPECTED_CREATE_MODEL_RESPONSE = [
    mock_weather_expected_data("Los Angeles"),
    mock_weather_expected_data("New York"),
]


# ------   create_fetch_list tests   ------ #
def test_create_fetch_list_with_user_coords(captured_logs):

    user_coords = (37.77, -122.42)  # San Francisco
    fetch_list = create_fetch_list(user_coords)

    log_counts = count_log_events(captured_logs, "create_fetch_list")

    assert len(fetch_list) == 10
    assert fetch_list[0] == user_coords
    assert fetch_list[-1] == DEFAULT_WEATHER_CITIES[-2]  # last city shifted down
    assert log_counts.get("INFO") == 1
    assert log_counts.get("PREPEND_USER_COORDS") == 1
    assert log_counts.get("SUCCESS") == 1


def test_create_fetch_list_user_coords_in_default(captured_logs):

    user_coords = DEFAULT_WEATHER_CITIES[3]  # Chicago
    fetch_list = create_fetch_list(user_coords)

    log_counts = count_log_events(captured_logs, "create_fetch_list")

    assert len(fetch_list) == 10
    assert fetch_list[0] == DEFAULT_WEATHER_CITIES[3]
    assert fetch_list[3] == DEFAULT_WEATHER_CITIES[0]
    assert log_counts.get("INFO") == 1
    assert log_counts.get("SWAP_LOCATION_ORDER") == 1


def test_create_fetch_list_no_user_coords(captured_logs):

    fetch_list = create_fetch_list(None)

    log_counts = count_log_events(captured_logs, "create_fetch_list")

    assert len(fetch_list) == 10
    assert fetch_list == DEFAULT_WEATHER_CITIES
    assert log_counts.get("INFO") == 1
    assert log_counts.get("GET_DEFAULT_CITIES") == 1


# ------   process_from_cache tests   ------ #
def test_process_from_cache_all_miss(captured_logs):

    with patch("app.services.weather.weather_builders.cache_get", return_value=None):
        cached_data, missing_coords = process_from_cache(DEFAULT_WEATHER_CITIES)

    log_counts = count_log_events(captured_logs, "process_from_cache")

    assert all(isinstance(item, type(None)) for item in cached_data)
    assert len(missing_coords) == len(DEFAULT_WEATHER_CITIES)
    assert isinstance(missing_coords, List)
    assert all(isinstance(coord, Tuple) for coord in missing_coords)
    assert (
        missing_coords[0][0] == 0 and missing_coords[0][1] == DEFAULT_WEATHER_CITIES[0]
    )
    assert (
        missing_coords[-1][0] == 9
        and missing_coords[-1][1] == DEFAULT_WEATHER_CITIES[-1]
    )
    assert log_counts.get("PROCESS_FROM_CACHE") == 1
    assert log_counts.get("SUCCESS") == 1


# ------   process_from_cache tests   ------ #
def test_process_from_cache_partial_hit(captured_logs):

    def mock_cache_get(key: str):
        cache_map = {
            "34.05,-118.24": mock_weather_expected_data("Los Angeles"),
            "29.76,-95.36": mock_weather_expected_data("Houston"),
            "25.76,-80.19": mock_weather_expected_data("Miami"),
        }
        return cache_map.get(key, None)

    with patch(
        "app.services.weather.weather_builders.cache_get",
        side_effect=mock_cache_get,
    ):
        cached_data, missing_coords = process_from_cache(DEFAULT_WEATHER_CITIES)

    log_counts = count_log_events(captured_logs, "process_from_cache")

    assert len(missing_coords) == 7
    assert all(
        (isinstance(idx, int) and isinstance(coord, tuple))
        for idx, coord in missing_coords
    )
    assert cached_data[0]["name"] == "Los Angeles"
    assert cached_data[3]["name"] == "Houston"
    assert cached_data[4]["name"] == "Miami"
    assert log_counts.get("PROCESS_FROM_CACHE") == 1
    assert log_counts.get("SUCCESS") == 1


# ------  create_weather_model tests  ------  #
def test_create_weather_model_success(captured_logs):

    test_data = MOCK_CREATE_MODEL_INPUT

    with patch("app.services.cache_service.cache_set", return_value=None):
        weather_models = create_weather_model(test_data)

    log_counts = count_log_events(captured_logs, "create_weather_model")

    assert (
        WeatherSchema(many=True).dump(weather_models) == EXPECTED_CREATE_MODEL_RESPONSE
    )
    assert all(isinstance(item, WeatherModel) for item in weather_models)
    assert log_counts.get("INFO") == 1
    assert log_counts.get("SUCCESS") == 1


def test_create_weather_model_from_schema(captured_logs):

    test_data = [{"test": "Validation Error"}]
    with patch("app.services.cache_service.cache_set", return_value=None):
        create_weather_model(test_data)

    log_counts = count_log_events(captured_logs, "create_weather_model")

    assert log_counts.get("INFO") == 1
    assert log_counts.get("VALIDATION_ERROR") == 1
    assert not log_counts.get("SUCCESS")
