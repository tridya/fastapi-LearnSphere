from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum
from app.database import Base

class Absensi(Base):
    __tablename__ = "absensi"
    
    absensi_id = Column(Integer, primary_key=True, index=True)
    siswa_id = Column(Integer, ForeignKey("siswa.siswa_id", ondelete="CASCADE"), nullable=False)
    tanggal = Column(Date, nullable=False)
    status = Column(Enum("Hadir", "Izin", "Sakit", "Alpa", name="absensi_status"), nullable=False)