import logging
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_db_connection, get_current_user
import sqlite3
from typing import List
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definisikan model SiswaResponse
class SiswaResponse(BaseModel):
    siswa_id: int
    nama: str
    kelas_id: int
    orang_tua_id: int
    kode_siswa: str

router = APIRouter(prefix="/api/siswa", tags=["siswa"])

@router.get("/kelas/{kelas_id}", response_model=List[SiswaResponse])
async def get_siswa_by_kelas(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Verifikasi role
        if current_user["role"] != "guru":
            logger.error(f"User {current_user['username']} (ID: {current_user['user_id']}) is not a guru")
            raise HTTPException(status_code=403, detail="Only teachers can access student data")

        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Verifikasi wali kelas
        logger.info(f"User {current_user['username']} checking wali kelas for kelas_id: {kelas_id}")
        cursor.execute(
            "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
            (kelas_id, current_user["user_id"])
        )
        kelas = cursor.fetchone()
        if not kelas:
            logger.error(f"User {current_user['user_id']} is not the wali kelas of kelas_id {kelas_id}")
            raise HTTPException(status_code=403, detail="You are not the class teacher of this class")

        # Ambil daftar siswa
        logger.info(f"User {current_user['username']} fetching siswa for kelas_id: {kelas_id}")
        cursor.execute("SELECT * FROM siswa WHERE kelas_id = ?", (kelas_id,))
        siswa_list = cursor.fetchall()

        if not siswa_list:
            logger.info(f"No siswa found for kelas_id: {kelas_id} by user {current_user['username']}")
            raise HTTPException(status_code=404, detail="No students found for this class")

        logger.info(f"Found {len(siswa_list)} siswa for kelas_id: {kelas_id} by user {current_user['username']}")
        return [
            {
                "siswa_id": row["siswa_id"],
                "nama": row["nama"],
                "kelas_id": row["kelas_id"],
                "orang_tua_id": row["orang_tua_id"],
                "kode_siswa": row["kode_siswa"]
            }
            for row in siswa_list
        ]

    except sqlite3.Error as e:
        logger.error(f"Database error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/by-kode/{kode_siswa}", response_model=SiswaResponse)
async def get_siswa_by_kode(
    kode_siswa: str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Verifikasi role
        if current_user["role"] != "orang_tua":
            logger.error(f"User {current_user['username']} (ID: {current_user['user_id']}) is not an orang_tua")
            raise HTTPException(status_code=403, detail="Only parents can access this endpoint")

        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Cari siswa berdasarkan kode_siswa
        logger.info(f"User {current_user['username']} fetching siswa with kode_siswa: {kode_siswa}")
        cursor.execute("SELECT * FROM siswa WHERE kode_siswa = ?", (kode_siswa,))
        siswa = cursor.fetchone()
        if not siswa:
            logger.error(f"Siswa with kode_siswa {kode_siswa} not found for user {current_user['username']}")
            raise HTTPException(status_code=404, detail="Siswa not found with this code")

        # Verifikasi orang tua
        if siswa["orang_tua_id"] != current_user["user_id"]:
            logger.error(f"User {current_user['user_id']} does not have access to siswa with kode_siswa {kode_siswa}")
            raise HTTPException(status_code=403, detail="You do not have access to this student's data")

        logger.info(f"Siswa with kode_siswa {kode_siswa} retrieved by user {current_user['username']}")
        return {
            "siswa_id": siswa["siswa_id"],
            "nama": siswa["nama"],
            "kelas_id": siswa["kelas_id"],
            "orang_tua_id": siswa["orang_tua_id"],
            "kode_siswa": siswa["kode_siswa"]
        }

    except sqlite3.Error as e:
        logger.error(f"Database error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/orang-tua", response_model=List[SiswaResponse])
async def get_siswa_by_orang_tua(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Verifikasi role
        if current_user["role"] != "orang_tua":
            logger.error(f"User {current_user['username']} (ID: {current_user['user_id']}) is not an orang_tua")
            raise HTTPException(status_code=403, detail="Only parents can access this endpoint")

        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Ambil daftar siswa
        logger.info(f"User {current_user['username']} fetching siswa for orang_tua_id: {current_user['user_id']}")
        cursor.execute("SELECT * FROM siswa WHERE orang_tua_id = ?", (current_user["user_id"],))
        siswa_list = cursor.fetchall()

        if not siswa_list:
            logger.info(f"No siswa found for orang_tua_id: {current_user['user_id']} by user {current_user['username']}")
            return []

        logger.info(f"Found {len(siswa_list)} siswa for orang_tua_id: {current_user['user_id']} by user {current_user['username']}")
        return [
            {
                "siswa_id": row["siswa_id"],
                "nama": row["nama"],
                "kelas_id": row["kelas_id"],
                "orang_tua_id": row["orang_tua_id"],
                "kode_siswa": row["kode_siswa"]
            }
            for row in siswa_list
        ]

    except sqlite3.Error as e:
        logger.error(f"Database error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")