from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserInDB, Token
from app.utils.security import hash_password, verify_password, create_access_token
from app.dependencies import get_db_connection
import sqlite3
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserInDB)
async def api_register_user(user: UserCreate, db: sqlite3.Connection = Depends(get_db_connection)):
    try:
        hashed_password = hash_password(user.password)
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (nama, username, password, role) VALUES (?, ?, ?, ?)",
            (user.nama, user.username, hashed_password, user.role)
        )
        db.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (cursor.lastrowid,))
        new_user = cursor.fetchone()
        if not new_user:
            raise HTTPException(status_code=500, detail="Failed to retrieve newly created user")
        return dict(new_user)  # Konversi ke dict untuk response
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/login", response_model=Token)
async def api_login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db_connection)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (form_data.username,))
    db_user = cursor.fetchone()
    
    if not db_user or not verify_password(form_data.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Buat token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user["username"], "role": db_user["role"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}