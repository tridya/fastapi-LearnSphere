# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.routes import (
    absensi_router,
    auth_router,
    jadwal_router,
    kelas_router,
    mata_pelajaran_router,
    notifikasi_router,
    perilaku_router,
    rekapan_siswa_router,
    siswa_router,
    tugas_router,
    user_router,
    web_router,
)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(absensi_router)
app.include_router(auth_router)
app.include_router(jadwal_router)
app.include_router(kelas_router)
app.include_router(mata_pelajaran_router)
app.include_router(notifikasi_router)
app.include_router(perilaku_router)
app.include_router(rekapan_siswa_router)
app.include_router(siswa_router)
app.include_router(tugas_router)
app.include_router(user_router)
app.include_router(web_router)

@app.on_event("startup")
async def startup_event():
    init_db()