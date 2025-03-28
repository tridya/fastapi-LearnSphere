from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class Siswa(Base):
    __tablename__ = "siswa"
    
    siswa_id = Column(Integer, primary_key=True, index=True)
    nama = Column(String, nullable=False)
    kelas_id = Column(Integer, ForeignKey("kelas.kelas_id", ondelete="CASCADE"), nullable=False)
    orang_tua_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    kode_siswa = Column(String, unique=True, nullable=True)