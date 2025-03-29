# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.routes import (
    auth_router,
    kelas_router,
    siswa_router,
    absensi_router,
    jadwal_router,
    perilaku_router,
    notifikasi_router,
    tugas_router,
    rekapan_siswa_router,
    mata_pelajaran_router,
    user_router,
    web_router
)
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LeanSphereAPI")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inisialisasi database saat startup
@app.on_event("startup")
async def on_startup():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized.")

# Include routers
app.include_router(auth_router)
app.include_router(kelas_router)
app.include_router(siswa_router)
app.include_router(absensi_router)
app.include_router(jadwal_router)
app.include_router(perilaku_router)
app.include_router(notifikasi_router)
app.include_router(tugas_router)
app.include_router(rekapan_siswa_router)
app.include_router(mata_pelajaran_router)
app.include_router(user_router)
app.include_router(web_router)