from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.dependencies import get_db_connection, get_current_user
from app.database import init_db
from app.utils.security import hash_password, verify_password
from app.schemas import (
    UserCreate, UserInDB, UserLogin,
    KelasCreate, KelasResponse,
    SiswaCreate, SiswaResponse,
    AbsensiCreate, AbsensiResponse,
    JadwalCreate, JadwalResponse,
    PerilakuCreate, PerilakuResponse,
    NotifikasiCreate, NotifikasiResponse,
    TugasCreate, TugasResponse,
    RekapanSiswaCreate, RekapanSiswaResponse,
    MataPelajaranCreate, MataPelajaranResponse,
    Token
)
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.security import create_access_token
from datetime import timedelta
import sqlite3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="School Management Data Entry with API")

# Mount static files dan templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inisialisasi database saat startup
@app.on_event("startup")
def on_startup():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized.")

# Root (Redirect ke Register)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Register (Web)
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, message: str = None):
    return templates.TemplateResponse("register.html", {"request": request, "message": message})

@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    nama: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    try:
        logger.info(f"Registering user: {username}")
        hashed_password = hash_password(password)
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (nama, username, password, role) VALUES (?, ?, ?, ?)",
            (nama, username, hashed_password, role)
        )
        db.commit()
        logger.info(f"User {username} registered successfully")
        return templates.TemplateResponse("register.html", {"request": request, "message": "User registered successfully"})
    except sqlite3.IntegrityError:
        logger.warning(f"Username {username} already exists")
        return templates.TemplateResponse("register.html", {"request": request, "message": "Username already exists"})
    except Exception as e:
        logger.error(f"Error registering user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Store Kelas (Web)
@app.get("/store/kelas", response_class=HTMLResponse)
async def store_kelas_page(request: Request, message: str = None):
    return templates.TemplateResponse("store_kelas.html", {"request": request, "message": message})

@app.post("/store/kelas", response_class=HTMLResponse)
async def store_kelas(
    request: Request,
    nama_kelas: str = Form(...),
    wali_kelas_id: int = Form(...),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'guru'", (wali_kelas_id,))
    if not cursor.fetchone():
        return templates.TemplateResponse("store_kelas.html", {"request": request, "message": "Wali kelas not found or not a guru"})
    
    cursor.execute(
        "INSERT INTO kelas (nama_kelas, wali_kelas_id) VALUES (?, ?)",
        (nama_kelas, wali_kelas_id)
    )
    db.commit()
    return templates.TemplateResponse("store_kelas.html", {"request": request, "message": "Kelas stored successfully"})

# Store Mata Pelajaran (Web)
@app.get("/store/mata-pelajaran", response_class=HTMLResponse)
async def store_mata_pelajaran_page(request: Request, message: str = None):
    return templates.TemplateResponse("store_mata_pelajaran.html", {"request": request, "message": message})

@app.post("/store/mata-pelajaran", response_class=HTMLResponse)
async def store_mata_pelajaran(
    request: Request,
    nama: str = Form(...),
    kode: str = Form(None),
    deskripsi: str = Form(None),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO mata_pelajaran (nama, kode, deskripsi) VALUES (?, ?, ?)",
            (nama, kode, deskripsi)
        )
        db.commit()
        return templates.TemplateResponse("store_mata_pelajaran.html", {"request": request, "message": "Mata pelajaran stored successfully"})
    except sqlite3.IntegrityError:
        return templates.TemplateResponse("store_mata_pelajaran.html", {"request": request, "message": "Nama atau kode sudah ada"})

# Store Jadwal (Web)
@app.get("/store/jadwal", response_class=HTMLResponse)
async def store_jadwal_page(request: Request, message: str = None):
    return templates.TemplateResponse("store_jadwal.html", {"request": request, "message": message})

@app.post("/store/jadwal", response_class=HTMLResponse)
async def store_jadwal(
    request: Request,
    kelas_id: int = Form(...),
    hari: str = Form(...),
    jam_mulai: str = Form(...),
    jam_selesai: str = Form(...),
    mata_pelajaran_id: int = Form(...),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (kelas_id,))
    if not cursor.fetchone():
        return templates.TemplateResponse("store_jadwal.html", {"request": request, "message": "Kelas not found"})
    
    cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (mata_pelajaran_id,))
    if not cursor.fetchone():
        return templates.TemplateResponse("store_jadwal.html", {"request": request, "message": "Mata pelajaran not found"})
    
    cursor.execute(
        "INSERT INTO jadwal (kelas_id, hari, jam_mulai, jam_selesai, mata_pelajaran_id) VALUES (?, ?, ?, ?, ?)",
        (kelas_id, hari, jam_mulai, jam_selesai, mata_pelajaran_id)
    )
    db.commit()
    return templates.TemplateResponse("store_jadwal.html", {"request": request, "message": "Jadwal stored successfully"})

# API Endpoints (Untuk Aplikasi Mobile)

# Register API
@app.post("/api/register", response_model=UserInDB)
async def api_register_user(user: UserCreate, db: sqlite3.Connection = Depends(get_db_connection)):
    hashed_password = hash_password(user.password)
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (nama, username, password, role) VALUES (?, ?, ?, ?)",
        (user.nama, user.username, hashed_password, user.role)
    )
    db.commit()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (cursor.lastrowid,))
    return cursor.fetchone()

# Login API (Mengembalikan token)
@app.post("/api/login", response_model=Token)
async def api_login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db_connection)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (form_data.username,))
    db_user = cursor.fetchone()
    
    if not db_user or not verify_password(form_data.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Buat token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user["username"], "role": db_user["role"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint API yang Dilindungi

# Create Kelas (Hanya Guru)
@app.post("/api/kelas", response_model=KelasResponse)
async def api_create_kelas(
    kelas: KelasCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    # Hanya guru yang boleh membuat kelas
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create a class")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'guru'", (kelas.wali_kelas_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Wali kelas not found or not a guru")
    
    cursor.execute(
        "INSERT INTO kelas (nama_kelas, wali_kelas_id) VALUES (?, ?)",
        (kelas.nama_kelas, kelas.wali_kelas_id)
    )
    db.commit()
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (cursor.lastrowid,))
    return cursor.fetchone()

# Create Siswa (Hanya Guru)
@app.post("/api/siswa", response_model=SiswaResponse)
async def api_create_siswa(
    siswa: SiswaCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create a student")
    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO siswa (nama, kelas_id, orang_tua_id, kode_siswa) VALUES (?, ?, ?, ?)",
        (siswa.nama, siswa.kelas_id, siswa.orang_tua_id, siswa.kode_siswa)
    )
    db.commit()
    cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (cursor.lastrowid,))
    return cursor.fetchone()

# Store Absensi (Hanya Guru)
@app.post("/api/absensi", response_model=AbsensiResponse)
async def api_store_absensi(
    absensi: AbsensiCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can record attendance")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (absensi.siswa_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Siswa not found")
    
    cursor.execute(
        "INSERT INTO absensi (siswa_id, tanggal, status) VALUES (?, ?, ?)",
        (absensi.siswa_id, absensi.tanggal, absensi.status)
    )
    db.commit()
    cursor.execute("SELECT * FROM absensi WHERE absensi_id = ?", (cursor.lastrowid,))
    return cursor.fetchone()

# Create Jadwal (Hanya Guru)
@app.post("/api/jadwal", response_model=JadwalResponse)
async def api_create_jadwal(
    jadwal: JadwalCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create a schedule")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (jadwal.kelas_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Kelas not found")
    
    cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (jadwal.mata_pelajaran_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Mata pelajaran not found")
    
    cursor.execute(
        "INSERT INTO jadwal (kelas_id, hari, jam_mulai, jam_selesai, mata_pelajaran_id) VALUES (?, ?, ?, ?, ?)",
        (jadwal.kelas_id, jadwal.hari, jadwal.jam_mulai, jadwal.jam_selesai, jadwal.mata_pelajaran_id)
    )
    db.commit()
    cursor.execute("SELECT * FROM jadwal WHERE jadwal_id = ?", (cursor.lastrowid,))
    return cursor.fetchone()

# Create Perilaku (Hanya Guru)
@app.post("/api/perilaku", response_model=PerilakuResponse)
async def api_create_perilaku(
    perilaku: PerilakuCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can record behavior")
    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO perilaku (siswa_id, guru_id, deskripsi, rating) VALUES (?, ?, ?, ?)",
        (perilaku.siswa_id, perilaku.guru_id, perilaku.deskripsi, perilaku.rating)
    )
    db.commit()
    cursor.execute("SELECT * FROM perilaku WHERE perilaku_id = ?", (cursor.lastrowid,))
    return cursor.fetchone()

# Create Notifikasi (Hanya Guru)
@app.post("/api/notifikasi", response_model=NotifikasiResponse)
async def api_create_notifikasi(
    notifikasi: NotifikasiCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create notifications")
    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO notifikasi (siswa_id, orang_tua_id, jenis, deskripsi, status) VALUES (?, ?, ?, ?, ?)",
        (notifikasi.siswa_id, notifikasi.orang_tua_id, notifikasi.jenis, notifikasi.deskripsi, notifikasi.status)
    )
    db.commit()
    cursor.execute("SELECT * FROM notifikasi WHERE notifikasi_id = ?", (cursor.lastrowid,))
    return cursor.fetchone()

# Create Tugas (Hanya Guru)
@app.post("/api/tugas", response_model=TugasResponse)
async def api_create_tugas(
    tugas: TugasCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create tasks")
    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO tugas (guru_id, kelas_id, deskripsi, batas_waktu) VALUES (?, ?, ?, ?)",
        (tugas.guru_id, tugas.kelas_id, tugas.deskripsi, tugas.batas_waktu)
    )
    db.commit()
    cursor.execute("SELECT * FROM tugas WHERE task_id = ?", (cursor.lastrowid,))
    return cursor.fetchone()

# Create Rekapan Siswa (Hanya Guru)
@app.post("/api/rekapan-siswa", response_model=RekapanSiswaResponse)
async def api_create_rekapan_siswa(
    rekapan: RekapanSiswaCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create student reports")
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM siswa WHERE siswa_id = ?", (rekapan.siswa_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Siswa not found")
    
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'guru'", (rekapan.guru_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Guru not found")
    
    cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (rekapan.mata_pelajaran_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Mata pelajaran not found")
    
    cursor.execute(
        "INSERT INTO rekapan_siswa (siswa_id, guru_id, mata_pelajaran_id, rating, catatan) VALUES (?, ?, ?, ?, ?)",
        (rekapan.siswa_id, rekapan.guru_id, rekapan.mata_pelajaran_id, rekapan.rating, rekapan.catatan)
    )
    db.commit()
    cursor.execute("SELECT * FROM rekapan_siswa WHERE report_id = ?", (cursor.lastrowid,))
    return cursor.fetchone()

# Create Mata Pelajaran (Hanya Guru)
@app.post("/api/mata-pelajaran", response_model=MataPelajaranResponse)
async def api_create_mata_pelajaran(
    mata_pelajaran: MataPelajaranCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "guru":
        raise HTTPException(status_code=403, detail="Only teachers can create subjects")
    
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO mata_pelajaran (nama, kode, deskripsi) VALUES (?, ?, ?)",
            (mata_pelajaran.nama, mata_pelajaran.kode, mata_pelajaran.deskripsi)
        )
        db.commit()
        cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (cursor.lastrowid,))
        return cursor.fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Nama atau kode mata pelajaran sudah ada")