from fastapi import APIRouter

from app.schemas.response import ok

api_router = APIRouter()
s2s_router = APIRouter()


@s2s_router.get("/")
def list_s2s_consults():
    return ok({"items": []})


@api_router.get("/")
def list_client_consults():
    return {"items": []}