from types import SimpleNamespace

from unittest.mock import AsyncMock, patch
import pytest

from app.tasks.weather_tasks import fetch_weather_updates_async
from tests.utils import count_log_events


TEST_CACHE_HIT_COORDS = [(1.0, -1.0), (2.0, -2.0)]
TEST_CACHE_MISS_COORDS = [(5.0, -5.0), (8.0, -8.0)]

MOCK_CACHE_HIT_REPSONSE = [
    SimpleNamespace(name="CityA"),
    SimpleNamespace(name="CityB"),
]

MOCK_CACHE_MISS_RESPONSE = [
    SimpleNamespace(name="CityC"),
    SimpleNamespace(name="CityD"),
]


@pytest.fixture(autouse=True)
def mock_default_cities(monkeypatch):
    default_cities = TEST_CACHE_MISS_COORDS
    monkeypatch.setattr(
        "app.tasks.weather_tasks.DEFAULT_CITIES",
        default_cities,
    )


@pytest.fixture
def mock_cache_get():
    with patch("app.tasks.weather_tasks.cache_get") as mock:
        yield mock


@pytest.fixture
def mock_fetch_all():
    with patch("app.tasks.weather_tasks.fetch_all", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_create_weather_model():
    with patch("app.tasks.weather_tasks.create_weather_model") as mock:
        yield mock


@pytest.fixture
def mock_cache_schema_load():
    with patch("app.tasks.weather_tasks.WeatherCoordsCacheSchema.load") as mock:
        yield mock


@pytest.mark.asyncio
async def test_fetch_weather_updates_success(
    mock_cache_get,
    mock_fetch_all,
    mock_create_weather_model,
    mock_cache_schema_load,
    captured_logs,
):
    # return deserialized coords because cache_get returns already json.loads processed dict
    cached_coords = {"coords": TEST_CACHE_HIT_COORDS}

    fresh_data = MOCK_CACHE_HIT_REPSONSE

    mock_cache_get.return_value = cached_coords
    mock_cache_schema_load.side_effect = lambda x: x
    mock_fetch_all.return_value = fresh_data
    mock_create_weather_model.side_effect = lambda x: x
    await fetch_weather_updates_async()

    log_count = count_log_events(captured_logs, "fetch_weather_updates")

    logged_fetch_cities = set(
        [
            log["extra"]["cities"]
            for log in captured_logs
            if log["extra"]["event_key"] == "SUCCESS"
        ][0]
    )

    mock_cache_get.assert_called_once_with("weather_coords_list")
    mock_cache_schema_load.assert_called_once()
    mock_fetch_all.assert_awaited_with(TEST_CACHE_HIT_COORDS)
    mock_create_weather_model.assert_called_once_with(fresh_data)
    assert log_count["REFRESH_CITIES"] == 1
    assert log_count["SUCCESS"] == 1
    assert not log_count["ERROR_COORDS_CACHE"]
    assert not log_count["ERROR_FETCH_WEATHER"]
    assert logged_fetch_cities == {"CityA", "CityB"}


@pytest.mark.asyncio
async def test_fetch_weather_updates_cache_miss(
    mock_cache_get,
    mock_fetch_all,
    mock_create_weather_model,
    mock_cache_schema_load,
    captured_logs,
):
    cached_coords = None

    mock_cache_get.return_value = cached_coords
    mock_fetch_all.return_value = MOCK_CACHE_MISS_RESPONSE
    mock_create_weather_model.side_effect = lambda x: x
    await fetch_weather_updates_async()

    log_count = count_log_events(captured_logs, "fetch_weather_updates")
    logged_fetch_cities = set(
        [
            log["extra"]["cities"]
            for log in captured_logs
            if log["extra"].get("event_key") == "SUCCESS"
        ][0]
    )

    mock_cache_get.assert_called_once_with("weather_coords_list")
    mock_cache_schema_load.assert_not_called()
    mock_fetch_all.assert_awaited_once_with(TEST_CACHE_MISS_COORDS)
    mock_create_weather_model.assert_called_once_with(MOCK_CACHE_MISS_RESPONSE)
    assert log_count["REFRESH_CITIES"] == 1
    assert log_count["SUCCESS"] == 1
    assert not log_count["ERROR"]
    assert logged_fetch_cities == {"CityC", "CityD"}


@pytest.mark.asyncio
async def test_fetch_weather_updates_redis_exception_log_error(
    mock_cache_get,
    mock_fetch_all,
    mock_create_weather_model,
    mock_cache_schema_load,
    captured_logs,
):

    mock_cache_get.side_effect = Exception("Error getting from cache")
    await fetch_weather_updates_async()

    log_count = count_log_events(captured_logs, "fetch_weather_updates")

    mock_cache_get.assert_called_once_with("weather_coords_list")
    mock_cache_schema_load.assert_not_called()
    mock_fetch_all.assert_not_called()
    mock_create_weather_model.assert_not_called()
    assert log_count["REFRESH_CITIES"] == 1
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"] == 1


@pytest.mark.asyncio
async def test_fetch_weather_updates_cache_set_exception_log_error(
    mock_cache_get,
    mock_fetch_all,
    mock_create_weather_model,
    mock_cache_schema_load,
    captured_logs,
):

    mock_cache_get.side_effect = Exception("Error getting from cache")

    await fetch_weather_updates_async()

    log_count = count_log_events(captured_logs, "fetch_weather_updates")

    mock_cache_get.assert_called_once_with("weather_coords_list")
    mock_cache_schema_load.assert_not_called()
    mock_fetch_all.assert_not_called()
    mock_create_weather_model.assert_not_called()
    assert log_count["REFRESH_CITIES"] == 1
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"] == 1


@pytest.mark.asyncio
async def test_fetch_weather_updates_schema_validation_exception_log_error(
    mock_cache_get,
    mock_fetch_all,
    mock_create_weather_model,
    mock_cache_schema_load,
    captured_logs,
):

    mock_cache_get.return_value = TEST_CACHE_HIT_COORDS
    mock_cache_schema_load.side_effect = Exception("Error validating cache schema")

    await fetch_weather_updates_async()

    log_count = count_log_events(captured_logs, "fetch_weather_updates")

    mock_cache_get.assert_called_once_with("weather_coords_list")
    mock_cache_schema_load.assert_called_once_with(TEST_CACHE_HIT_COORDS)
    mock_fetch_all.assert_not_called()
    mock_create_weather_model.assert_not_called()
    assert log_count["REFRESH_CITIES"] == 1
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"] == 1


@pytest.mark.asyncio
async def test_fetch_weather_updates_fetch_all_exception_log_error(
    mock_cache_get,
    mock_fetch_all,
    mock_create_weather_model,
    mock_cache_schema_load,
    captured_logs,
):
    cached_coords = {"coords": TEST_CACHE_HIT_COORDS}

    mock_cache_get.return_value = cached_coords
    mock_cache_schema_load.side_effect = lambda x: x
    mock_fetch_all.side_effect = Exception("Error fetching from API")

    await fetch_weather_updates_async()

    log_count = count_log_events(captured_logs, "fetch_weather_updates")

    mock_cache_get.assert_called_once_with("weather_coords_list")
    mock_cache_schema_load.assert_called_once_with(cached_coords)
    mock_fetch_all.assert_awaited_once_with(TEST_CACHE_HIT_COORDS)
    mock_create_weather_model.assert_not_called()
    assert log_count["REFRESH_CITIES"] == 1
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"] == 1
