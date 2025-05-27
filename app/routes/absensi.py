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
    logger.info(f"Memulai api_store_absensi untuk absensi: {absensi}, user: {current_user}")
    if current_user["role"] != "guru":
        logger.error("User bukan guru")
        raise HTTPException(status_code=403, detail="Only teachers can record attendance")
    
    cursor = db.cursor()
    logger.info(f"Mencari siswa dengan siswa_id: {absensi.siswa_id}")
    cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (absensi.siswa_id,))
    siswa = cursor.fetchone()
    if not siswa:
        logger.error(f"Siswa tidak ditemukan untuk siswa_id: {absensi.siswa_id}")
        raise HTTPException(status_code=404, detail="Siswa not found")
    
    # Pastikan user adalah wali kelas dari kelas siswa
    logger.info(f"Memeriksa kelas dengan kelas_id: {siswa[2]} dan wali_kelas_id: {current_user['user_id']}")
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?", (siswa[2], current_user["user_id"]))
    kelas = cursor.fetchone()
    if not kelas:
        logger.error(f"User bukan wali kelas untuk kelas_id: {siswa[2]}")
        raise HTTPException(status_code=403, detail="You are not the class teacher of this student")
    
    # Cek apakah absensi sudah ada untuk siswa dan tanggal tersebut
    logger.info(f"Mencari absensi yang sudah ada untuk siswa_id: {absensi.siswa_id}, tanggal: {absensi.tanggal}")
    cursor.execute(
        "SELECT * FROM absensi WHERE siswa_id = ? AND tanggal = ?",
        (absensi.siswa_id, absensi.tanggal)
    )
    existing_absensi = cursor.fetchone()
    if existing_absensi:
        logger.info(f"Absensi ditemukan, memperbarui status ke: {absensi.status}")
        cursor.execute(
            "UPDATE absensi SET status = ? WHERE absensi_id = ?",
            (absensi.status, existing_absensi[0])
        )
        db.commit()
        cursor.execute("SELECT * FROM absensi WHERE absensi_id = ?", (existing_absensi[0],))
        updated_absensi = cursor.fetchone()
        logger.info(f"Absensi diperbarui: {updated_absensi}")
        return {
            "absensi_id": updated_absensi[0],
            "siswa_id": updated_absensi[1],
            "tanggal": updated_absensi[2],
            "status": updated_absensi[3]
        }
    
    logger.info("Membuat absensi baru")
    cursor.execute(
        "INSERT INTO absensi (siswa_id, tanggal, status) VALUES (?, ?, ?)",
        (absensi.siswa_id, absensi.tanggal, absensi.status)
    )
    db.commit()
    cursor.execute("SELECT * FROM absensi WHERE absensi_id = ?", (cursor.lastrowid,))
    new_absensi = cursor.fetchone()
    if not new_absensi:
        logger.error("Gagal mengambil absensi yang baru dibuat")
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created absensi")
    logger.info(f"Absensi baru dibuat: {new_absensi}")
    return {
        "absensi_id": new_absensi[0],
        "siswa_id": new_absensi[1],
        "tanggal": new_absensi[2],
        "status": new_absensi[3]
    }

@router.get("/kelas/{kelas_id}", response_model=List[AbsensiResponse])
async def get_absensi_by_class_and_date(
    kelas_id: int,
    tanggal: str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"Memulai get_absensi_by_class_and_date untuk kelas_id: {kelas_id}, tanggal: {tanggal}, user: {current_user}")
        
        if current_user["role"] != "guru":
            logger.error("User bukan guru")
            raise HTTPException(status_code=403, detail="Hanya guru yang dapat mengakses absensi")
        
        cursor = db.cursor()
        # Pastikan kelas ada dan user adalah wali kelas
        logger.info(f"Memeriksa kelas dengan kelas_id: {kelas_id} dan wali_kelas_id: {current_user['user_id']}")
        cursor.execute("SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?", (kelas_id, current_user["user_id"]))
        kelas = cursor.fetchone()
        logger.info(f"Hasil query kelas: {kelas}")
        if not kelas:
            logger.error(f"Kelas tidak ditemukan atau user bukan wali kelas untuk kelas_id: {kelas_id}")
            raise HTTPException(status_code=404, detail="Kelas tidak ditemukan atau Anda bukan wali kelas")
        
        # Konversi tanggal dari string ke string (karena di database bertipe TEXT)
        try:
            # Validasi format tanggal
            tanggal_date = datetime.strptime(tanggal, "%Y-%m-%d").date()
            tanggal_str = tanggal_date.strftime("%Y-%m-%d")  # Konversi ke string untuk query
            logger.info(f"Tanggal dikonversi ke: {tanggal_str}")
        except ValueError as e:
            logger.error(f"Format tanggal salah: {tanggal}, error: {str(e)}")
            raise HTTPException(status_code=400, detail="Format tanggal salah. Gunakan YYYY-MM-DD")
        
        # Ambil daftar siswa di kelas tersebut
        logger.info(f"Mengambil daftar siswa untuk kelas_id: {kelas_id}")
        cursor.execute("SELECT siswa_id FROM siswa WHERE kelas_id = ?", (kelas_id,))
        siswa_ids = [row[0] for row in cursor.fetchall()]
        logger.info(f"Ditemukan {len(siswa_ids)} siswa: {siswa_ids}")
        
        if not siswa_ids:
            logger.info(f"Tidak ada siswa ditemukan untuk kelas_id: {kelas_id}")
            return []  # Return empty list kalau nggak ada siswa
        
        # Ambil absensi untuk siswa-siswa tersebut pada tanggal yang diberikan
        query = "SELECT * FROM absensi WHERE siswa_id IN ({}) AND tanggal = ?".format(','.join(['?'] * len(siswa_ids)))
        params = siswa_ids + [tanggal_str]
        logger.info(f"Menjalankan query: {query} dengan params: {params}")
        
        cursor.execute(query, params)
        absensi_list = cursor.fetchall()
        logger.info(f"Hasil query absensi: {absensi_list}")
        
        # Konversi hasil query ke format AbsensiResponse
        absensi_response = [
            {
                "absensi_id": row[0],
                "siswa_id": row[1],
                "tanggal": row[2],
                "status": row[3]
            }
            for row in absensi_list
        ]
        
        logger.info(f"Absensi ditemukan: {len(absensi_response)} entri untuk kelas_id: {kelas_id}, tanggal: {tanggal}")
        return absensi_response if absensi_response else []
    
    except Exception as e:
        logger.error(f"Error saat mengambil absensi: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/siswa/{siswa_id}", response_model=List[AbsensiResponse])
async def get_absensi_by_student(
    siswa_id: int,
    start_date: str,
    end_date: str,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"Memulai get_absensi_by_student untuk siswa_id: {siswa_id}, start_date: {start_date}, end_date: {end_date}, user: {current_user}")
        
        if current_user["role"] != "orang_tua":
            logger.error("User bukan orang tua")
            raise HTTPException(status_code=403, detail="Hanya orang tua yang dapat mengakses absensi anak")
        
        cursor = db.cursor()
        # Pastikan siswa adalah anak dari orang tua yang login
        logger.info(f"Memeriksa siswa dengan siswa_id: {siswa_id} dan orang_tua_id: {current_user['user_id']}")
        cursor.execute("SELECT * FROM siswa WHERE siswa_id = ? AND orang_tua_id = ?", (siswa_id, current_user["user_id"]))
        siswa = cursor.fetchone()
        if not siswa:
            logger.error(f"Siswa tidak ditemukan atau bukan anak dari user untuk siswa_id: {siswa_id}")
            raise HTTPException(status_code=404, detail="Siswa tidak ditemukan atau Anda bukan orang tua dari siswa ini")
        
        # Validasi format tanggal
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            start_date_str = start_date_obj.strftime("%Y-%m-%d")
            end_date_str = end_date_obj.strftime("%Y-%m-%d")
            logger.info(f"Tanggal dikonversi: start_date={start_date_str}, end_date={end_date_str}")
        except ValueError as e:
            logger.error(f"Format tanggal salah: start_date={start_date}, end_date={end_date}, error: {str(e)}")
            raise HTTPException(status_code=400, detail="Format tanggal salah. Gunakan YYYY-MM-DD")
        
        # Ambil absensi untuk siswa tersebut dalam rentang tanggal
        logger.info(f"Mengambil absensi untuk siswa_id: {siswa_id} dari {start_date_str} hingga {end_date_str}")
        cursor.execute(
            "SELECT * FROM absensi WHERE siswa_id = ? AND tanggal BETWEEN ? AND ?",
            (siswa_id, start_date_str, end_date_str)
        )
        absensi_list = cursor.fetchall()
        logger.info(f"Hasil query absensi: {absensi_list}")
        
        # Konversi hasil query ke format AbsensiResponse
        absensi_response = [
            {
                "absensi_id": row[0],
                "siswa_id": row[1],
                "tanggal": row[2],
                "status": row[3]
            }
            for row in absensi_list
        ]
        
        logger.info(f"Absensi ditemukan: {len(absensi_response)} entri untuk siswa_id: {siswa_id}")
        return absensi_response if absensi_response else []
    
    except Exception as e:
        logger.error(f"Error saat mengambil absensi: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
