from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.v1.router import router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.mongodb import close_mongo_connection, connect_to_mongo
from app.models import Consult, QuestionnaireVersion  # noqa: F401 — register models with metadata
from app.services.health import check_database, check_mongodb, check_redis

# Ensure app / FLOW logs appear in the uvicorn terminal (access logs alone are not enough).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    force=True,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    connect_to_mongo()
    try:
        yield
    finally:
        close_mongo_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.include_router(router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok"}


@app.get("/health", tags=["Health"])
def detailed_health_check():
    return {
        "status": "ok",
        "database": check_database(),
        "mongodb": check_mongodb(),
        "redis": check_redis(),
    }
