# app/routes/user.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.database import get_db
from app.utils.security import verify_password, create_access_token
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.schemas.user import UserInDB
import sqlite3
import logging
import base64

router = APIRouter(prefix="/api/users", tags=["users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    from app.utils.security import SECRET_KEY, ALGORITHM

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user is None:
        raise credentials_exception
    
    logging.info(f"User data from DB: {user}")
    columns = [column[0] for column in cursor.description]
    user_dict = dict(zip(columns, user))
    return user_dict

@router.get("/me", response_model=UserInDB)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    # Konversi BLOB ke base64 untuk dikirim ke frontend
    profile_picture_base64 = None
    if current_user.get("profile_picture"):
        profile_picture_base64 = base64.b64encode(current_user["profile_picture"]).decode("utf-8")
    
    return {
        "user_id": current_user["user_id"],
        "nama": current_user["nama"],
        "username": current_user["username"],
        "role": current_user["role"],
        "password": current_user["password"],
        "created_at": current_user["created_at"],
        "profile_picture": profile_picture_base64  # Kirim sebagai base64
    }

@router.post("/me/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    logging.info(f"Current user: {current_user}")
    logging.info(f"File received: {file.filename}")

    # Baca konten file sebagai data biner
    try:
        content = await file.read()
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to read file")

    # Simpan data biner ke database
    cursor = db.cursor()
    try:
        logging.info(f"Executing SQL: UPDATE users SET profile_picture = ? WHERE user_id = ?")
        cursor.execute(
            "UPDATE users SET profile_picture = ? WHERE user_id = ?",
            (sqlite3.Binary(content), current_user["user_id"])
        )
        db.commit()
        logging.info("Update database berhasil.")
    except sqlite3.OperationalError as e:
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return {"message": "Profile picture updated successfully"}