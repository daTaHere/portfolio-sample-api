# Created a Redis client for caching and session management.
from redis import Redis, ConnectionError, TimeoutError
from app.utils.logger_helper import handle_log


redis_client: Redis | None = None  # global client


def init_redis(app):
    """
    Initialize Redis client (lazy connection).
    Does NOT attempt to connect immediately.
    """
    global redis_client
    try:
        redis_client = Redis(
            host=app.config["REDIS_HOST"],
            port=app.config["REDIS_PORT"],
            db=app.config["REDIS_DB"],
            decode_responses=True,
            socket_connect_timeout=app.config.get("REDIS_SOCKET_CONNECT_TIMEOUT", 0.2),
            socket_timeout=app.config.get("REDIS_SOCKET_TIMEOUT", 0.8),
            retry_on_timeout=False,  # fail fast
            health_check_interval=0,  # optional, prevents background pings
        )
        # Do NOT call ping() or any command here — this is lazy
        handle_log(
            "Redis client initialized (lazy connection)",
            log_level="info",
            event_key="REDIS_INIT",
            service_method="init_redis",
        )
    except Exception as e:
        # Defensive catch — should never happen during lazy init
        handle_log(
            f"Unexpected error initializing Redis client: {e}",
            log_level="error",
            event_key="ERROR",
            service_method="init_redis",
        )


# redis_client = None


# def init_redis(app):
#     try:
#         global redis_client
#         redis_client = Redis(
#             host=app.config["REDIS_HOST"],
#             port=app.config["REDIS_PORT"],
#             db=app.config["REDIS_DB"],
#             socket_connect_timeout=app.config["REDIS_SOCKET_CONNECT_TIMEOUT"],
#             socket_timeout=app.config["REDIS_SOCKET_TIMEOUT"],
#             decode_responses=True,
#         )
#     except (ConnectionError, TimeoutError) as e:
#         handle_log(
#             f"Failed to connect to Redis: {e}",
#             log_level="error",
#             event_key="ERROR",
#             service_name="init_redis",
#         )
