"""Cache management functions using Redis."""

import json
from typing import Dict
from app.clients.redis_client import redis_client

from app.utils.logger_helper import handle_log, debug_logger
from concurrent.futures import ThreadPoolExecutor


cache_logger = debug_logger("cache_service")
executor = ThreadPoolExecutor(max_workers=5)
CACHE_TIMEOUT_SEC = 0.5  # seconds


def cache_set(key: str, value: dict, ttl: int = 10) -> None:
    """
    Set a cache value in Redis with a specified TTL (time-to-live) in seconds.
    """
    handle_log(
        f"Setting cache for key: {key}",
        method="POST",
        event_key="CACHE_SET",
        log_level="info",
        service_method="cache_set",
        key=key,
    )

    if not redis_client or not key:
        handle_log(
            "Failed to set cache: Redis client or key is None",
            method="POST",
            event_key="ERROR",
            log_level="error",
            service_method="cache_set",
            key=key,
            redis_client=redis_client,
        )
        return

    try:

        future = executor.submit(redis_client.set, key, json.dumps(value), ex=ttl)
        future.result(timeout=CACHE_TIMEOUT_SEC)

        handle_log(
            f"Cache set successfully for key: {key}",
            method="POST",
            event_key="SUCCESS",
            log_level="info",
            service_method="cache_set",
            key=key,
        )
    except Exception as e:
        handle_log(
            f"Unable to set cache for key: {key}",
            method="POST",
            event_key="ERROR",
            log_level="error",
            service_method="cache_set",
            key=key,
            exception=repr(e),
        )


def cache_get(key: str) -> Dict | None:
    """
    Retrieve a cache value from Redis by key.
    """
    handle_log(
        f"Retrieving cache for key: {key}",
        method="GET",
        event_key="CACHE_GET",
        log_level="info",
        service_method="cache_get",
        key=key,
    )

    if not redis_client or not key:
        handle_log(
            "Failed to get cache: Redis client or key is None",
            method="GET",
            event_key="ERROR",
            log_level="error",
            service_method="cache_get",
            key=key,
            redis_client=redis_client,
        )
        return None

    data = None
    try:
        future = executor.submit(redis_client.get, key)
        is_cached = future.result(timeout=CACHE_TIMEOUT_SEC)

        if is_cached:
            data = json.loads(is_cached)
        handle_log(
            f"Cache retrieved successfully for key: {key}",
            method="GET",
            event_key="SUCCESS",
            log_level="info",
            service_method="cache_get",
            key=key,
            items=len(data) if data else 0,
        )

    except Exception as e:
        handle_log(
            f"Unable to fetch cache for key: {key}",
            method="GET",
            event_key="ERROR",
            log_level="error",
            service_method="cache_get",
            key=key,
            exception=repr(e),
        )

    return data


def cache_delete(key: str) -> int:
    """
    Delete a cache value from Redis by key.
    """
    handle_log(
        "Attempting to delete cache",
        method="DELETE",
        event_key="CACHE_DELETE",
        log_level="info",
        service_method="cache_delete",
        key=key,
    )

    is_deleted = 0

    if not redis_client or not key:
        handle_log(
            "Failed to delete cache: Redis client or key is None",
            method="DELETE",
            event_key="ERROR",
            log_level="error",
            service_method="cache_delete",
            key=key,
            redis_client=redis_client,
        )
        return is_deleted

    try:
        future = executor.submit(redis_client.delete, key)
        is_deleted = future.result(timeout=CACHE_TIMEOUT_SEC)
        handle_log(
            (
                f"Cache deleted successfully for key: {key}"
                if is_deleted > 0
                else f"Cache not found for key: {key}"
            ),
            method="DELETE",
            event_key="SUCCESS",
            log_level="info",
            service_method="cache_delete",
            key=key,
        )

    except Exception as e:
        handle_log(
            f"Unable to delete cache for key: {key}",
            method="DELETE",
            event_key="ERROR",
            log_level="error",
            service_method="cache_delete",
            key=key,
            exception=repr(e),
        )

    return is_deleted
