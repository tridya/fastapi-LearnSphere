# app/routes/perilaku.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.perilaku import PerilakuCreate, PerilakuResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3

router = APIRouter(prefix="/api/perilaku", tags=["perilaku"])

@router.post("/", response_model=PerilakuResponse)
async def api_create_perilaku(
    perilaku: PerilakuCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can record behavior")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (perilaku.siswa_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Siswa not found")
    
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'guru'", (perilaku.guru_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Guru not found")
    
    cursor.execute(
        "INSERT INTO perilaku (siswa_id, guru_id, deskripsi, rating) VALUES (?, ?, ?, ?)",
        (perilaku.siswa_id, perilaku.guru_id, perilaku.deskripsi, perilaku.rating)
    )
    db.commit()
    cursor.execute("SELECT * FROM perilaku WHERE perilaku_id = ?", (cursor.lastrowid,))
    new_perilaku = cursor.fetchone()
    if not new_perilaku:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created perilaku")
    return new_perilaku