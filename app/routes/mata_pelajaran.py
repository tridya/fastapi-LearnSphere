# app/routes/mata_pelajaran.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.mata_pelajaran import MataPelajaranCreate, MataPelajaranResponse
from app.dependencies import get_db_connection, get_current_user
import sqlite3

router = APIRouter(prefix="/api/mata-pelajaran", tags=["mata_pelajaran"])

@router.post("/", response_model=MataPelajaranResponse)
async def api_create_mata_pelajaran(
    mata_pelajaran: MataPelajaranCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create subjects")
    
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO mata_pelajaran (nama, kode, deskripsi) VALUES (?, ?, ?)",
            (mata_pelajaran.nama, mata_pelajaran.kode, mata_pelajaran.deskripsi)
        )
        db.commit()
        cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (cursor.lastrowid,))
        new_mata_pelajaran = cursor.fetchone()
        if not new_mata_pelajaran:
            raise HTTPException(status_code=500, detail="Failed to retrieve newly created mata pelajaran")
        return new_mata_pelajaran
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Nama atau kode mata pelajaran sudah ada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
    