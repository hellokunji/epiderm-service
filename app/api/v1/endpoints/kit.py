from fastapi import APIRouter

from app.schemas.response import ok

api_router = APIRouter()
s2s_router = APIRouter()


@s2s_router.get("/")
def list_s2s_kits():
    return ok({"items": []})


@api_router.get("/")
def list_client_kits():
    return {"items": []}