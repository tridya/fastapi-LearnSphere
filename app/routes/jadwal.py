from fastapi import APIRouter, Depends, HTTPException
from app.schemas.jadwal import JadwalCreate, JadwalResponse
from app.schemas.kelas import KelasResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3
from typing import List

router = APIRouter(prefix="/api/jadwal", tags=["jadwal"])

# Fungsi untuk menormalkan format waktu ke HH:MM
def normalize_time(time_str: str) -> str:
    if len(time_str) > 5 and time_str[5] == ':':
        return time_str[:5]
    return time_str

@router.get("/guru/kelas", response_model=List[KelasResponse])
async def get_kelas_by_guru(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can access their classes")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM kelas WHERE wali_kelas_id = ?", (current_user["user_id"],))
    kelas_list = cursor.fetchall()
    
    result = []
    for kelas in kelas_list:
        result.append({
            "kelas_id": kelas[0],
            "nama_kelas": kelas[1],
            "wali_kelas_id": kelas[2]
        })
    return result

@router.post("/", response_model=JadwalResponse)
async def api_create_jadwal(
    jadwal: JadwalCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create a schedule")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?", (jadwal.kelas_id, current_user["user_id"]))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Kelas not found or you are not the class teacher")
    
    cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (jadwal.mata_pelajaran_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Mata pelajaran not found")
    
    jam_mulai = normalize_time(jadwal.jam_mulai)
    jam_selesai = normalize_time(jadwal.jam_selesai)
    
    cursor.execute(
        "INSERT INTO jadwal (kelas_id, hari, jam_mulai, jam_selesai, mata_pelajaran_id) VALUES (?, ?, ?, ?, ?)",
        (jadwal.kelas_id, jadwal.hari, jam_mulai, jam_selesai, jadwal.mata_pelajaran_id)
    )
    db.commit()
    cursor.execute("SELECT * FROM jadwal WHERE jadwal_id = ?", (cursor.lastrowid,))
    new_jadwal = cursor.fetchone()
    if not new_jadwal:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created jadwal")
    
    cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (new_jadwal[5],))
    mata_pelajaran = cursor.fetchone()
    
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (new_jadwal[1],))
    kelas = cursor.fetchone()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (kelas[2],))
    wali_kelas = cursor.fetchone()
    
    return {
        "jadwal_id": new_jadwal[0],
        "kelas_id": new_jadwal[1],
        "hari": new_jadwal[2],
        "jam_mulai": new_jadwal[3],
        "jam_selesai": new_jadwal[4],
        "mata_pelajaran_id": new_jadwal[5],
        "mata_pelajaran": {
            "mata_pelajaran_id": mata_pelajaran[0],
            "nama": mata_pelajaran[1],
            "kode": mata_pelajaran[2],
            "deskripsi": mata_pelajaran[3]
        } if mata_pelajaran else None,
        "wali_kelas": {
            "user_id": wali_kelas[0],
            "nama": wali_kelas[1],
            "username": wali_kelas[2],
            "role": wali_kelas[3]
        } if wali_kelas else None
    }

@router.put("/{jadwal_id}", response_model=JadwalResponse)
async def update_jadwal(
    jadwal_id: int,
    jadwal: JadwalCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can update a schedule")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM jadwal WHERE jadwal_id = ?", (jadwal_id,))
    existing_jadwal = cursor.fetchone()
    if not existing_jadwal:
        raise HTTPException(status_code=404, detail="Jadwal not found")
    
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?", (jadwal.kelas_id, current_user["user_id"]))
    if not cursor.fetchone():
        raise HTTPException(status_code=403, detail="Kelas not found or you are not the class teacher")
    
    cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (jadwal.mata_pelajaran_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Mata pelajaran not found")
    
    jam_mulai = normalize_time(jadwal.jam_mulai)
    jam_selesai = normalize_time(jadwal.jam_selesai)
    
    cursor.execute(
        """
        UPDATE jadwal 
        SET kelas_id = ?, hari = ?, jam_mulai = ?, jam_selesai = ?, mata_pelajaran_id = ?
        WHERE jadwal_id = ?
        """,
        (jadwal.kelas_id, jadwal.hari, jam_mulai, jam_selesai, jadwal.mata_pelajaran_id, jadwal_id)
    )
    db.commit()
    
    cursor.execute("SELECT * FROM jadwal WHERE jadwal_id = ?", (jadwal_id,))
    updated_jadwal = cursor.fetchone()
    if not updated_jadwal:
        raise HTTPException(status_code=500, detail="Failed to retrieve updated jadwal")
    
    cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (updated_jadwal[5],))
    mata_pelajaran = cursor.fetchone()
    
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (updated_jadwal[1],))
    kelas = cursor.fetchone()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (kelas[2],))
    wali_kelas = cursor.fetchone()
    
    return {
        "jadwal_id": updated_jadwal[0],
        "kelas_id": updated_jadwal[1],
        "hari": updated_jadwal[2],
        "jam_mulai": updated_jadwal[3],
        "jam_selesai": updated_jadwal[4],
        "mata_pelajaran_id": updated_jadwal[5],
        "mata_pelajaran": {
            "mata_pelajaran_id": mata_pelajaran[0],
            "nama": mata_pelajaran[1],
            "kode": mata_pelajaran[2],
            "deskripsi": mata_pelajaran[3]
        } if mata_pelajaran else None,
        "wali_kelas": {
            "user_id": wali_kelas[0],
            "nama": wali_kelas[1],
            "username": wali_kelas[2],
            "role": wali_kelas[3]
        } if wali_kelas else None
    }

@router.delete("/{jadwal_id}", response_model=dict)
async def delete_jadwal(
    jadwal_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can delete a schedule")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM jadwal WHERE jadwal_id = ?", (jadwal_id,))
    existing_jadwal = cursor.fetchone()
    if not existing_jadwal:
        raise HTTPException(status_code=404, detail="Jadwal not found")
    
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?", (existing_jadwal[1], current_user["user_id"]))
    if not cursor.fetchone():
        raise HTTPException(status_code=403, detail="You are not the class teacher of this schedule")
    
    cursor.execute("DELETE FROM jadwal WHERE jadwal_id = ?", (jadwal_id,))
    db.commit()
    
    return {"message": "Jadwal successfully deleted"}

@router.get("/kelas/{kelas_id}/current", response_model=List[JadwalResponse])
async def get_current_jadwal_by_kelas(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?", (kelas_id, current_user["user_id"]))
    if not cursor.fetchone():
        raise HTTPException(status_code=403, detail="Kelas not found or you are not the class teacher")
    
    from datetime import datetime
    current_time = datetime.now()
    current_day = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][current_time.weekday()]
    current_time_str = current_time.strftime("%H:%M")
    
    cursor.execute(
        """
        SELECT * FROM jadwal
        WHERE kelas_id = ? AND hari = ? AND jam_mulai <= ? AND jam_selesai >= ?
        """,
        (kelas_id, current_day, current_time_str, current_time_str)
    )
    jadwal_list = cursor.fetchall()
    
    result = []
    for jadwal in jadwal_list:
        cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (jadwal[5],))
        mata_pelajaran = cursor.fetchone()
        
        cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (jadwal[1],))
        kelas = cursor.fetchone()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (kelas[2],))
        wali_kelas = cursor.fetchone()
        
        result.append({
            "jadwal_id": jadwal[0],
            "kelas_id": jadwal[1],
            "hari": jadwal[2],
            "jam_mulai": jadwal[3],
            "jam_selesai": jadwal[4],
            "mata_pelajaran_id": jadwal[5],
            "mata_pelajaran": {
                "mata_pelajaran_id": mata_pelajaran[0],
                "nama": mata_pelajaran[1],
                "kode": mata_pelajaran[2],
                "deskripsi": mata_pelajaran[3]
            } if mata_pelajaran else None,
            "wali_kelas": {
                "user_id": wali_kelas[0],
                "nama": wali_kelas[1],
                "username": wali_kelas[2],
                "role": wali_kelas[3]
            } if wali_kelas else None
        })
    return result

@router.get("/kelas/{kelas_id}", response_model=List[JadwalResponse])
async def get_all_jadwal_by_kelas(
    kelas_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?", (kelas_id, current_user["user_id"]))
    if not cursor.fetchone():
        raise HTTPException(status_code=403, detail="Kelas not found or you are not the class teacher")
    
    cursor.execute("SELECT * FROM jadwal WHERE kelas_id = ?", (kelas_id,))
    jadwal_list = cursor.fetchall()
    
    result = []
    for jadwal in jadwal_list:
        cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (jadwal[5],))
        mata_pelajaran = cursor.fetchone()
        
        cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (jadwal[1],))
        kelas = cursor.fetchone()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (kelas[2],))
        wali_kelas = cursor.fetchone()
        
        result.append({
            "jadwal_id": jadwal[0],
            "kelas_id": jadwal[1],
            "hari": jadwal[2],
            "jam_mulai": jadwal[3],
            "jam_selesai": jadwal[4],
            "mata_pelajaran_id": jadwal[5],
            "mata_pelajaran": {
                "mata_pelajaran_id": mata_pelajaran[0],
                "nama": mata_pelajaran[1],
                "kode": mata_pelajaran[2],
                "deskripsi": mata_pelajaran[3]
            } if mata_pelajaran else None,
            "wali_kelas": {
                "user_id": wali_kelas[0],
                "nama": wali_kelas[1],
                "username": wali_kelas[2],
                "role": wali_kelas[3]
            } if wali_kelas else None
        })
    return result