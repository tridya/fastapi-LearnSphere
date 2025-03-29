# app/routes/__init__.py
from .auth import router as auth_router
from .kelas import router as kelas_router
from .siswa import router as siswa_router
from .absensi import router as absensi_router
from .jadwal import router as jadwal_router
from .perilaku import router as perilaku_router
from .notifikasi import router as notifikasi_router
from .tugas import router as tugas_router
from .rekapan_siswa import router as rekapan_siswa_router
from .mata_pelajaran import router as mata_pelajaran_router
from .user import router as user_router
from .web import router as web_router