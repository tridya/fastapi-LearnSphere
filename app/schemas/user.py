from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class UserBase(BaseModel):
    user_id:int
    nama: str
    username: str
    role: Literal["guru", "orang_tua"]

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    user_id: int
    password: str
    created_at: datetime

    class Config:
        from_attributes = True  # Already correct, no change needed

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str