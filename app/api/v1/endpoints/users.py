from fastapi import APIRouter
from app.schemas.user import UserRead, UserCreate

router = APIRouter()

@router.post("/", response_model=UserRead)
def create_user(user_in: UserCreate):
    # Business logic or DB call goes here
    return {"id": 1, "email": user_in.email}