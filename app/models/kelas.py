from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class Kelas(Base):
    __tablename__ = "kelas"
    
    kelas_id = Column(Integer, primary_key=True, index=True)
    nama_kelas = Column(String, nullable=False)
    wali_kelas_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)