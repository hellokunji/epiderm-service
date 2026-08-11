from fastapi import FastAPI

from app.api.v1.router import router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok"}
