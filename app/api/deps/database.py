from collections.abc import Generator

from pymongo.database import Database
from sqlalchemy.orm import Session

from app.core.database import get_db as _get_db
from app.core.mongodb import mongo_db_dependency as _get_mongo_db

__all__ = ["get_db", "get_mongo_db"]


def get_db() -> Generator[Session, None, None]:
    yield from _get_db()


def get_mongo_db() -> Generator[Database, None, None]:
    yield from _get_mongo_db()
