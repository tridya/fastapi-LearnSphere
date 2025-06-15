# app/dependencies.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
import sqlite3
from app.utils.security import SECRET_KEY, ALGORITHM
from jose import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db_connection():
    conn = sqlite3.connect("school.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_templates():
    return Jinja2Templates(directory="templates")

def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db_connection)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # First, try the token from the Authorization header (oauth2_scheme)
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except jwt.JWTError:
            # If header token fails, try the cookie
            token = request.cookies.get("access_token")
            if not token:
                raise credentials_exception
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username: str = payload.get("sub")
                if username is None:
                    raise credentials_exception
            except jwt.JWTError:
                raise credentials_exception
    else:
        # If no token in header, check cookie directly
        token = request.cookies.get("access_token")
        if not token:
            raise credentials_exception
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except jwt.JWTError:
            raise credentials_exception

    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user is None:
        raise credentials_exception
    
    return dict(user)