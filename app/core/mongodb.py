import json
import time
from collections.abc import Generator
from typing import Optional
from urllib.parse import urlparse

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import settings

_client: Optional[MongoClient] = None

# #region agent log
_DEBUG_LOG_PATH = "/Users/kunji/Documents/work/epiderm/epiderm-service/.cursor/debug-6557d1.log"


def _agent_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    payload = {
        "sessionId": "6557d1",
        "runId": "pre-fix",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=str) + "\n")


# #endregion


def connect_to_mongo() -> None:
    global _client
    if _client is not None:
        return
    # #region agent log
    parsed = urlparse(settings.MONGODB_URL)
    _agent_log(
        "A",
        "mongodb.py:connect_to_mongo:url",
        "Resolved MongoDB URL (sanitized)",
        {
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "port": parsed.port,
            "username": parsed.username,
            "has_password": bool(parsed.password),
            "path": parsed.path,
            "query": parsed.query,
            "db_name": settings.MONGODB_DB_NAME,
        },
    )
    # #endregion
    _client = MongoClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5_000,
    )
    # #region agent log
    try:
        server_info = _client.server_info()
        _agent_log(
            "C",
            "mongodb.py:connect_to_mongo:server_info",
            "Reached a MongoDB server before/during auth path",
            {
                "version": server_info.get("version"),
                "ok": server_info.get("ok"),
            },
        )
    except Exception as exc:
        _agent_log(
            "C",
            "mongodb.py:connect_to_mongo:server_info_error",
            "server_info failed",
            {"error_type": type(exc).__name__, "error": str(exc)},
        )
    # #endregion
    try:
        # Fail fast if MongoDB is unreachable at startup.
        _client.admin.command("ping")
        # #region agent log
        _agent_log(
            "B",
            "mongodb.py:connect_to_mongo:ping_ok",
            "Authenticated ping succeeded",
            {"auth_source_query": parsed.query},
        )
        # #endregion
    except Exception as exc:
        # #region agent log
        _agent_log(
            "B",
            "mongodb.py:connect_to_mongo:ping_error",
            "Authenticated ping failed",
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
                "code": getattr(exc, "code", None),
                "details": getattr(exc, "details", None),
            },
        )
        # Probe whether unauthenticated localhost mongod accepts connections
        try:
            bare = MongoClient(
                "mongodb://localhost:27017/",
                serverSelectionTimeoutMS=2_000,
            )
            bare_info = bare.admin.command("ping")
            bare.close()
            _agent_log(
                "D",
                "mongodb.py:connect_to_mongo:bare_ping",
                "Unauthenticated localhost ping result",
                {"ok": bare_info.get("ok"), "reachable_without_auth": True},
            )
        except Exception as bare_exc:
            _agent_log(
                "D",
                "mongodb.py:connect_to_mongo:bare_ping_error",
                "Unauthenticated localhost ping failed",
                {
                    "error_type": type(bare_exc).__name__,
                    "error": str(bare_exc),
                    "reachable_without_auth": False,
                },
            )
        # #endregion
        raise


def close_mongo_connection() -> None:
    global _client
    if _client is None:
        return
    _client.close()
    _client = None


def get_mongo_client() -> MongoClient:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized")
    return _client


def get_mongo_db() -> Database:
    return get_mongo_client()[settings.MONGODB_DB_NAME]


def mongo_db_dependency() -> Generator[Database, None, None]:
    yield get_mongo_db()


def check_mongodb() -> dict:
    try:
        get_mongo_client().admin.command("ping")
        return {"status": "ok"}
    except (PyMongoError, RuntimeError) as exc:
        return {"status": "error", "detail": str(exc)}
