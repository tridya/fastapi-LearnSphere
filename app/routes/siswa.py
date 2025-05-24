from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_db_connection, get_current_user
import sqlite3
from typing import List
import logging
from app.schemas.siswa import SiswaResponse

router = APIRouter(prefix="/api/siswa", tags=["siswa"])

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@router.get("/kelas/{kelas_id}", response_model=List[SiswaResponse])
async def get_siswa_by_kelas(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch all students in a specific class for the homeroom teacher.
    """
    logger.debug(f"Endpoint /api/siswa/kelas/{kelas_id} invoked for user {current_user['user_id']}")
    
    if current_user["role"] != "guru":
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru")
        raise HTTPException(status_code=403, detail="Only teachers can access student data")
    
    cursor = db.cursor()
    # Pastikan user adalah wali kelas dari kelas tersebut
    cursor.execute(
        "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
        (kelas_id, current_user["user_id"])
    )
    kelas = cursor.fetchone()
    if not kelas:
        logger.error(f"Kelas {kelas_id} not found or user {current_user['user_id']} is not wali kelas")
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan atau Anda bukan wali kelas")
    
    # Ambil daftar siswa di kelas tersebut
    cursor.execute(
        """
        SELECT siswa_id, nama, kelas_id, orang_tua_id, kode_siswa 
        FROM siswa 
        WHERE kelas_id = ?
        """,
        (kelas_id,)
    )
    siswa_list = cursor.fetchall()
    if not siswa_list:
        logger.info(f"No students found for kelas_id: {kelas_id}")
        return []
    
    logger.info(f"Found {len(siswa_list)} students for kelas_id: {kelas_id}")
    
    # Map to SiswaResponse
    return [
        SiswaResponse(
            siswa_id=row[0],
            nama=row[1],
            kelas_id=row[2],
            orang_tua_id=row[3],
            kode_siswa=row[4]
        )
        for row in siswa_list
    ]

@router.get("/orangtua", response_model=List[SiswaResponse])
async def get_siswa_orangtua(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch all students associated with the authenticated parent user.
    """
    logger.debug(f"Endpoint /api/siswa/orangtua invoked for user {current_user['user_id']}, role={current_user['role']}")
    
    # Restrict access to parents only
    if current_user["role"] != "orang_tua":
        logger.error(f"Access denied for user {current_user['user_id']}: role is {current_user['role']}, expected orang_tua")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya orang tua yang dapat mengakses data siswa"
        )
    
    cursor = db.cursor()
    
    # Fetch the orang_tua_id linked to the user
    cursor.execute(
        "SELECT orang_tua_id FROM orang_tua WHERE user_id = ?",
        (current_user["user_id"],)
    )
    orang_tua = cursor.fetchone()
    if not orang_tua:
        logger.error(f"No orang_tua record found for user_id: {current_user['user_id']}. Please ensure an orang_tua record exists in the database.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Akun orang tua tidak ditemukan untuk user_id {current_user['user_id']}. Hubungi admin untuk mendaftarkan akun orang tua."
        )
    
    orang_tua_id = orang_tua[0]
    logger.debug(f"Found orang_tua_id: {orang_tua_id} for user_id: {current_user['user_id']}")
    
    # Fetch students linked to the orang_tua_id
    cursor.execute(
        """
        SELECT siswa_id, nama, kelas_id, orang_tua_id, kode_siswa 
        FROM siswa 
        WHERE orang_tua_id = ?
        """,
        (orang_tua_id,)
    )
    siswa_list = cursor.fetchall()
    
    if not siswa_list:
        logger.info(f"No students found for orang_tua_id: {orang_tua_id}")
        return []
    
    logger.info(f"Found {len(siswa_list)} students for orang_tua_id: {orang_tua_id}")
    
    # Map to SiswaResponse
    return [
        SiswaResponse(
            siswa_id=row[0],
            nama=row[1],
            kelas_id=row[2],
            orang_tua_id=row[3],
            kode_siswa=row[4]
        )
        for row in siswa_list
    ]