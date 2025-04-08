from pydantic import BaseModel

class KelasCreate(BaseModel):
    nama_kelas: str
    wali_kelas_id: int

class KelasResponse(BaseModel):
    kelas_id: int
    nama_kelas: str
    wali_kelas_id: int

    class Config:
        from_attributes = True  # Changed from orm_mode