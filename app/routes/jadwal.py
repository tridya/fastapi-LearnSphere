# app/routes/jadwal.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.jadwal import JadwalCreate, JadwalResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3

router = APIRouter(prefix="/api/jadwal", tags=["jadwal"])

@router.post("/", response_model=JadwalResponse)
async def api_create_jadwal(
    jadwal: JadwalCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create a schedule")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (jadwal.kelas_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Kelas not found")
    
    cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (jadwal.mata_pelajaran_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Mata pelajaran not found")
    
    cursor.execute(
        "INSERT INTO jadwal (kelas_id, hari, jam_mulai, jam_selesai, mata_pelajaran_id) VALUES (?, ?, ?, ?, ?)",
        (jadwal.kelas_id, jadwal.hari, jadwal.jam_mulai, jadwal.jam_selesai, jadwal.mata_pelajaran_id)
    )
    db.commit()
    cursor.execute("SELECT * FROM jadwal WHERE jadwal_id = ?", (cursor.lastrowid,))
    new_jadwal = cursor.fetchone()
    if not new_jadwal:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created jadwal")
    return new_jadwal