from sqlalchemy import Column, Integer, String, Time, ForeignKey, Enum
from app.database import Base

class Jadwal(Base):
    __tablename__ = "jadwal"
    
    jadwal_id = Column(Integer, primary_key=True, index=True)
    kelas_id = Column(Integer, ForeignKey("kelas.kelas_id", ondelete="CASCADE"), nullable=False)
    hari = Column(Enum("Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", name="hari"), nullable=False)
    jam_mulai = Column(Time, nullable=False)
    jam_selesai = Column(Time, nullable=False)
    mata_pelajaran_id = Column(Integer, ForeignKey("mata_pelajaran.mata_pelajaran_id", ondelete="RESTRICT"), nullable=False)