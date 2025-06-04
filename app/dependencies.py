# app/dependencies.py
from fastapi.templating import Jinja2Templates
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import sqlite3
from app.utils.security import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db_connection():
    conn = sqlite3.connect("app/data/school.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db_connection)):
    payload = verify_token(token)
    username = payload.get("sub")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Tambahkan dependensi untuk templates
def get_templates():
    return Jinja2Templates(directory="templates")