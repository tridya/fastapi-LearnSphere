# app/routes/mata_pelajaran.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.mata_pelajaran import MataPelajaranCreate, MataPelajaranResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3
import logging
from typing import List

router = APIRouter(prefix="/api/mata-pelajaran", tags=["mata_pelajaran"])

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@router.post("/", response_model=MataPelajaranResponse)
async def api_create_mata_pelajaran(
    mata_pelajaran: MataPelajaranCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received POST request to /api/mata-pelajaran for user {current_user['user_id']}")
    if current_user["role"] != "guru":
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru")
        raise HTTPException(status_code=403, detail="Hanya guru yang dapat membuat mata pelajaran")
    
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO mata_pelajaran (nama, kode, deskripsi) VALUES (?, ?, ?)",
            (mata_pelajaran.nama, mata_pelajaran.kode, mata_pelajaran.deskripsi)
        )
        db.commit()
        cursor.execute("SELECT mata_pelajaran_id, nama, kode, deskripsi FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (cursor.lastrowid,))
        new_mata_pelajaran = cursor.fetchone()
        if not new_mata_pelajaran:
            logger.error("Failed to retrieve newly created mata pelajaran")
            raise HTTPException(status_code=500, detail="Gagal mengambil mata pelajaran yang baru dibuat")
        logger.info(f"Created mata pelajaran: {new_mata_pelajaran['nama']} for user {current_user['user_id']}")
        return MataPelajaranResponse(
            mata_pelajaran_id=new_mata_pelajaran[0],
            nama=new_mata_pelajaran[1],
            kode=new_mata_pelajaran[2],
            deskripsi=new_mata_pelajaran[3]
        )
    except sqlite3.IntegrityError:
        logger.error(f"Duplicate nama or kode for mata pelajaran: {mata_pelajaran.nama}, {mata_pelajaran.kode}")
        raise HTTPException(status_code=400, detail="Nama atau kode mata pelajaran sudah ada")
    except Exception as e:
        logger.error(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/", response_model=List[MataPelajaranResponse])
async def get_mata_pelajaran_list(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received GET request to /api/mata-pelajaran for user {current_user['user_id']}")
    if current_user["role"] not in ["guru", "orang_tua"]:
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru or orang_tua")
        raise HTTPException(status_code=403, detail="Hanya guru atau orang tua yang dapat melihat daftar mata pelajaran")
    
    cursor = db.cursor()
    
    if current_user["role"] == "orang_tua":
        # Verify that the user is a parent
        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = ? AND role = 'orang_tua'",
            (current_user["user_id"],)
        )
        parent = cursor.fetchone()
        if not parent:
            logger.error(f"No parent record found for user_id: {current_user['user_id']}")
            raise HTTPException(status_code=404, detail="Akun orang tua tidak ditemukan")
        
        orang_tua_id = parent[0]
        
        # Fetch kelas_id of the student's class
        cursor.execute(
            "SELECT DISTINCT kelas_id FROM siswa WHERE orang_tua_id = ?",
            (orang_tua_id,)
        )
        kelas_list = cursor.fetchall()
        if not kelas_list:
            logger.info(f"No students found for orang_tua_id: {orang_tua_id}")
            return []
        
        kelas_ids = [kelas[0] for kelas in kelas_list]
        
        # Fetch mata_pelajaran linked to the student's kelas via jadwal
        cursor.execute(
            """
            SELECT DISTINCT mp.mata_pelajaran_id, mp.nama, mp.kode, mp.deskripsi
            FROM mata_pelajaran mp
            JOIN jadwal j ON mp.mata_pelajaran_id = j.mata_pelajaran_id
            WHERE j.kelas_id IN ({})
            """.format(','.join('?' * len(kelas_ids))),
            kelas_ids
        )
        mata_pelajaran_list = cursor.fetchall()
    else:  # role == "guru"
        # Fetch all mata_pelajaran for guru
        cursor.execute("SELECT mata_pelajaran_id, nama, kode, deskripsi FROM mata_pelajaran")
        mata_pelajaran_list = cursor.fetchall()
    
    logger.info(f"Returning {len(mata_pelajaran_list)} mata pelajaran for user {current_user['user_id']}")
    
    return [
        MataPelajaranResponse(
            mata_pelajaran_id=mp[0],
            nama=mp[1],
            kode=mp[2],
            deskripsi=mp[3]
        ) for mp in mata_pelajaran_list
    ]