from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.database import Base

class Tugas(Base):
    __tablename__ = "tugas"
    
    task_id = Column(Integer, primary_key=True, index=True)
    guru_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    kelas_id = Column(Integer, ForeignKey("kelas.kelas_id", ondelete="CASCADE"), nullable=False)
    deskripsi = Column(String, nullable=False)
    batas_waktu = Column(Date, nullable=False)