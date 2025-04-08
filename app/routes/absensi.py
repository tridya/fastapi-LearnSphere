import logging
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.absensi import AbsensiCreate, AbsensiResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3
from typing import List
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/absensi", tags=["absensi"])

@router.post("/", response_model=AbsensiResponse)
async def api_store_absensi(
    absensi: AbsensiCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Verifikasi role
        if current_user["role"] != "guru":
            logger.error(f"User {current_user['username']} (ID: {current_user['user_id']}) is not a guru")
            raise HTTPException(status_code=403, detail="Only teachers can record attendance")

        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Verifikasi siswa
        logger.info(f"User {current_user['username']} (ID: {current_user['user_id']}) verifying siswa_id: {absensi.siswa_id}")
        cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (absensi.siswa_id,))
        siswa = cursor.fetchone()
        if not siswa:
            logger.error(f"Siswa_id {absensi.siswa_id} not found for user {current_user['username']}")
            raise HTTPException(status_code=404, detail="Siswa not found")

        # Verifikasi wali kelas
        logger.info(f"User {current_user['username']} checking wali kelas for kelas_id: {siswa['kelas_id']}")
        cursor.execute(
            "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
            (siswa["kelas_id"], current_user["user_id"])
        )
        kelas = cursor.fetchone()
        if not kelas:
            logger.error(f"User {current_user['user_id']} is not the wali kelas of kelas_id {siswa['kelas_id']}")
            raise HTTPException(status_code=403, detail="You are not the class teacher of this student")

        # Validasi tanggal
        try:
            datetime.strptime(absensi.tanggal, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {absensi.tanggal} by user {current_user['username']}")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # Cek absensi existing
        cursor.execute(
            "SELECT * FROM absensi WHERE siswa_id = ? AND tanggal = ?",
            (absensi.siswa_id, absensi.tanggal)
        )
        existing_absensi = cursor.fetchone()

        if existing_absensi:
            logger.info(f"User {current_user['username']} updating absensi for siswa_id: {absensi.siswa_id}")
            cursor.execute(
                "UPDATE absensi SET status = ? WHERE absensi_id = ?",
                (absensi.status, existing_absensi["absensi_id"])
            )
            db.commit()
            cursor.execute("SELECT * FROM absensi WHERE absensi_id = ?", (existing_absensi["absensi_id"],))
            updated_absensi = cursor.fetchone()
            logger.info(f"Absensi updated for siswa_id: {absensi.siswa_id} by user {current_user['username']}")
            return dict(updated_absensi)
        else:
            logger.info(f"User {current_user['username']} creating new absensi for siswa_id: {absensi.siswa_id}")
            cursor.execute(
                "INSERT INTO absensi (siswa_id, tanggal, status) VALUES (?, ?, ?)",
                (absensi.siswa_id, absensi.tanggal, absensi.status)
            )
            db.commit()
            cursor.execute("SELECT * FROM absensi WHERE absensi_id = ?", (cursor.lastrowid,))
            new_absensi = cursor.fetchone()
            logger.info(f"New absensi created for siswa_id: {absensi.siswa_id} by user {current_user['username']}")
            return dict(new_absensi)

    except sqlite3.Error as e:
        logger.error(f"Database error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/kelas/{kelas_id}", response_model=List[AbsensiResponse])
async def get_absensi_by_class_and_date(
    kelas_id: int,
    tanggal: str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Verifikasi role
        if current_user["role"] != "guru":
            logger.error(f"User {current_user['username']} (ID: {current_user['user_id']}) is not a guru")
            raise HTTPException(status_code=403, detail="Only teachers can access attendance")

        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Verifikasi wali kelas
        logger.info(f"User {current_user['username']} checking authorization for kelas_id: {kelas_id}")
        cursor.execute(
            "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
            (kelas_id, current_user["user_id"])
        )
        kelas = cursor.fetchone()
        if not kelas:
            logger.error(f"User {current_user['user_id']} is not the wali kelas of kelas_id {kelas_id}")
            raise HTTPException(status_code=403, detail="You are not the class teacher of this class")

        # Validasi tanggal
        try:
            datetime.strptime(tanggal, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {tanggal} by user {current_user['username']}")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # Ambil daftar siswa
        logger.info(f"User {current_user['username']} fetching siswa for kelas_id: {kelas_id}")
        cursor.execute("SELECT siswa_id FROM siswa WHERE kelas_id = ?", (kelas_id,))
        siswa_list = cursor.fetchall()
        if not siswa_list:
            logger.info(f"No siswa found for kelas_id: {kelas_id} by user {current_user['username']}")
            return []

        siswa_ids = [row["siswa_id"] for row in siswa_list]
        # Gunakan IN dengan parameter untuk mencegah SQL injection
        placeholders = ",".join("?" for _ in siswa_ids)
        query = f"SELECT * FROM absensi WHERE siswa_id IN ({placeholders}) AND tanggal = ?"
        params = siswa_ids + [tanggal]
        logger.debug(f"User {current_user['username']} executing query: {query} with params: {params}")
        cursor.execute(query, params)
        absensi_list = cursor.fetchall()

        logger.info(f"User {current_user['username']} found {len(absensi_list)} absensi records for kelas_id: {kelas_id}")
        return [dict(row) for row in absensi_list]

    except sqlite3.Error as e:
        logger.error(f"Database error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error for user {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")