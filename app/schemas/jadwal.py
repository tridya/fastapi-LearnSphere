from pydantic import BaseModel
from typing import Literal, Optional
from app.schemas.mata_pelajaran import MataPelajaranResponse

class WaliKelasResponse(BaseModel):
    user_id: int
    nama: str
    username: str
    role: str

    class Config:
        from_attributes = True

class JadwalBase(BaseModel):
    kelas_id: int
    hari: Literal["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
    jam_mulai: str
    jam_selesai: str
    mata_pelajaran_id: int

class JadwalCreate(JadwalBase):
    pass

class JadwalResponse(JadwalBase):
    jadwal_id: int
    mata_pelajaran: MataPelajaranResponse
    wali_kelas: WaliKelasResponse  # Gunakan skema baru

    class Config:
        from_attributes = True