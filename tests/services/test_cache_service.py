# tests/services/test_cache_service.py
import time
import pytest

from json import JSONDecodeError
from typing import Any
from redis import Redis, ConnectionError, TimeoutError, ResponseError
from unittest.mock import MagicMock, patch

from tests.utils import count_log_events
from app.services import cache_service

DEFAULT_KEY = "test:key"
DEFAULT_VALUE = {"foo": "bar"}


@pytest.fixture
def test_redis_client():
    """Create a fresh Redis client for testing."""
    client = Redis(host="localhost", port=6379, db=1, decode_responses=True)
    client.flushdb()  # start with clean slate
    yield client
    client.flushdb()
    client.close()


@pytest.fixture
def patch_redis_client(monkeypatch, test_redis_client):
    """Monkeypatch the global redis_client in cache_service with test client."""
    monkeypatch.setattr(cache_service, "redis_client", test_redis_client)
    return test_redis_client


def test_cache_set_and_get_success(patch_redis_client, captured_logs):
    key = DEFAULT_KEY
    value = DEFAULT_VALUE

    # Set and get value
    cache_service.cache_set(key, value, ttl=30)
    log_count = count_log_events(captured_logs, "cache_set")

    assert log_count["CACHE_SET"]
    assert log_count["SUCCESS"]
    assert not log_count["ERROR"]

    cached = cache_service.cache_get(key)
    log_count = count_log_events(captured_logs, "cache_get")

    assert cached == value
    assert log_count["CACHE_GET"]
    assert log_count["SUCCESS"]
    assert not log_count["ERROR"]


@pytest.mark.parametrize(
    "client,key",
    [(None, DEFAULT_KEY), (patch_redis_client, None), (patch_redis_client, "")],
)
def test_cache_set_falsy_key_or_client_log_error(captured_logs, client, key):
    value = DEFAULT_VALUE

    cache_service.cache_set(key, value, ttl=30)
    log_count = count_log_events(captured_logs, "cache_set")

    assert log_count["CACHE_SET"]
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"]


@pytest.mark.parametrize(
    "mock_error", [TypeError("forced error"), ValueError("forced error")]
)
def test_cache_set_type_and_value_exception_log_error(
    patch_redis_client, captured_logs, mock_error: Exception
):
    key = DEFAULT_KEY
    value = DEFAULT_VALUE

    # Mock json.dumps to raise TypeError or ValueError
    with patch("app.services.cache_service.json.dumps", side_effect=mock_error):
        cache_service.cache_set(key, value, ttl=30)

    log_count = count_log_events(captured_logs, "cache_set")

    assert log_count["CACHE_SET"]
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"]


def test_cache_set_client_bad_response_log_error(patch_redis_client, captured_logs):
    key = DEFAULT_KEY
    value = DEFAULT_VALUE

    # Mock Redis set response to raise connection or timeout error
    patch_redis_client.set = MagicMock(side_effect=ResponseError("Response error"))
    cache_service.cache_set(key, value, ttl=30)

    log_count = count_log_events(captured_logs, "cache_set")

    assert log_count["CACHE_SET"]
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"]


@pytest.mark.parametrize("invalid_key", [{}, [], ()])
def test_cache_get_data_invalid_key_log_error(
    patch_redis_client, captured_logs, invalid_key: Any
):

    cache_service.cache_get(invalid_key)
    log_count = count_log_events(captured_logs, "cache_get")

    assert log_count["CACHE_GET"]
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"]


@pytest.mark.parametrize(
    "client,key",
    [(None, DEFAULT_KEY), (patch_redis_client, None), (patch_redis_client, "")],
)
def test_cache_get_falsy_key_or_client_log_error(captured_logs, client, key):

    cache_service.cache_get(key)
    log_count = count_log_events(captured_logs, "cache_get")

    assert log_count["CACHE_GET"]
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"]


def test_cache_get_json_decode_error_log_error(patch_redis_client, captured_logs):
    key = DEFAULT_KEY
    patch_redis_client.get = MagicMock(return_value=DEFAULT_VALUE)

    with patch(
        "app.services.cache_service.json.loads",
        side_effect=JSONDecodeError("forced error", "", 0),
    ):
        cache_service.cache_get(key)

    log_count = count_log_events(captured_logs, "cache_get")

    assert log_count["CACHE_GET"]
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"]


def test_cache_get_response_error_log_error(patch_redis_client, captured_logs):
    key = DEFAULT_KEY

    patch_redis_client.get = MagicMock(side_effect=ResponseError("Response error"))

    cache_service.cache_get(key)

    log_count = count_log_events(captured_logs, "cache_get")

    assert log_count["CACHE_GET"]
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"]


def test_cache_miss_returns_none(patch_redis_client, captured_logs):
    key = "nonexistent:key"
    cached = cache_service.cache_get(key)
    log_count = count_log_events(captured_logs, "cache_get")

    assert cached is None
    assert log_count["CACHE_GET"]
    assert log_count["SUCCESS"]
    assert not log_count["ERROR"]


def test_cache_overwrite(patch_redis_client, captured_logs):

    key = DEFAULT_KEY
    cache_service.cache_set(key, DEFAULT_VALUE, ttl=30)
    log_set_count = count_log_events(captured_logs, "cache_set")

    # overwrite with new value
    cache_service.cache_set(key, {"foo": "baz"}, ttl=30)
    cached = cache_service.cache_get(key)

    log_get_count = count_log_events(captured_logs, "cache_get")

    assert cached == {"foo": "baz"}
    assert log_set_count["CACHE_SET"]
    assert log_set_count["SUCCESS"]
    assert not log_set_count["ERROR"]
    assert log_get_count["CACHE_GET"]
    assert log_get_count["SUCCESS"]
    assert not log_get_count["ERROR"]


@pytest.mark.parametrize("cache_age,delay_time", [(1, 1.2), (2, 2.2), (3, 3.2)])
def test_cache_ttl_expiration(
    patch_redis_client, captured_logs, cache_age: float, delay_time: float
):
    key = DEFAULT_KEY
    value = {"expire": True}
    cache_service.cache_set(key, value, ttl=cache_age)  # TTL set to cache_age
    cached = cache_service.cache_get(key)

    time.sleep(delay_time)
    not_cached = cache_service.cache_get(key)

    log_count = count_log_events(captured_logs, "cache_get")

    assert cached == value  # Cache should be available before TTL
    assert not not_cached  # Cache should expire after TTL
    assert log_count["CACHE_GET"] == 2
    assert log_count["SUCCESS"]
    assert not log_count["ERROR"]


def test_cache_delete_success(patch_redis_client, captured_logs):
    key = DEFAULT_KEY
    value = DEFAULT_VALUE

    cache_service.cache_set(key, value, ttl=30)
    is_deleted = cache_service.cache_delete(key)
    cached = cache_service.cache_get(key)

    log_count = count_log_events(captured_logs, "cache_delete")

    assert is_deleted
    assert cached is None  # Deleted key should no longer exist in cache
    assert log_count["CACHE_DELETE"]
    assert log_count["SUCCESS"] == 1
    assert not log_count["ERROR"]


@pytest.mark.parametrize(
    "client,key",
    [(None, DEFAULT_KEY), (patch_redis_client, None), (patch_redis_client, "")],
)
def test_cache_delete_falsy_key_or_client_log_error(captured_logs, client, key):

    cache_service.cache_delete(key)
    log_count = count_log_events(captured_logs, "cache_delete")
    assert log_count["CACHE_DELETE"]
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"]


def test_cache_delete_nonexistent_key_success(patch_redis_client, captured_logs):
    key = DEFAULT_KEY
    value = DEFAULT_VALUE

    cache_service.cache_set(key, value, ttl=30)
    existing_key = cache_service.cache_delete(key)
    cached = cache_service.cache_get(key)
    nonexisting_key = cache_service.cache_delete(key)

    log_count = count_log_events(captured_logs, "cache_delete")

    assert existing_key == 1
    assert nonexisting_key == 0
    assert cached is None  # Deleted key should no longer exist in cache
    assert log_count["CACHE_DELETE"]
    assert log_count["SUCCESS"] == 2
    assert not log_count["ERROR"]


def test_cache_delete_connection_and_timeout_error_raises_api_exception(
    patch_redis_client, captured_logs
):
    key = DEFAULT_KEY
    patch_redis_client.delete = MagicMock(side_effect=ResponseError("Response error"))

    cache_service.cache_delete(key)

    log_count = count_log_events(captured_logs, "cache_delete")

    assert log_count["CACHE_DELETE"]
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"]


@pytest.mark.parametrize("invalid_key", [{}, [], ()])
def test_cache_delete_data_error_raises_service_exception(
    patch_redis_client, captured_logs, invalid_key: Any
):

    cache_service.cache_delete(invalid_key)

    log_count = count_log_events(captured_logs, "cache_delete")

    assert log_count["CACHE_DELETE"]
    assert not log_count["SUCCESS"]
    assert log_count["ERROR"]
