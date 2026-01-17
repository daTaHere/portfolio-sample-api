"""
Comprehensive unit tests for request_weather related helper functions.
Tests cover:
- Successful api call counts.
- Argument passing correctness.
- Handling of cache misses.
- Logging of function events.
- Verification of returned data structures and order preservation.
"""

import pytest
from unittest.mock import patch

from app.models.weather_model import WeatherModel
from tests.services.weathers.test_mock_weather_data import (
    DEFAULT_WEATHER_CITIES,
    mock_weather_expected_data,
)
from app.services.weather.weather_fetchers import (
    fetch_all,
    fetch_cache_missed,
    fetch_with_index,
)
from tests.utils import count_log_events


# Mock coordinates for testing cache misses
TEST_MISSING_COORDS = [
    (0, (42.35, -71.05)),
    (2, (40.71, -74.0)),
    (4, (25.76, -80.19)),
]

TEST_CACHE_LIST = [
    None,
    WeatherModel(mock_weather_expected_data("New York")),
    None,
    WeatherModel(mock_weather_expected_data("Houston")),
    None,
    WeatherModel(mock_weather_expected_data("London")),
]

TEST_MOCKED_SIDE_EFFECTS = [
    (
        0,
        mock_weather_expected_data(
            "Los Angeles",
            lat=TEST_MISSING_COORDS[0][1][0],
            lon=TEST_MISSING_COORDS[0][1][1],
        ),
    ),
    (
        2,
        mock_weather_expected_data(
            "Chicago",
            lat=TEST_MISSING_COORDS[1][1][0],
            lon=TEST_MISSING_COORDS[1][1][1],
        ),
    ),
    (
        4,
        mock_weather_expected_data(
            "Miami",
            lat=TEST_MISSING_COORDS[2][1][0],
            lon=TEST_MISSING_COORDS[2][1][1],
        ),
    ),
]

TEST_EXPECTED_RESULTS = [
    mock_weather_expected_data(
        "Los Angeles",
        lat=TEST_MISSING_COORDS[0][1][0],
        lon=TEST_MISSING_COORDS[0][1][1],
    ),
    mock_weather_expected_data("New York"),
    mock_weather_expected_data(
        "Chicago", lat=TEST_MISSING_COORDS[1][1][0], lon=TEST_MISSING_COORDS[1][1][1]
    ),
    mock_weather_expected_data("Houston"),
    mock_weather_expected_data(
        "Miami", lat=TEST_MISSING_COORDS[2][1][0], lon=TEST_MISSING_COORDS[2][1][1]
    ),
    mock_weather_expected_data("London"),
]


@pytest.fixture
def mock_request_weather():
    with patch("app.services.weather.weather_fetchers.request_weather") as mock_request:
        yield mock_request


@pytest.mark.asyncio
async def test_fetch_all_success(
    captured_logs,
    mock_request_weather,
):
    results = await fetch_all(DEFAULT_WEATHER_CITIES)
    actual_args = [c.args for c in mock_request_weather.call_args_list]

    log_counts = count_log_events(captured_logs, "fetch_all")

    assert mock_request_weather.call_count == len(DEFAULT_WEATHER_CITIES)
    assert actual_args == DEFAULT_WEATHER_CITIES
    assert len(results) == len(DEFAULT_WEATHER_CITIES)
    assert log_counts.get("FETCH_ALL") == 1


@pytest.mark.asyncio
async def test_fetch_all_successV2(
    captured_logs,
    mock_request_weather,
):
    results = await fetch_all(DEFAULT_WEATHER_CITIES)
    actual_args = [c.args for c in mock_request_weather.call_args_list]

    log_counts = count_log_events(captured_logs, "fetch_all")

    assert mock_request_weather.call_count == len(DEFAULT_WEATHER_CITIES)
    assert actual_args == DEFAULT_WEATHER_CITIES
    assert len(results) == len(DEFAULT_WEATHER_CITIES)
    assert log_counts.get("FETCH_ALL") == 1


@pytest.mark.parametrize(
    "mock_index, mock_lat, mock_lon",
    [
        [2, 40.71, -74.0],
        [5, 29.76, -95.36],
        [8, 35.68, 139.69],
    ],
)
@pytest.mark.asyncio
async def test_fetch_with_index_success(
    captured_logs,
    mock_request_weather,
    mock_index: int,
    mock_lat: float,
    mock_lon: float,
):
    mock_request_weather.return_value = {"test": "weather_data"}
    results = await fetch_with_index(mock_index, mock_lat, mock_lon)

    log_counts = count_log_events(captured_logs, "fetch_with_index")

    mock_request_weather.assert_called_once()
    assert mock_request_weather.call_args[0] == (mock_lat, mock_lon)
    assert isinstance(results, tuple)
    assert results == (mock_index, {"test": "weather_data"})
    assert log_counts.get("FETCH_WITH_INDEX") == 1


@pytest.mark.asyncio
async def test_fetch_cache_missed_success(
    captured_logs,
):
    missed_coords = TEST_MISSING_COORDS
    cached_list = TEST_CACHE_LIST.copy()
    mock_side_effects = TEST_MOCKED_SIDE_EFFECTS

    with patch(
        "app.services.weather.weather_fetchers.fetch_with_index",
        side_effect=mock_side_effects,
    ) as mock_fetch_with_index:
        results = await fetch_cache_missed(missed_coords, cached_list)

    log_counts = count_log_events(captured_logs, "fetch_cache_missed")

    assert mock_fetch_with_index.call_count == len(missed_coords)
    assert all(isinstance(res, WeatherModel) for res in results)
    assert (
        results[0].name == "Los Angeles"
        and results[0].coord["lat"] == 42.35
        and results[0].coord["lon"] == -71.05
    )
    assert (
        results[2].name == "Chicago"
        and results[2].coord["lat"] == 40.71
        and results[2].coord["lon"] == -74.0
    )
    assert (
        results[4].name == "Miami"
        and results[4].coord["lat"] == 25.76
        and results[4].coord["lon"] == -80.19
    )
    assert log_counts.get("INFO") == 1
    assert log_counts.get("SUCCESS") == 1
