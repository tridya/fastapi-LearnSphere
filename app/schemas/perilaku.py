from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class PerilakuCreate(BaseModel):
    siswa_id: int
    guru_id: int
    deskripsi: str
    rating: Literal["Sangat Baik", "Baik", "Cukup", "Kurang", "Buruk"]

class PerilakuResponse(BaseModel):
    perilaku_id: int
    siswa_id: int
    guru_id: int
    deskripsi: str
    rating: Literal["Sangat Baik", "Baik", "Cukup", "Kurang", "Buruk"]
    tanggal: datetime

    class Config:
        from_attributes = True  # Changed from orm_mode