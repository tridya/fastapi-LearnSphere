from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class NotifikasiCreate(BaseModel):
    siswa_id: int
    orang_tua_id: int
    jenis: Literal["Tugas", "Perilaku", "Absensi", "Pengumuman"]
    deskripsi: str
    status: Literal["Belum Dibaca", "Dibaca"] = "Belum Dibaca"

class NotifikasiResponse(BaseModel):
    notifikasi_id: int
    siswa_id: int
    orang_tua_id: int
    jenis: Literal["Tugas", "Perilaku", "Absensi", "Pengumuman"]
    deskripsi: str
    status: Literal["Belum Dibaca", "Dibaca"]
    tanggal: datetime

    class Config:
        orm_mode = True