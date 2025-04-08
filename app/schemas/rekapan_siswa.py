from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class RekapanSiswaCreate(BaseModel):
    siswa_id: int
    guru_id: int
    mata_pelajaran_id: int  # Diubah dari mata_pelajaran
    rating: Literal["Sangat Baik", "Baik", "Cukup", "Kurang", "Buruk"]
    catatan: Optional[str] = None

class RekapanSiswaResponse(BaseModel):
    report_id: int
    siswa_id: int
    guru_id: int
    mata_pelajaran_id: int
    rating: Literal["Sangat Baik", "Baik", "Cukup", "Kurang", "Buruk"]
    catatan: Optional[str]
    tanggal: datetime

    class Config:
        from_attributes = True  # Changed from orm_mode