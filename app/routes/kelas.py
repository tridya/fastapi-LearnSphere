# app/routes/kelas.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.kelas import KelasCreate, KelasResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3

router = APIRouter(prefix="/api/kelas", tags=["kelas"])

@router.post("/", response_model=KelasResponse)
async def api_create_kelas(
    kelas: KelasCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create a class")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'guru'", (kelas.wali_kelas_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Wali kelas not found or not a guru")
    
    cursor.execute(
        "INSERT INTO kelas (nama_kelas, wali_kelas_id) VALUES (?, ?)",
        (kelas.nama_kelas, kelas.wali_kelas_id)
    )
    db.commit()
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (cursor.lastrowid,))
    new_kelas = cursor.fetchone()
    if not new_kelas:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created kelas")
    return new_kelas