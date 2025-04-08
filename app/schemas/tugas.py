from pydantic import BaseModel
from datetime import date

class TugasCreate(BaseModel):
    guru_id: int
    kelas_id: int
    deskripsi: str
    batas_waktu: date

class TugasResponse(BaseModel):
    task_id: int
    guru_id: int
    kelas_id: int
    deskripsi: str
    batas_waktu: date

    class Config:
        from_attributes = True  # Changed from orm_mode