"""
Comprehensive unit tests for the get_current_weather service.
Covers:
- Successful request with and without query parameters.
- Handling cache hits, partial cache misses, and full cache misses.
- Correct exception raising for internal and validation errors.
- Asynchronous HTTP request mocking with respx.
"""

import pytest
from unittest.mock import patch
from marshmallow import ValidationError

from app.services.weather.weather_service import get_current_weather
from app.services.weather import weather_service
from app.exceptions.service import ServiceInternalException, ServiceValidationException
from tests.utils import count_log_events

# Sample coordinates for testing
TEST_COORDS = [40.7128, -74.0060]
# Mock return values
MOCK_CANONICALIZED_RESULTS = [(40.712, -74.006), (34.05, -118.24)]
MOCK_MISSING_COORDS_LIST = [(1, (34.05, -118.24))]
MOCK_CACHE_RESULTS = [{"name": "NYC", "temp": 20}]
MOCK_MISSING_RESULTS = [{"name": "LA", "temp": 25}]
MOCK_FETCHED_RESULTS = [{"name": "NYC", "temp": 20}, {"name": "LA", "temp": 25}]

MOCK_FETCHED_RESULTSV2 = []


@pytest.fixture
def mock_create_fetch_list():
    with patch("app.services.weather.weather_service.create_fetch_list") as mock:
        yield mock


@pytest.fixture
def mock_process_from_cache():
    with patch("app.services.weather.weather_service.process_from_cache") as mock:
        yield mock


@pytest.fixture
def mock_fetch_all():
    with patch("app.services.weather.weather_service.fetch_all") as mock:
        yield mock


@pytest.fixture
def mock_fetch_cache_missed():
    with patch("app.services.weather.weather_service.fetch_cache_missed") as mock:
        yield mock


@pytest.fixture
def mock_create_weather_model():
    with patch("app.services.weather.weather_service.create_weather_model") as mock:
        yield mock


# @pytest.fixture
# def mock_WeatherSchema():
#     with patch("app.services.weather.weather_service.WeatherSchema") as mock:
#         yield mock


# -------------------------------------------------
#     get_current_weather success path tests
# -------------------------------------------------
@pytest.mark.asyncio
async def test_get_current_weather_success_hit_all(
    mock_create_fetch_list, mock_process_from_cache, captured_logs
):
    mock_create_fetch_list.return_value = [MOCK_CANONICALIZED_RESULTS[0]]
    mock_process_from_cache.return_value = ([MOCK_CACHE_RESULTS], [])

    results = await get_current_weather(TEST_COORDS)
    log_counts = count_log_events(captured_logs, "get_current_weather")

    mock_create_fetch_list.assert_called_once_with(MOCK_CANONICALIZED_RESULTS[0])
    mock_process_from_cache.assert_called_once_with([MOCK_CANONICALIZED_RESULTS[0]])
    assert results[0] == MOCK_CACHE_RESULTS
    assert log_counts["GET_WEATHER"] == 1
    assert not log_counts["ERROR"]
    assert log_counts["HIT_ALL_CACHE"] == 1
    assert not log_counts["MISSED_ALL_CACHE"]
    assert not log_counts["PARTIAL_CACHE_MISSED"]
    assert not log_counts["ERROR"]
    assert not log_counts["SUCCESS"]


@pytest.mark.asyncio
async def test_get_current_weather_success_no_query_params(
    mock_create_fetch_list, mock_process_from_cache, captured_logs
):
    mock_create_fetch_list.return_value = [MOCK_CANONICALIZED_RESULTS[0]]
    mock_process_from_cache.return_value = ([MOCK_CACHE_RESULTS], [])

    with patch(
        "app.services.weather.weather_service.canonicalize_coords"
    ) as mock_canonicalize:
        results = await get_current_weather(None)
    log_counts = count_log_events(captured_logs, "get_current_weather")

    mock_canonicalize.assert_not_called()
    mock_create_fetch_list.assert_called_once_with(None)
    mock_process_from_cache.assert_called_once_with([MOCK_CANONICALIZED_RESULTS[0]])
    assert results[0] == MOCK_CACHE_RESULTS
    assert log_counts["GET_WEATHER"] == 1
    assert log_counts["HIT_ALL_CACHE"] == 1
    assert not log_counts["MISSED_ALL_CACHE"]
    assert not log_counts["PARTIAL_CACHE_MISSED"]
    assert not log_counts["ERROR"]
    assert not log_counts["SUCCESS"]


@pytest.mark.asyncio
async def test_get_current_weather_success_missed_all(
    monkeypatch,
    mock_create_fetch_list,
    mock_process_from_cache,
    mock_fetch_all,
    mock_create_weather_model,
    captured_logs,
):
    mock_create_fetch_list.return_value = [MOCK_CANONICALIZED_RESULTS[0]]
    mock_process_from_cache.return_value = (
        [None],
        MOCK_MISSING_COORDS_LIST,
    )
    mock_fetch_all.return_value = MOCK_MISSING_RESULTS
    mock_create_weather_model.side_effect = lambda x: x
    monkeypatch.setattr(
        weather_service.WeatherSchema,
        "dump",
        lambda self, x: MOCK_MISSING_RESULTS,
    )
    results = await get_current_weather(TEST_COORDS)
    log_counts = count_log_events(captured_logs, "get_current_weather")

    mock_create_fetch_list.assert_called_once_with(MOCK_CANONICALIZED_RESULTS[0])
    mock_process_from_cache.assert_called_once_with([MOCK_CANONICALIZED_RESULTS[0]])
    mock_create_weather_model.assert_called_once_with(MOCK_MISSING_RESULTS)
    assert results == MOCK_MISSING_RESULTS
    assert log_counts["GET_WEATHER"] == 1
    assert not log_counts["HIT_ALL_CACHE"]
    assert log_counts["MISSED_ALL_CACHE"] == 1
    assert not log_counts["PARTIAL_CACHE_MISSED"]
    assert not log_counts["ERROR"]
    assert log_counts["SUCCESS"] == 1


@pytest.mark.asyncio
async def test_get_current_weather_success_partial_cache(
    monkeypatch,
    mock_create_fetch_list,
    mock_process_from_cache,
    mock_fetch_cache_missed,
    captured_logs,
):
    mock_create_fetch_list.return_value = MOCK_CANONICALIZED_RESULTS
    mock_process_from_cache.return_value = (
        [MOCK_CACHE_RESULTS[0], None],
        MOCK_MISSING_COORDS_LIST,
    )
    mock_fetch_cache_missed.return_value = MOCK_MISSING_RESULTS
    monkeypatch.setattr(
        weather_service.WeatherSchema,
        "dump",
        lambda self, x: MOCK_FETCHED_RESULTS,
    )
    results = await get_current_weather(TEST_COORDS)
    log_counts = count_log_events(captured_logs, "get_current_weather")

    mock_create_fetch_list.assert_called_once_with(MOCK_CANONICALIZED_RESULTS[0])
    mock_process_from_cache.assert_called_once_with(MOCK_CANONICALIZED_RESULTS)
    mock_fetch_cache_missed.assert_called_once()
    assert results == MOCK_FETCHED_RESULTS
    assert log_counts["GET_WEATHER"] == 1
    assert not log_counts["HIT_ALL_CACHE"]
    assert not log_counts["MISSED_ALL_CACHE"]
    assert log_counts["PARTIAL_CACHE_MISSED"] == 1
    assert not log_counts["ERROR"]
    assert log_counts["SUCCESS"] == 1


# ---------------------------------------------------------------
#     get_current_weather raise validation exception tests
# ---------------------------------------------------------------
@pytest.mark.parametrize(
    "exception",
    [ValidationError("invalid data"), AttributeError("missing attribute")],
)
@pytest.mark.asyncio
async def test_get_current_weather_raise_ServiceValidationException(
    monkeypatch,
    mock_fetch_all,
    mock_create_fetch_list,
    mock_process_from_cache,
    mock_create_weather_model,
    captured_logs,
    exception: Exception,
):
    mock_create_fetch_list.return_value = [MOCK_CANONICALIZED_RESULTS[0]]
    mock_process_from_cache.return_value = (
        [None],
        MOCK_MISSING_COORDS_LIST,
    )
    mock_fetch_all.return_value = MOCK_MISSING_RESULTS
    mock_create_weather_model.side_effect = lambda x: x
    monkeypatch.setattr(
        weather_service.WeatherSchema,
        "dump",
        lambda self, x: (_ for _ in ()).throw(exception),
    )
    with pytest.raises(ServiceValidationException) as exc_info:
        await get_current_weather(TEST_COORDS)
    log_counts = count_log_events(captured_logs, "get_current_weather")

    mock_create_fetch_list.assert_called_once_with(MOCK_CANONICALIZED_RESULTS[0])
    mock_process_from_cache.assert_called_once_with([MOCK_CANONICALIZED_RESULTS[0]])
    mock_create_weather_model.assert_called_once_with(MOCK_MISSING_RESULTS)
    assert log_counts["GET_WEATHER"] == 1
    assert not log_counts["HIT_ALL_CACHE"]
    assert log_counts["MISSED_ALL_CACHE"] == 1
    assert not log_counts["PARTIAL_CACHE_MISSED"]
    assert log_counts["ERROR"] == 1
    assert not log_counts["SUCCESS"]
    assert "Validation Error:" in str(exc_info.value)


# ---------------------------------------------------------------
#     get_current_weather raise internal exception tests
# ---------------------------------------------------------------
@pytest.mark.parametrize(
    "exception",
    [TypeError("invalid type"), ValueError("invalid value"), KeyError("missing key")],
)
@pytest.mark.asyncio
async def test_get_current_weather_raise_ServiceInternalException(
    mock_fetch_all,
    mock_create_fetch_list,
    mock_process_from_cache,
    mock_create_weather_model,
    captured_logs,
    exception: Exception,
):
    mock_create_fetch_list.return_value = [MOCK_CANONICALIZED_RESULTS[0]]
    mock_process_from_cache.return_value = (
        [None],
        MOCK_MISSING_COORDS_LIST,
    )
    mock_fetch_all.return_value = MOCK_MISSING_RESULTS
    mock_create_weather_model.side_effect = exception
    with pytest.raises(ServiceInternalException) as exc_info:
        await get_current_weather(TEST_COORDS)
    log_counts = count_log_events(captured_logs, "get_current_weather")

    mock_create_fetch_list.assert_called_once_with(MOCK_CANONICALIZED_RESULTS[0])
    mock_process_from_cache.assert_called_once_with([MOCK_CANONICALIZED_RESULTS[0]])
    mock_create_weather_model.assert_called_once_with(MOCK_MISSING_RESULTS)
    assert log_counts["GET_WEATHER"] == 1
    assert not log_counts["HIT_ALL_CACHE"]
    assert log_counts["MISSED_ALL_CACHE"] == 1
    assert not log_counts["PARTIAL_CACHE_MISSED"]
    assert log_counts["ERROR"] == 1
    assert not log_counts["SUCCESS"]
    assert "Internal Error:" in str(exc_info.value)
