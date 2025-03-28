from pydantic import BaseModel
from typing import Literal
from datetime import date

class AbsensiCreate(BaseModel):
    siswa_id: int
    tanggal: date
    status: Literal["Hadir", "Izin", "Sakit", "Alpa"]

class AbsensiResponse(BaseModel):
    absensi_id: int
    siswa_id: int
    tanggal: date
    status: Literal["Hadir", "Izin", "Sakit", "Alpa"]

    class Config:
        orm_mode = True