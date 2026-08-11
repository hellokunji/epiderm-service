from fastapi import APIRouter, Depends
from app.schemas.response import ok

api_router = APIRouter()
s2s_router = APIRouter()

@s2s_router.get("/")
def list_client_questionnaires():
    return ok({"items": []})

@api_router.get("/")
def list_client_questionnaires():
    return {"items": []}

