from pydantic import BaseModel
from typing import Optional

class SiswaCreate(BaseModel):
    nama: str
    kelas_id: int
    orang_tua_id: Optional[int] = None
    kode_siswa: Optional[str] = None

class SiswaResponse(BaseModel):
    siswa_id: int
    nama: str
    kelas_id: int
    orang_tua_id: Optional[int]
    kode_siswa: Optional[str]

    class Config:
        orm_mode = True