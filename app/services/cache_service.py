import json
from app.clients.redis_client import redis_client


def cache_set(key: str, value: dict, ttl: int = 300):
    redis_client.set(key, json.dumps(value), ex=ttl)


def cache_get(key: str):
    data = redis_client.get(key)
    return json.loads(data) if data else None


def cache_delete(key: str):
    redis_client.delete(key)
