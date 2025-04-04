# app/routes/jadwal.py
# from fastapi import APIRouter, Depends, HTTPException
# from app.schemas.jadwal import JadwalCreate, JadwalResponse
# from app.dependencies import get_db_connection, get_current_user
# import sqlite3

# router = APIRouter(prefix="/api/jadwal", tags=["jadwal"])

# @router.post("/", response_model=JadwalResponse)
# async def api_create_jadwal(
#     jadwal: JadwalCreate,
#     db: sqlite3.Connection = Depends(get_db_connection),
#     current_user: dict = Depends(get_current_user)
# ):
#     if current_user["role"] != "guru":
#         raise HTTPException(status_code=403, detail="Only teachers can create a schedule")
    
#     cursor = db.cursor()
#     cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (jadwal.kelas_id,))
#     if not cursor.fetchone():
#         raise HTTPException(status_code=404, detail="Kelas not found")
    
#     cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (jadwal.mata_pelajaran_id,))
#     if not cursor.fetchone():
#         raise HTTPException(status_code=404, detail="Mata pelajaran not found")
    
#     cursor.execute(
#         "INSERT INTO jadwal (kelas_id, hari, jam_mulai, jam_selesai, mata_pelajaran_id) VALUES (?, ?, ?, ?, ?)",
#         (jadwal.kelas_id, jadwal.hari, jadwal.jam_mulai, jadwal.jam_selesai, jadwal.mata_pelajaran_id)
#     )
#     db.commit()
#     cursor.execute("SELECT * FROM jadwal WHERE jadwal_id = ?", (cursor.lastrowid,))
#     new_jadwal = cursor.fetchone()
#     if not new_jadwal:
#         raise HTTPException(status_code=500, detail="Failed to retrieve newly created jadwal")
#     return new_jadwal
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.jadwal import JadwalCreate, JadwalResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3
from typing import List
from datetime import datetime

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
    
    # Ambil data mata pelajaran
    cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (new_jadwal[5],))
    mata_pelajaran = cursor.fetchone()
    
    # Ambil data kelas untuk mendapatkan wali kelas
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (new_jadwal[1],))
    kelas = cursor.fetchone()
    
    # Ambil data wali kelas
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (kelas[2],))
    wali_kelas = cursor.fetchone()
    
    return {
        "jadwal_id": new_jadwal[0],
        "kelas_id": new_jadwal[1],
        "hari": new_jadwal[2],
        "jam_mulai": new_jadwal[3],
        "jam_selesai": new_jadwal[4],
        "mata_pelajaran_id": new_jadwal[5],
        "mata_pelajaran": {
            "mata_pelajaran_id": mata_pelajaran[0],
            "nama": mata_pelajaran[1],
            "kode": mata_pelajaran[2],
            "deskripsi": mata_pelajaran[3]
        },
        "wali_kelas": {
            "user_id": wali_kelas[0],
            "nama": wali_kelas[1],
            "username": wali_kelas[2],
            "role": wali_kelas[3],
            "created_at": wali_kelas[4]
        }
    }

@router.get("/kelas/{kelas_id}/current", response_model=List[JadwalResponse])
async def get_current_jadwal(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can access schedules")
    
    cursor = db.cursor()
    # Pastikan kelas ada dan user adalah wali kelas
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?", (kelas_id, current_user["user_id"]))
    kelas = cursor.fetchone()
    if not kelas:
        raise HTTPException(status_code=403, detail="Kelas not found or you are not the class teacher")
    
    # Ambil hari dan jam saat ini
    now = datetime.now()
    current_day = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][now.weekday()]
    current_time = now.strftime("%H:%M:%S")
    
    # Ambil jadwal untuk kelas tersebut pada hari ini
    cursor.execute(
        """
        SELECT j.* FROM jadwal j
        WHERE j.kelas_id = ? AND j.hari = ? AND j.jam_mulai <= ? AND j.jam_selesai >= ?
        """,
        (kelas_id, current_day, current_time, current_time)
    )
    jadwal_list = cursor.fetchall()
    if not jadwal_list:
        return []
    
    # Ambil data tambahan untuk setiap jadwal
    result = []
    for jadwal in jadwal_list:
        # Ambil data mata pelajaran
        cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (jadwal[5],))
        mata_pelajaran = cursor.fetchone()
        
        # Ambil data wali kelas
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
            },
            "wali_kelas": {
                "user_id": wali_kelas[0],
                "nama": wali_kelas[1],
                "username": wali_kelas[2],
                "role": wali_kelas[3],
                "created_at": wali_kelas[4]
            }
        })
    
    return result