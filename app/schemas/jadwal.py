from pydantic import BaseModel
from typing import Literal

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

    class Config:
        from_attributes = True  # Diubah dari orm_mode