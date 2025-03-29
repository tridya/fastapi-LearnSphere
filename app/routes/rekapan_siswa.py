# app/routes/rekapan_siswa.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.rekapan_siswa import RekapanSiswaCreate, RekapanSiswaResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3

router = APIRouter(prefix="/api/rekapan-siswa", tags=["rekapan_siswa"])

@router.post("/", response_model=RekapanSiswaResponse)
async def api_create_rekapan_siswa(
    rekapan: RekapanSiswaCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create student reports")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (rekapan.siswa_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Siswa not found")
    
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'guru'", (rekapan.guru_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Guru not found")
    
    cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (rekapan.mata_pelajaran_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Mata pelajaran not found")
    
    cursor.execute(
        "INSERT INTO rekapan_siswa (siswa_id, guru_id, mata_pelajaran_id, rating, catatan) VALUES (?, ?, ?, ?, ?)",
        (rekapan.siswa_id, rekapan.guru_id, rekapan.mata_pelajaran_id, rekapan.rating, rekapan.catatan)
    )
    db.commit()
    cursor.execute("SELECT * FROM rekapan_siswa WHERE report_id = ?", (cursor.lastrowid,))
    new_rekapan = cursor.fetchone()
    if not new_rekapan:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created rekapan")
    return new_rekapan