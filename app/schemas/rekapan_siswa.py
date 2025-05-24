from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime
from .mata_pelajaran import MataPelajaranResponse
from .user import UserInDB

class RekapanSiswaCreate(BaseModel):
    siswa_id: int
    mata_pelajaran_id: int
    rating: Literal["Sangat Baik", "Baik", "Cukup", "Kurang", "Buruk"]
    catatan: Optional[str] = None

class RekapanSiswaResponse(BaseModel):
    report_id: int
    siswa_id: int
    guru_id: int
    mata_pelajaran_id: int
<<<<<<< HEAD
    rating: Literal["Sangat Baik", "Baik", "Cukup", "Kurang", "Buruk"]
=======
    rating: str
>>>>>>> origin/main
    catatan: Optional[str]
    tanggal: str

    class Config:
<<<<<<< HEAD
        from_attributes = True  # Changed from orm_mode
=======
        from_attributes = True

class StatusRekapanSiswa(BaseModel):
    siswa_id: int
    nama_siswa: str
    sudah_dibuat: bool
    rekapan: Optional[RekapanSiswaResponse] = None

class KelasResponse(BaseModel):
    kelas_id: int
    nama: str
>>>>>>> origin/main
