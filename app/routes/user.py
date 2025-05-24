from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.utils.security import verify_password, create_access_token
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.schemas.user import UserInDB  # Import skema yang benar
import sqlite3

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
        print(f"JWT payload: {payload}")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        print(f"JWT error: {str(e)}")
        raise credentials_exception

    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user is None:
        print(f"No user found for username: {username}")
        raise credentials_exception
    
    user_dict = dict(user)
    if user_dict["user_id"] <= 0:
        print(f"Invalid user_id for user: {user_dict}")
        raise HTTPException(status_code=500, detail="Invalid user ID in database")
    
    print(f"User fetched from DB: {user_dict}")
    return user_dict

@router.get("/me", response_model=UserInDB)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    print(f"Returning user: {current_user}")  # Log data yang dikembalikan
    return {
        "user_id": current_user["user_id"],
        "nama": current_user["nama"],
        "username": current_user["username"],
        "role": current_user["role"],
        "password": current_user["password"],
        "created_at": current_user["created_at"]
    }