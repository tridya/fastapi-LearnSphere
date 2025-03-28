from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class UserBase(BaseModel):
    nama: str
    username: str
    role: Literal["guru", "orang_tua"]

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    user_id: int
    password: str  # Hashed password
    created_at: datetime

    class Config:
        from_attributes = True  # Diubah ke from_attributes

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str