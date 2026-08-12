from functools import lru_cache

import redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import engine
from app.core.mongodb import check_mongodb

__all__ = ["check_database", "check_mongodb", "check_redis", "get_redis_client"]


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


def check_database() -> dict:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}
    except SQLAlchemyError as exc:
        return {"status": "error", "detail": str(exc)}
