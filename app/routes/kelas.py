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

@router.get("/{kelas_id}/current")
async def get_current_kelas(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can access class schedules")
    
    cursor = db.cursor()
    # Pastikan user adalah wali kelas dari kelas tersebut
    cursor.execute(
        "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
        (kelas_id, current_user["user_id"])
    )
    kelas = cursor.fetchone()
    if not kelas:
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan atau Anda bukan wali kelas")
    
    # Ambil jadwal saat ini (misalnya, berdasarkan hari ini)
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT * FROM jadwal WHERE kelas_id = ? AND tanggal = ?",
        (kelas_id, today)
    )
    jadwal = cursor.fetchall()
    if not jadwal:
        return []  # Return empty list jika tidak ada jadwal
    
    # Format response sesuai dengan JadwalResponse
    return [
        {
            "jadwal_id": row[0],
            "kelas_id": row[1],
            "mata_pelajaran": {"nama": row[2]},  # Sesuaikan dengan struktur database
            "jam_mulai": row[3],
            "jam_selesai": row[4],
            "wali_kelas": {"nama": current_user["username"]},  # Sesuaikan dengan data wali kelas
            "tanggal": row[5]
        }
        for row in jadwal
    ]