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

from app.services.weather.weather_fetchers import (
    fetch_all,
    fetch_cache_missed,
    fetch_with_index,
)

from tests.utils import count_log_events

DEFAULT_COORDS_LIST = [
    (42.35, -71.05),
    (34.05, -118.24),
    (40.71, -74.0),
    (41.87, -87.62),
    (29.76, -95.36),
    (25.76, -80.19),
    (51.51, -0.13),
    (35.68, 139.69),
    (39.9, 116.4),
    (30.03, 31.23),
]

# Mock coordinates for testing cache misses
TEST_MISSING_COORDS = [
    (0, (42.35, -71.05)),
    (2, (40.71, -74.0)),
    (4, (29.76, -95.36)),
]

TEST_CACHE_LIST = [
    {},
    {"mocked_1": "data"},
    {},
    {"mocked_3": "data"},
    {},
    {"mocked_5": "data"},
]

TEST_MOCKED_SIDE_EFFECTS = [
    (0, {"mocked_0": "data"}),
    (2, {"mocked_2": "data"}),
    (4, {"mocked_4": "data"}),
]

TEST_EXPECTED_RESULTS = [
    {"mocked_0": "data"},
    {"mocked_1": "data"},
    {"mocked_2": "data"},
    {"mocked_3": "data"},
    {"mocked_4": "data"},
    {"mocked_5": "data"},
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
    results = await fetch_all(DEFAULT_COORDS_LIST)
    actual_args = [c.args for c in mock_request_weather.call_args_list]

    log_counts = count_log_events(captured_logs, "fetch_all")

    assert mock_request_weather.call_count == len(DEFAULT_COORDS_LIST)
    assert actual_args == DEFAULT_COORDS_LIST
    assert len(results) == len(DEFAULT_COORDS_LIST)
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
    assert results == TEST_EXPECTED_RESULTS
    assert log_counts.get("INFO") == 1
    assert log_counts.get("SUCCESS") == 1
