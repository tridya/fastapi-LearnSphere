from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_db_connection, get_templates
from app.utils.security import hash_password, verify_password, create_access_token
import sqlite3
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web"])

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    logger.info(f"Accessed root with method: {request.method}")
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, message: str = None, templates: Jinja2Templates = Depends(get_templates)):
    logger.info(f"Accessed login page with method: {request.method}")
    return templates.TemplateResponse("login.html", {"request": request, "message": message})

@router.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info(f"Login attempt for username: {username} with method: {request.method}")
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        db_user = cursor.fetchone()

        if not db_user or not verify_password(password, db_user["password"]):
            logger.warning(f"Login failed for username: {username}")
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "message": "Invalid username or password"}
            )

        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": db_user["username"], "role": db_user["role"]},
            expires_delta=access_token_expires
        )

        response = RedirectResponse(url="/register", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        logger.info(f"User {username} logged in successfully")
        return response

    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "An error occurred during login"}
        )

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, message: str = None, templates: Jinja2Templates = Depends(get_templates)):
    logger.info(f"Accessed register page with method: {request.method}")
    return templates.TemplateResponse("register.html", {"request": request, "message": message})

@router.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    nama: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info(f"Register attempt for username: {username} with method: {request.method}")
    try:
        if role not in ["guru", "orang_tua"]:
            return templates.TemplateResponse(
                "register.html", {"request": request, "message": "Invalid role. Must be 'guru' or 'orang_tua'"}
            )
        
        hashed_password = hash_password(password)
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (nama, username, password, role) VALUES (?, ?, ?, ?)",
            (nama, username, hashed_password, role)
        )
        db.commit()
        logger.info(f"User {username} registered successfully")
        return templates.TemplateResponse(
            "register.html", {"request": request, "message": "User registered successfully"}
        )
    except sqlite3.IntegrityError:
        logger.warning(f"Username {username} already exists")
        return templates.TemplateResponse(
            "register.html", {"request": request, "message": "Username already exists"}
        )
    except Exception as e:
        logger.error(f"Error registering user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/store/kelas", response_class=HTMLResponse)
async def store_kelas_page(request: Request, message: str = None, templates: Jinja2Templates = Depends(get_templates)):
    logger.info(f"Accessed store/kelas with method: {request.method}")
    return templates.TemplateResponse("store_kelas.html", {"request": request, "message": message})

@router.post("/store/kelas", response_class=HTMLResponse)
async def store_kelas(
    request: Request,
    nama_kelas: str = Form(...),
    wali_kelas_id: int = Form(...),
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info(f"Store kelas attempt with method: {request.method}")
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'guru'", (wali_kelas_id,))
        if not cursor.fetchone():
            return templates.TemplateResponse(
                "store_kelas.html", {"request": request, "message": "Wali kelas not found or not a guru"}
            )
        
        cursor.execute(
            "INSERT INTO kelas (nama_kelas, wali_kelas_id) VALUES (?, ?)",
            (nama_kelas, wali_kelas_id)
        )
        db.commit()
        return templates.TemplateResponse(
            "store_kelas.html", {"request": request, "message": "Kelas stored successfully"}
        )
    except Exception as e:
        logger.error(f"Error storing kelas: {str(e)}")
        return templates.TemplateResponse(
            "store_kelas.html", {"request": request, "message": "Error storing kelas"}
        )

# Rute lainnya (store/mata-pelajaran, store/jadwal) tetap sama, tambahkan logging jika perlu
@router.get("/store/mata-pelajaran", response_class=HTMLResponse)
async def store_mata_pelajaran_page(request: Request, message: str = None, templates: Jinja2Templates = Depends(get_templates)):
    logger.info(f"Accessed store/mata-pelajaran with method: {request.method}")
    return templates.TemplateResponse("store_mata_pelajaran.html", {"request": request, "message": message})

@router.post("/store/mata-pelajaran", response_class=HTMLResponse)
async def store_mata_pelajaran(
    request: Request,
    nama: str = Form(...),
    kode: str = Form(None),
    deskripsi: str = Form(None),
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info(f"Store mata-pelajaran attempt with method: {request.method}")
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO mata_pelajaran (nama, kode, deskripsi) VALUES (?, ?, ?)",
            (nama, kode, deskripsi)
        )
        db.commit()
        return templates.TemplateResponse(
            "store_mata_pelajaran.html", {"request": request, "message": "Mata pelajaran stored successfully"}
        )
    except sqlite3.IntegrityError:
        return templates.TemplateResponse(
            "store_mata_pelajaran.html", {"request": request, "message": "Nama atau kode sudah ada"}
        )
    except Exception as e:
        logger.error(f"Error storing mata pelajaran: {str(e)}")
        return templates.TemplateResponse(
            "store_mata_pelajaran.html", {"request": request, "message": "Error storing mata pelajaran"}
        )

@router.get("/store/jadwal", response_class=HTMLResponse)
async def store_jadwal_page(request: Request, message: str = None, templates: Jinja2Templates = Depends(get_templates)):
    logger.info(f"Accessed store/jadwal with method: {request.method}")
    return templates.TemplateResponse("store_jadwal.html", {"request": request, "message": message})

@router.post("/store/jadwal", response_class=HTMLResponse)
async def store_jadwal(
    request: Request,
    kelas_id: int = Form(...),
    hari: str = Form(...),
    jam_mulai: str = Form(...),
    jam_selesai: str = Form(...),
    mata_pelajaran_id: int = Form(...),
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info(f"Store jadwal attempt with method: {request.method}")
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (kelas_id,))
        if not cursor.fetchone():
            return templates.TemplateResponse(
                "store_jadwal.html", {"request": request, "message": "Kelas not found"}
            )
        
        cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (mata_pelajaran_id,))
        if not cursor.fetchone():
            return templates.TemplateResponse(
                "store_jadwal.html", {"request": request, "message": "Mata pelajaran not found"}
            )
        
        cursor.execute(
            "INSERT INTO jadwal (kelas_id, hari, jam_mulai, jam_selesai, mata_pelajaran_id) VALUES (?, ?, ?, ?, ?)",
            (kelas_id, hari, jam_mulai, jam_selesai, mata_pelajaran_id)
        )
        db.commit()
        return templates.TemplateResponse(
            "store_jadwal.html", {"request": request, "message": "Jadwal stored successfully"}
        )
    except Exception as e:
        logger.error(f"Error storing jadwal: {str(e)}")
        return templates.TemplateResponse(
            "store_jadwal.html", {"request": request, "message": "Error storing jadwal"}
        )