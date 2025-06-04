from fastapi import APIRouter, Depends, HTTPException
from typing import List
import sqlite3
from app.schemas.notifikasi import NotifikasiCreate, NotifikasiResponse
from app.dependencies import get_db_connection, get_current_user

router = APIRouter()

# Fungsi untuk mendapatkan daftar siswa dan orang tua berdasarkan kelas_id
def get_siswa_and_orang_tua_by_kelas(kelas_id: int, db: sqlite3.Connection):
    cursor = db.cursor()
    # Ambil semua siswa dalam kelas
    cursor.execute("SELECT siswa_id, orang_tua_id FROM siswa WHERE kelas_id = ?", (kelas_id,))
    result = cursor.fetchall()
    siswa_ids = [row["siswa_id"] for row in result if row["siswa_id"] is not None]
    orang_tua_ids = [row["orang_tua_id"] for row in result if row["orang_tua_id"] is not None]
    return siswa_ids, orang_tua_ids

@router.post("/", response_model=NotifikasiResponse)
async def create_notifikasi(
    notifikasi: NotifikasiCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create notifications")

    # Ambil kelas_id dari guru (diasumsikan guru hanya mengelola satu kelas)
    cursor = db.cursor()
    cursor.execute("SELECT kelas_id FROM users WHERE user_id = ? AND role = 'guru'", (current_user["user_id"],))
    kelas = cursor.fetchone()
    if not kelas:
        raise HTTPException(status_code=404, detail="Teacher's class not found")
    kelas_id = kelas["kelas_id"]

    # Ambil daftar siswa dan orang tua berdasarkan kelas_id
    siswa_ids, orang_tua_ids = get_siswa_and_orang_tua_by_kelas(kelas_id, db)

    # Jika ada siswa atau orang tua, buatkan notifikasi untuk masing-masing
    if not siswa_ids and not orang_tua_ids:
        raise HTTPException(status_code=404, detail="No students or parents found in this class")

    # Simpan notifikasi untuk setiap siswa dan orang tua
    for siswa_id in siswa_ids:
        for orang_tua_id in orang_tua_ids:
            cursor.execute(
                """
                INSERT INTO notifikasi (siswa_id, orang_tua_id, jenis, deskripsi, status, tanggal)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    siswa_id,
                    orang_tua_id,
                    notifikasi.jenis,
                    notifikasi.deskripsi,
                    notifikasi.status,
                    notifikasi.tanggal
                )
            )
    db.commit()
    notifikasi_id = cursor.lastrowid

    cursor.execute("SELECT * FROM notifikasi WHERE notifikasi_id = ?", (notifikasi_id,))
    result = cursor.fetchone()
    return dict(result)

# Endpoint lainnya tetap sama
@router.get("/guru", response_model=List[NotifikasiResponse])
async def get_notifikasi_guru(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can access this")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM notifikasi ORDER BY tanggal DESC")
    notifikasi_list = cursor.fetchall()
    return [dict(row) for row in notifikasi_list]

@router.put("/{notifikasi_id}", response_model=NotifikasiResponse)
async def update_notifikasi(
    notifikasi_id: int,
    notifikasi: NotifikasiCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can update notifications")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM notifikasi WHERE notifikasi_id = ?", (notifikasi_id,))
    existing_notifikasi = cursor.fetchone()
    if not existing_notifikasi:
        raise HTTPException(status_code=404, detail="Notification not found")

    cursor.execute(
        """
        UPDATE notifikasi
        SET siswa_id = ?, orang_tua_id = ?, jenis = ?, deskripsi = ?, status = ?, tanggal = ?
        WHERE notifikasi_id = ?
        """,
        (
            notifikasi.siswa_id,
            notifikasi.orang_tua_id,
            notifikasi.jenis,
            notifikasi.deskripsi,
            notifikasi.status,
            notifikasi.tanggal,
            notifikasi_id
        )
    )
    db.commit()

    cursor.execute("SELECT * FROM notifikasi WHERE notifikasi_id = ?", (notifikasi_id,))
    updated_notifikasi = cursor.fetchone()
    return dict(updated_notifikasi)

@router.delete("/{notifikasi_id}", response_model=dict)
async def delete_notifikasi(
    notifikasi_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can delete notifications")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM notifikasi WHERE notifikasi_id = ?", (notifikasi_id,))
    notifikasi = cursor.fetchone()
    if not notifikasi:
        raise HTTPException(status_code=404, detail="Notification not found")

    cursor.execute("DELETE FROM notifikasi WHERE notifikasi_id = ?", (notifikasi_id,))
    db.commit()
    return {"message": "Notification deleted successfully"}