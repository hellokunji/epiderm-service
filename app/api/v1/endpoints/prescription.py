from fastapi import APIRouter, Depends
from app.schemas.response import ok

api_router = APIRouter()
s2s_router = APIRouter()

@api_router.get("/")
def list_client_prescriptions():
    return ok({"items": []})

@s2s_router.get("/")
def list_s2s_prescriptions():
    return ok({"items": []})