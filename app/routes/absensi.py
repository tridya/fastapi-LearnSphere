# app/routes/absensi.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.absensi import AbsensiCreate, AbsensiResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3

router = APIRouter(prefix="/api/absensi", tags=["absensi"])

@router.post("/", response_model=AbsensiResponse)
async def api_store_absensi(
    absensi: AbsensiCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can record attendance")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (absensi.siswa_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Siswa not found")
    
    cursor.execute(
        "INSERT INTO absensi (siswa_id, tanggal, status) VALUES (?, ?, ?)",
        (absensi.siswa_id, absensi.tanggal, absensi.status)
    )
    db.commit()
    cursor.execute("SELECT * FROM absensi WHERE absensi_id = ?", (cursor.lastrowid,))
    new_absensi = cursor.fetchone()
    if not new_absensi:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created absensi")
    return new_absensi