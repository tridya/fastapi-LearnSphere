# fastapi-LearnSphere/app/models/auth.py
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str