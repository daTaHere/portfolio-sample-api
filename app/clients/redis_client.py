# Created a Redis client for caching and session management.
from redis import Redis, ConnectionError, TimeoutError
from app.utils.logger_helper import handle_log

redis_client = None


def init_redis(app):
    try:
        global redis_client
        redis_client = Redis(
            host=app.config["REDIS_HOST"],
            port=app.config["REDIS_PORT"],
            db=app.config["REDIS_DB"],
            decode_responses=True,
        )
    except (ConnectionError, TimeoutError) as e:
        handle_log(
            f"Failed to connect to Redis: {e}",
            log_level="error",
            event_key="ERROR",
            service_name="init_redis",
        )
        redis_client = None
