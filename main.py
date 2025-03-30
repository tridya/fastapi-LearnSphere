# fastapi-LearnSphere/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
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

# Initialize FastAPI app
app = FastAPI(
    title="LearnSphere API",
    description="API untuk aplikasi LearnSphere",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Add root route to display HTML page
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Initialize database on startup
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