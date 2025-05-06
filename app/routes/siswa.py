from fastapi import APIRouter, Depends, HTTPException
from app.schemas.siswa import SiswaCreate, SiswaResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3
from typing import List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (siswa.kelas_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Kelas not found")
    
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
    
    return {
        "siswa_id": new_siswa[0],
        "nama": new_siswa[1],
        "kelas_id": new_siswa[2],
        "orang_tua_id": new_siswa[3],
        "kode_siswa": new_siswa[4]
    }

@router.get("/kelas/{kelas_id}", response_model=List[SiswaResponse])
async def get_siswa_by_kelas(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can access student data")
    
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
        (kelas_id, current_user["user_id"])
    )
    kelas = cursor.fetchone()
    if not kelas:
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan atau Anda bukan wali kelas")
    
    cursor.execute("SELECT * FROM siswa WHERE kelas_id = ?", (kelas_id,))
    siswa_list = cursor.fetchall()
    
    return [
        {
            "siswa_id": row[0],
            "nama": row[1],
            "kelas_id": row[2],
            "orang_tua_id": row[3],
            "kode_siswa": row[4]
        }
        for row in siswa_list
    ]

@router.get("/orangtua", response_model=List[SiswaResponse])
async def get_siswa_by_orangtua(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"User attempting to access children's data: {current_user}")
    if current_user["role"] != "orang_tua":
        logger.warning(f"Access denied for user with role={current_user['role']}, expected role='orang_tua'")
        raise HTTPException(status_code=403, detail="Only parents can access their children's data")
    
    cursor = db.cursor()
    logger.info(f"Querying siswa for orang_tua_id={current_user['user_id']}")
    cursor.execute("SELECT * FROM siswa WHERE orang_tua_id = ?", (current_user["user_id"],))
    siswa_list = cursor.fetchall()
    if not siswa_list:
        logger.warning(f"No siswa found for orang_tua_id={current_user['user_id']}")
    else:
        logger.info(f"Siswa found: {siswa_list}")
    
    return [
        {
            "siswa_id": row[0],
            "nama": row[1],
            "kelas_id": row[2],
            "orang_tua_id": row[3],
            "kode_siswa": row[4]
        }
        for row in siswa_list
    ]