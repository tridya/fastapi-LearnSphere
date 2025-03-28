from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base

class RekapanSiswa(Base):
    __tablename__ = "rekapan_siswa"
    
    report_id = Column(Integer, primary_key=True, index=True)
    siswa_id = Column(Integer, ForeignKey("siswa.siswa_id", ondelete="CASCADE"), nullable=False)
    guru_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    mata_pelajaran_id = Column(Integer, ForeignKey("mata_pelajaran.mata_pelajaran_id", ondelete="RESTRICT"), nullable=False)
    rating = Column(Enum("Sangat Baik", "Baik", "Cukup", "Kurang", "Buruk", name="rating"), nullable=False)
    catatan = Column(String, nullable=True)
    tanggal = Column(DateTime, default=func.now())