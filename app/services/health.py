from functools import lru_cache

import redis
from redis.exceptions import RedisError

from app.core.config import settings


@lru_cache
def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def check_redis() -> dict:
    try:
        client = get_redis_client()
        client.ping()
        return {"status": "ok"}
    except RedisError as exc:
        return {"status": "error", "detail": str(exc)}
