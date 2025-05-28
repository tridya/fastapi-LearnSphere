from fastapi import APIRouter, Depends, HTTPException
from app.schemas.kelas import KelasCreate, KelasResponse
from app.schemas.jadwal import JadwalResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3
from typing import List
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    return {
        "kelas_id": new_kelas[0],
        "nama_kelas": new_kelas[1],
        "wali_kelas_id": new_kelas[2]
    }

@router.get("/{kelas_id}/current", response_model=List[JadwalResponse])
async def get_current_kelas(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can access class schedules")
    
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
        (kelas_id, current_user["user_id"])
    )
    kelas = cursor.fetchone()
    if not kelas:
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan atau Anda bukan wali kelas")
    
    # Ambil jadwal saat ini berdasarkan hari dan waktu
    current_time = datetime.now()
    current_day = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][current_time.weekday()]
    current_time_str = current_time.strftime("%H:%M")
    
    cursor.execute(
        """
        SELECT * FROM jadwal
        WHERE kelas_id = ? AND hari = ? AND jam_mulai <= ? AND jam_selesai >= ?
        """,
        (kelas_id, current_day, current_time_str, current_time_str)
    )
    jadwal_list = cursor.fetchall()
    logger.info(f"Jadwal found for kelas_id={kelas_id}, hari={current_day}: {jadwal_list}")
    
    result = []
    for jadwal in jadwal_list:
        cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (jadwal[5],))
        mata_pelajaran = cursor.fetchone()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (kelas[2],))
        wali_kelas = cursor.fetchone()
        
        result.append({
            "jadwal_id": jadwal[0],
            "kelas_id": jadwal[1],
            "hari": jadwal[2],
            "jam_mulai": jadwal[3],
            "jam_selesai": jadwal[4],
            "mata_pelajaran_id": jadwal[5],
            "mata_pelajaran": {
                "mata_pelajaran_id": mata_pelajaran[0],
                "nama": mata_pelajaran[1],
                "kode": mata_pelajaran[2],
                "deskripsi": mata_pelajaran[3]
            } if mata_pelajaran else None,
            "wali_kelas": {
                "user_id": wali_kelas[0],
                "nama": wali_kelas[1],
                "username": wali_kelas[2],
                "role": wali_kelas[3]
            } if wali_kelas else None
        })
    return result