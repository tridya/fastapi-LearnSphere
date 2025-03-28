from sqlalchemy import Column, Integer, String
from app.database import Base

class MataPelajaran(Base):
    __tablename__ = "mata_pelajaran"
    
    mata_pelajaran_id = Column(Integer, primary_key=True, index=True)
    nama = Column(String, unique=True, nullable=False)
    kode = Column(String, unique=True, nullable=True)
    deskripsi = Column(String, nullable=True)