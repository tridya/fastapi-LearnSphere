# app/routes/siswa.py
# from fastapi import APIRouter, Depends, HTTPException
# from app.schemas.siswa import SiswaCreate, SiswaResponse
# from app.dependencies import get_db_connection, get_current_user
# import sqlite3

# router = APIRouter(prefix="/api/siswa", tags=["siswa"])

# @router.post("/", response_model=SiswaResponse)
# async def api_create_siswa(
#     siswa: SiswaCreate,
#     db: sqlite3.Connection = Depends(get_db_connection),
#     current_user: dict = Depends(get_current_user)
# ):
#     if current_user["role"] != "guru":
#         raise HTTPException(status_code=403, detail="Only teachers can create a student")
    
#     cursor = db.cursor()
#     # Validasi kelas_id
#     cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (siswa.kelas_id,))
#     if not cursor.fetchone():
#         raise HTTPException(status_code=404, detail="Kelas not found")
    
#     # Validasi orang_tua_id (opsional, jika ada)
#     if siswa.orang_tua_id:
#         cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'orang_tua'", (siswa.orang_tua_id,))
#         if not cursor.fetchone():
#             raise HTTPException(status_code=404, detail="Orang tua not found or not a parent")
    
#     cursor.execute(
#         "INSERT INTO siswa (nama, kelas_id, orang_tua_id, kode_siswa) VALUES (?, ?, ?, ?)",
#         (siswa.nama, siswa.kelas_id, siswa.orang_tua_id, siswa.kode_siswa)
#     )
#     db.commit()
#     cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (cursor.lastrowid,))
#     new_siswa = cursor.fetchone()
#     if not new_siswa:
#         raise HTTPException(status_code=500, detail="Failed to retrieve newly created siswa")
#     return new_siswa
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_db_connection, get_current_user
import sqlite3
from typing import List

router = APIRouter(prefix="/api/siswa", tags=["siswa"])

@router.get("/kelas/{kelas_id}")
async def get_siswa_by_kelas(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can access student data")
    
    cursor = db.cursor()
    # Pastikan user adalah wali kelas dari kelas tersebut
    cursor.execute(
        "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
        (kelas_id, current_user["user_id"])
    )
    kelas = cursor.fetchone()
    if not kelas:
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan atau Anda bukan wali kelas")
    
    # Ambil daftar siswa di kelas tersebut
    cursor.execute("SELECT * FROM siswa WHERE kelas_id = ?", (kelas_id,))
    siswa_list = cursor.fetchall()
    if not siswa_list:
        return []  # Return empty list jika tidak ada siswa
    
    # Format response sesuai dengan SiswaResponse
    return [
        {
            "siswa_id": row[0],
            "nama": row[1],
            "kelas_id": row[2]
        }
        for row in siswa_list
    ]