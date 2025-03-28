from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base

class Notifikasi(Base):
    __tablename__ = "notifikasi"
    
    notifikasi_id = Column(Integer, primary_key=True, index=True)
    siswa_id = Column(Integer, ForeignKey("siswa.siswa_id", ondelete="CASCADE"), nullable=False)
    orang_tua_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    jenis = Column(Enum("Tugas", "Perilaku", "Absensi", "Pengumuman", name="notifikasi_jenis"), nullable=False)
    deskripsi = Column(String, nullable=False)
    status = Column(Enum("Belum Dibaca", "Dibaca", name="notifikasi_status"), default="Belum Dibaca")
    tanggal = Column(DateTime, default=func.now())