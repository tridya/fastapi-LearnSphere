from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserInDB, Token
from app.utils.security import hash_password, verify_password, create_access_token
from app.dependencies import get_db_connection
import sqlite3
from datetime import timedelta

# Inisialisasi router untuk endpoint autentikasi dengan prefix "/auth"
router = APIRouter(prefix="/auth", tags=["auth"])

# Endpoint untuk registrasi pengguna baru
@router.post("/register", response_model=UserInDB)
async def api_register_user(user: UserCreate, db: sqlite3.Connection = Depends(get_db_connection)):
    try:
        # Hash password sebelum menyimpan ke database
        hashed_password = hash_password(user.password)
        cursor = db.cursor()
        # Insert data pengguna baru ke tabel users
        cursor.execute(
            "INSERT INTO users (nama, username, password, role) VALUES (?, ?, ?, ?)",
            (user.nama, user.username, hashed_password, user.role)
        )
        db.commit()
        # Ambil data pengguna yang baru dibuat
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (cursor.lastrowid,))
        new_user = cursor.fetchone()
        if not new_user:
            raise HTTPException(status_code=500, detail="Failed to retrieve newly created user")
        return dict(new_user)  # Kembalikan data pengguna sebagai respons
    except sqlite3.IntegrityError:
        # Tangani kasus username sudah ada (konstrain unik di database)
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        # Tangani error tak terduga
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Endpoint untuk login pengguna
@router.post("/login", response_model=Token)
async def api_login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db_connection)):
    cursor = db.cursor()
    # Cari pengguna berdasarkan username
    cursor.execute("SELECT * FROM users WHERE username = ?", (form_data.username,))
    db_user = cursor.fetchone()
    
    # Validasi username: jika tidak ditemukan, kembalikan error spesifik
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username not found",  # Pesan error jika username tidak ada
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validasi password: jika tidak cocok, kembalikan error spesifik
    if not verify_password(form_data.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",  # Pesan error jika password salah
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Jika autentikasi berhasil, buat access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user["username"], "role": db_user["role"]},
        expires_delta=access_token_expires
    )
    # Kembalikan token sebagai respons
    return {"access_token": access_token, "token_type": "bearer"}