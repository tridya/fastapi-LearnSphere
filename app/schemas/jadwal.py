from pydantic import BaseModel
from typing import Literal
from app.schemas.mata_pelajaran import MataPelajaranResponse
from app.schemas.user import UserInDB

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
    wali_kelas: UserInDB

    class Config:
        from_attributes = True