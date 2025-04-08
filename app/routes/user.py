# app/routes/user.py
from fastapi import APIRouter, Depends
from app.dependencies import get_db_connection, get_current_user
from app.schemas.user import UserInDB
import sqlite3

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=UserInDB)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "nama": current_user["nama"],
        "username": current_user["username"],
        "role": current_user["role"],
        "password": current_user["password"],  # Note: Avoid returning this in production
        "created_at": current_user["created_at"]
    }