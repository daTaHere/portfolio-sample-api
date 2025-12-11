# tests/services/test_cache_service.py
import time
import pytest
from redis import Redis
from app.services import cache_service


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


def test_cache_set_and_get(patch_redis_client):
    key = "test:key"
    value = {"foo": "bar"}

    # Set and get
    cache_service.cache_set(key, value, ttl=30)
    cached = cache_service.cache_get(key)
    assert cached == value  # Cache get should return the value just set


def test_cache_miss_returns_none(patch_redis_client):
    key = "nonexistent:key"
    cached = cache_service.cache_get(key)
    assert cached is None  # Cache miss should return None


def test_cache_overwrite(patch_redis_client):
    key = "test:key"
    cache_service.cache_set(key, {"foo": "bar"}, ttl=30)
    # overwrite with new value
    cache_service.cache_set(key, {"foo": "baz"}, ttl=30)
    cached = cache_service.cache_get(key)
    assert cached == {"foo": "baz"}  # Cache should overwrite previous value


def test_cache_ttl_expiration(patch_redis_client):
    key = "temp:key"
    value = {"expire": True}
    cache_service.cache_set(key, value, ttl=1)  # 1 second TTL
    cached = cache_service.cache_get(key)
    assert cached == value  # Cache should return value immediately after set
    time.sleep(1.2)
    cached = cache_service.cache_get(key)
    assert cached is None  # Cache should expire after TTL


def test_cache_delete(patch_redis_client):
    key = "delete:key"
    value = {"foo": "bar"}
    cache_service.cache_set(key, value, ttl=30)
    cache_service.cache_delete(key)
    cached = cache_service.cache_get(key)
    assert cached is None  # Deleted key should no longer exist in cache
