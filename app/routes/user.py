# app/routes/user.py
from fastapi import APIRouter, Depends
from app.schemas.user import UserInDB
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=UserInDB)
async def get_current_user_endpoint(current_user: dict = Depends(get_current_user)):
    return current_user