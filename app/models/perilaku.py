from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base

class Perilaku(Base):
    __tablename__ = "perilaku"
    
    perilaku_id = Column(Integer, primary_key=True, index=True)
    siswa_id = Column(Integer, ForeignKey("siswa.siswa_id", ondelete="CASCADE"), nullable=False)
    guru_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    deskripsi = Column(String, nullable=False)
    rating = Column(Enum("Sangat Baik", "Baik", "Cukup", "Kurang", "Buruk", name="rating"), nullable=False)
    tanggal = Column(DateTime, default=func.now())