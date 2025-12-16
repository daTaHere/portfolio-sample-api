"""Cache management functions using Redis."""

import json
from typing import Dict, List
from redis.exceptions import ConnectionError, TimeoutError, DataError
from app.clients.redis_client import redis_client

from app.exceptions.base import APIException, ServiceException
from app.exceptions.exception_handlers import handle_service_error
from app.utils.logger_helper import handle_log, debug_logger

cache_logger = debug_logger("cache_service")


def cache_set(key: str, value: dict, ttl: int = 10) -> None:
    """
    Set a cache value in Redis with a specified TTL (time-to-live) in seconds.
    """
    handle_log(
        f"Setting cache for key: {key}",
        method="POST",
        event_key="CACHE_SET",
        log_level="debug",
        service_method="cache_set",
        key=key,
    )
    try:
        redis_client.set(key, json.dumps(value), ex=ttl)
        handle_log(
            f"Cache set successfully for key: {key}",
            method="POST",
            event_key="SUCCESS",
            log_level="info",
            service_method="cache_set",
            key=key,
        )
    except (TypeError, ValueError) as e:
        handle_service_error(
            exc=e,
            exc_message="Failed to serialize value: TypeError or ValueError",
            log_message="Serialization error in cache_set",
            exc_type=ServiceException,
            service_method="cache_set",
            method="POST",
        )
    except DataError as e:
        handle_service_error(
            exc=e,
            exc_message="Failed to set cache: DataError",
            log_message="Data error in cache_set",
            exc_type=ServiceException,
            service_method="cache_set",
            method="POST",
        )
    except (ConnectionError, TimeoutError) as e:
        handle_service_error(
            exc=e,
            exc_message="Cache service is unreachable",
            log_message="Connection error in cache_set",
            exc_type=APIException,
            service_method="cache_set",
            method="POST",
        )


def cache_get(key: str) -> Dict | None:
    """
    Retrieve a cache value from Redis by key.
    """
    handle_log(
        f"Retrieving cache for key: {key}",
        method="GET",
        event_key="CACHE_GET",
        log_level="debug",
        service_method="cache_get",
        key=key,
    )
    data = None
    try:
        is_cached = redis_client.get(key)
        if is_cached:
            data = json.loads(is_cached)
            handle_log(
                f"Cache retrieved successfully for key: {key}",
                method="GET",
                event_key="SUCCESS",
                log_level="info",
                service_method="cache_get",
                key=key,
            )
    except DataError as e:
        handle_service_error(
            exc=e,
            exc_message="Failed to get cache: DataError",
            log_message="Data error in cache_get",
            exc_type=ServiceException,
            service_method="cache_get",
            method="GET",
        )
    except (json.JSONDecodeError, TypeError) as e:
        handle_service_error(
            exc=e,
            exc_message="Failed to deserialize value",
            log_message="Deserialization error in cache_get",
            exc_type=ServiceException,
            service_method="cache_get",
            method="GET",
        )
    except (ConnectionError, TimeoutError) as e:
        handle_service_error(
            exc=e,
            exc_message="Cache service is unreachable",
            log_message="Connection error in cache_get",
            exc_type=APIException,
            service_method="cache_get",
            method="GET",
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
        log_level="debug",
        service_method="cache_delete",
        key=key,
    )
    try:
        is_deleted = redis_client.delete(key)
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
    except AttributeError as e:
        handle_service_error(
            exc=e,
            exc_message="Failed to delete cache: AttributeError",
            log_message="Attribute error in cache_delete",
            exc_type=APIException,
            service_method="cache_delete",
            method="DELETE",
        )
    except DataError as e:
        handle_service_error(
            exc=e,
            exc_message="Failed to delete cache: DataError",
            log_message="Data error in cache_delete",
            exc_type=ServiceException,
            service_method="cache_delete",
            method="DELETE",
        )
    except (ConnectionError, TimeoutError) as e:
        handle_service_error(
            exc=e,
            exc_message="Cache service is unreachable: ConnectionError or TimeoutError",
            log_message="Connection error in cache_delete",
            exc_type=APIException,
            service_method="cache_delete",
            method="DELETE",
        )
    return is_deleted
