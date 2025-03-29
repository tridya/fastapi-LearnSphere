# app/routes/tugas.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.tugas import TugasCreate, TugasResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3

router = APIRouter(prefix="/api/tugas", tags=["tugas"])

@router.post("/", response_model=TugasResponse)
async def api_create_tugas(
    tugas: TugasCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create tasks")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'guru'", (tugas.guru_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Guru not found")
    
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (tugas.kelas_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Kelas not found")
    
    cursor.execute(
        "INSERT INTO tugas (guru_id, kelas_id, deskripsi, batas_waktu) VALUES (?, ?, ?, ?)",
        (tugas.guru_id, tugas.kelas_id, tugas.deskripsi, tugas.batas_waktu)
    )
    db.commit()
    cursor.execute("SELECT * FROM tugas WHERE task_id = ?", (cursor.lastrowid,))
    new_tugas = cursor.fetchone()
    if not new_tugas:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created tugas")
    return new_tugas