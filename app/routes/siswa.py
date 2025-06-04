from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.siswa import SiswaCreate, SiswaResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3
from typing import List
import logging
from app.schemas.siswa import SiswaResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/siswa", tags=["siswa"])

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AssignKelasRequest(BaseModel):
    kelas_id: int

@router.get("/kelas/{kelas_id}", response_model=List[SiswaResponse])
async def get_siswa_by_kelas(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Endpoint /api/siswa/kelas/{kelas_id} invoked for user {current_user['user_id']}")
    
    if current_user["role"] != "guru":
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru")
        raise HTTPException(status_code=403, detail="Hanya guru yang dapat mengakses data siswa")
    
    cursor = db.cursor()
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
    logger.debug(f"Endpoint /api/siswa/orangtua invoked for user {current_user['user_id']}, role={current_user['role']}")
    
    if current_user["role"] != "orang_tua":
        logger.error(f"Access denied for user {current_user['user_id']}: role is {current_user['role']}, expected orang_tua")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya orang tua yang dapat mengakses data siswa"
        )
    
    cursor = db.cursor()
    
    # Verify that the user is a parent
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ? AND role = 'orang_tua'",
        (current_user["user_id"],)
    )
    parent = cursor.fetchone()
    if not parent:
        logger.error(f"No parent record found for user_id: {current_user['user_id']}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Akun orang tua tidak ditemukan"
        )
    
    orang_tua_id = parent[0]
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
    
    # Check if kelas_id is valid
    valid_kelas_ids = set(
        cursor.execute("SELECT kelas_id FROM kelas").fetchall()
    )
    valid_kelas_ids = {row[0] for row in valid_kelas_ids}
    
    return [
        SiswaResponse(
            siswa_id=row[0],
            nama=row[1],
            kelas_id=row[2] if row[2] in valid_kelas_ids else None,
            orang_tua_id=row[3],
            kode_siswa=row[4],
            is_unassigned=row[2] is None or row[2] not in valid_kelas_ids
        )
        for row in siswa_list
    ]

@router.post("/{siswa_id}/assign-kelas", response_model=SiswaResponse)
async def assign_kelas_to_siswa(
    siswa_id: int,
    request: AssignKelasRequest,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Endpoint /api/siswa/{siswa_id}/assign-kelas invoked for user {current_user['user_id']}")
    
    if current_user["role"] not in ["guru", "admin"]:
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru or admin")
        raise HTTPException(status_code=403, detail="Hanya guru atau admin yang dapat menetapkan kelas")
    
    cursor = db.cursor()
    
    # Verify siswa exists
    cursor.execute(
        """
        SELECT siswa_id, nama, kelas_id, orang_tua_id, kode_siswa 
        FROM siswa 
        WHERE siswa_id = ?
        """,
        (siswa_id,)
    )
    siswa = cursor.fetchone()
    if not siswa:
        logger.error(f"Siswa not found for siswa_id: {siswa_id}")
        raise HTTPException(status_code=404, detail="Siswa tidak ditemukan")
    
    # Verify kelas exists
    cursor.execute("SELECT kelas_id FROM kelas WHERE kelas_id = ?", (request.kelas_id,))
    kelas = cursor.fetchone()
    if not kelas:
        logger.error(f"Kelas not found for kelas_id: {request.kelas_id}")
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan")
    
    # Update siswa with new kelas_id
    try:
        cursor.execute(
            """
            UPDATE siswa 
            SET kelas_id = ? 
            WHERE siswa_id = ?
            """,
            (request.kelas_id, siswa_id)
        )
        db.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error while updating siswa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui kelas siswa: {str(e)}")
    
    # Fetch updated siswa
    cursor.execute(
        """
        SELECT siswa_id, nama, kelas_id, orang_tua_id, kode_siswa 
        FROM siswa 
        WHERE siswa_id = ?
        """,
        (siswa_id,)
    )
    updated_siswa = cursor.fetchone()
    
    logger.info(f"Assigned kelas_id: {request.kelas_id} to siswa_id: {siswa_id}")
    return SiswaResponse(
        siswa_id=updated_siswa[0],
        nama=updated_siswa[1],
        kelas_id=updated_siswa[2],
        orang_tua_id=updated_siswa[3],
        kode_siswa=updated_siswa[4],
        is_unassigned=False
    )