from fastapi import APIRouter, Depends, HTTPException
from app.schemas.kelas import KelasCreate, KelasResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3
from typing import List
import logging
from datetime import datetime

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
    try:
        # Verifikasi role
        if current_user["role"] != "guru":
            logger.error(f"User {current_user['username']} (ID: {current_user['user_id']}) is not a guru")
            raise HTTPException(status_code=403, detail="Only teachers can create a class")

        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Verifikasi wali kelas
        logger.info(f"User {current_user['username']} verifying wali_kelas_id: {kelas.wali_kelas_id}")
        cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'guru'", (kelas.wali_kelas_id,))
        wali_kelas = cursor.fetchone()
        if not wali_kelas:
            logger.error(f"Wali kelas ID {kelas.wali_kelas_id} not found or not a guru for user {current_user['username']}")
            raise HTTPException(status_code=404, detail="Wali kelas not found or not a guru")

        # Buat kelas baru
        logger.info(f"User {current_user['username']} creating new kelas: {kelas.nama_kelas}")
        cursor.execute(
            "INSERT INTO kelas (nama_kelas, wali_kelas_id) VALUES (?, ?)",
            (kelas.nama_kelas, kelas.wali_kelas_id)
        )
        db.commit()

        # Ambil kelas yang baru dibuat
        cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (cursor.lastrowid,))
        new_kelas = cursor.fetchone()
        if not new_kelas:
            logger.error(f"Failed to retrieve newly created kelas for user {current_user['username']}")
            raise HTTPException(status_code=500, detail="Failed to retrieve newly created kelas")

        logger.info(f"New kelas created: {new_kelas['kelas_id']} by user {current_user['username']}")
        return dict(new_kelas)

    except sqlite3.Error as e:
        logger.error(f"Database error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/", response_model=List[KelasResponse])
async def get_kelas(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Verifikasi role
        if current_user["role"] != "guru":
            logger.error(f"User {current_user['username']} (ID: {current_user['user_id']}) is not a guru")
            raise HTTPException(status_code=403, detail="Only teachers can access this")

        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Ambil kelas yang dikelola oleh guru
        logger.info(f"User {current_user['username']} fetching kelas for guru_id: {current_user['user_id']}")
        cursor.execute(
            "SELECT kelas_id, nama_kelas FROM kelas WHERE wali_kelas_id = ?",
            (current_user["user_id"],)
        )
        kelas_list = cursor.fetchall()

        if not kelas_list:
            logger.warning(f"No kelas found for guru_id: {current_user['user_id']}")
            return []

        logger.info(f"Found {len(kelas_list)} kelas for guru_id: {current_user['user_id']}: {[dict(row) for row in kelas_list]}")
        return [dict(row) for row in kelas_list]

    except sqlite3.Error as e:
        logger.error(f"Database error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{kelas_id}/current", response_model=List[dict])  # Belum ada JadwalResponse, gunakan dict sementara
async def get_current_kelas(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Verifikasi role
        if current_user["role"] != "guru":
            logger.error(f"User {current_user['username']} (ID: {current_user['user_id']}) is not a guru")
            raise HTTPException(status_code=403, detail="Only teachers can access class schedules")

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
            logger.error(f"Kelas ID {kelas_id} not found or user {current_user['user_id']} is not the wali kelas")
            raise HTTPException(status_code=404, detail="Kelas not found or you are not the class teacher")

        # Ambil jadwal saat ini
        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"User {current_user['username']} fetching jadwal for kelas_id: {kelas_id} on {today}")
        cursor.execute(
            "SELECT * FROM jadwal WHERE kelas_id = ? AND tanggal = ?",
            (kelas_id, today)
        )
        jadwal_list = cursor.fetchall()

        if not jadwal_list:
            logger.info(f"No jadwal found for kelas_id: {kelas_id} on {today} by user {current_user['username']}")
            return []

        # Format response
        response = [
            {
                "jadwal_id": row["jadwal_id"],
                "kelas_id": row["kelas_id"],
                "mata_pelajaran": {"nama": row["mata_pelajaran"]},  # Sesuaikan dengan struktur database
                "jam_mulai": row["jam_mulai"],
                "jam_selesai": row["jam_selesai"],
                "wali_kelas": {"nama": current_user["username"]},
                "tanggal": row["tanggal"]
            }
            for row in jadwal_list
        ]
        logger.info(f"Found {len(response)} jadwal for kelas_id: {kelas_id} by user {current_user['username']}")
        return response

    except sqlite3.Error as e:
        logger.error(f"Database error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")