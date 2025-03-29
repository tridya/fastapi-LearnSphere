# app/routes/notifikasi.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.notifikasi import NotifikasiCreate, NotifikasiResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3

router = APIRouter(prefix="/api/notifikasi", tags=["notifikasi"])

@router.post("/", response_model=NotifikasiResponse)
async def api_create_notifikasi(
    notifikasi: NotifikasiCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create notifications")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (notifikasi.siswa_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Siswa not found")
    
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'orang_tua'", (notifikasi.orang_tua_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Orang tua not found")
    
    cursor.execute(
        "INSERT INTO notifikasi (siswa_id, orang_tua_id, jenis, deskripsi, status) VALUES (?, ?, ?, ?, ?)",
        (notifikasi.siswa_id, notifikasi.orang_tua_id, notifikasi.jenis, notifikasi.deskripsi, notifikasi.status)
    )
    db.commit()
    cursor.execute("SELECT * FROM notifikasi WHERE notifikasi_id = ?", (cursor.lastrowid,))
    new_notifikasi = cursor.fetchone()
    if not new_notifikasi:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created notifikasi")
    return new_notifikasi