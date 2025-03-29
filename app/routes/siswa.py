# app/routes/siswa.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.siswa import SiswaCreate, SiswaResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3

router = APIRouter(prefix="/api/siswa", tags=["siswa"])

@router.post("/", response_model=SiswaResponse)
async def api_create_siswa(
    siswa: SiswaCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create a student")
    
    cursor = db.cursor()
    # Validasi kelas_id
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (siswa.kelas_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Kelas not found")
    
    # Validasi orang_tua_id (opsional, jika ada)
    if siswa.orang_tua_id:
        cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'orang_tua'", (siswa.orang_tua_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Orang tua not found or not a parent")
    
    cursor.execute(
        "INSERT INTO siswa (nama, kelas_id, orang_tua_id, kode_siswa) VALUES (?, ?, ?, ?)",
        (siswa.nama, siswa.kelas_id, siswa.orang_tua_id, siswa.kode_siswa)
    )
    db.commit()
    cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (cursor.lastrowid,))
    new_siswa = cursor.fetchone()
    if not new_siswa:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created siswa")
    return new_siswa