from pydantic import BaseModel
from typing import Optional

class MataPelajaranBase(BaseModel):
    nama: str
    kode: Optional[str] = None
    deskripsi: Optional[str] = None

class MataPelajaranCreate(MataPelajaranBase):
    pass

class MataPelajaranResponse(MataPelajaranBase):
    mata_pelajaran_id: int

    class Config:
        from_attributes = True  # Diubah dari orm_mode