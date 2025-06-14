# app/routes/web.py
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
async def home(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    return templates.TemplateResponse("landingpage.html", {"request": request})

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
            logger.warning(f"Invalid role {role} for username: {username}")
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "message": "Invalid role. Must be 'guru' or 'orang_tua'"}
            )
        
        hashed_password = hash_password(password)
        
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (nama, username, password, role) VALUES (?, ?, ?, ?)",
            (nama, username, hashed_password, role)
        )
        db.commit()
        
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        new_user = cursor.fetchone()
        if not new_user:
            logger.error(f"Failed to retrieve new user {username} after insertion")
            raise HTTPException(status_code=500, detail="Failed to retrieve new user")
        
        logger.info(f"User {username} registered successfully with ID: {new_user['user_id']}")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "message": f"User {username} registered successfully!"}
        )
    
    except sqlite3.IntegrityError:
        logger.warning(f"Username {username} already exists")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "message": "Username already exists"}
        )
    except Exception as e:
        logger.error(f"Error registering user {username}: {str(e)}")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "message": f"Error: {str(e)}"}
        )

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    return templates.TemplateResponse("login.html", {"request": request})

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

        response = RedirectResponse(url="/dashboard/siswa", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        logger.info(f"User {username} logged in successfully")
        return response

    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "An error occurred during login"}
        )

@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    logger.info("User logged out")
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response

# Siswa Routes
@router.get("/dashboard/siswa", response_class=HTMLResponse)
async def siswa_page(
    request: Request,
    kelas_id: int = None,
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info(f"Accessed siswa page with kelas_id: {kelas_id}")
    try:
        cursor = db.cursor()
        
        cursor.execute("SELECT kelas_id, nama_kelas FROM kelas")
        kelas_list = cursor.fetchall()
        
        if kelas_id:
            cursor.execute("SELECT s.*, k.nama_kelas FROM siswa s JOIN kelas k ON s.kelas_id = k.kelas_id WHERE s.kelas_id = ?", (kelas_id,))
        else:
            cursor.execute("SELECT s.*, k.nama_kelas FROM siswa s JOIN kelas k ON s.kelas_id = k.kelas_id")
        siswa_list = cursor.fetchall()
        
        cursor.execute("SELECT user_id, nama FROM users WHERE role = 'orang_tua'")
        orang_tua_list = cursor.fetchall()
        
        return templates.TemplateResponse(
            "siswa.html",
            {
                "request": request,
                "siswa_list": siswa_list,
                "kelas_list": kelas_list,
                "orang_tua_list": orang_tua_list,
                "selected_kelas_id": kelas_id
            }
        )
    except Exception as e:
        logger.error(f"Error loading siswa page: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading siswa page: {str(e)}")

@router.post("/dashboard/siswa/add", response_class=HTMLResponse)
async def add_siswa(
    request: Request,
    nama: str = Form(...),
    kelas_id: int = Form(...),
    orang_tua_id: int = Form(None),
    kode_siswa: str = Form(None),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    logger.info(f"Adding siswa: {nama}")
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO siswa (nama, kelas_id, orang_tua_id, kode_siswa) VALUES (?, ?, ?, ?)",
            (nama, kelas_id, orang_tua_id, kode_siswa)
        )
        db.commit()
        return RedirectResponse(url=f"/dashboard/siswa?kelas_id={kelas_id}", status_code=303)
    except Exception as e:
        logger.error(f"Error adding siswa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding siswa: {str(e)}")

@router.post("/dashboard/siswa/update/{siswa_id}", response_class=HTMLResponse)
async def update_siswa(
    siswa_id: int,
    request: Request,
    nama: str = Form(...),
    kelas_id: int = Form(...),
    orang_tua_id: int = Form(None),
    kode_siswa: str = Form(None),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    logger.info(f"Updating siswa ID: {siswa_id}")
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE siswa SET nama = ?, kelas_id = ?, orang_tua_id = ?, kode_siswa = ? WHERE siswa_id = ?",
            (nama, kelas_id, orang_tua_id, kode_siswa, siswa_id)
        )
        db.commit()
        return RedirectResponse(url=f"/dashboard/siswa?kelas_id={kelas_id}", status_code=303)
    except Exception as e:
        logger.error(f"Error updating siswa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating siswa: {str(e)}")

@router.post("/dashboard/siswa/delete/{siswa_id}", response_class=HTMLResponse)
async def delete_siswa(
    siswa_id: int,
    request: Request,
    kelas_id: int = Form(None),  # Hidden field to preserve filter
    db: sqlite3.Connection = Depends(get_db_connection)
):
    logger.info(f"Deleting siswa ID: {siswa_id}")
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM siswa WHERE siswa_id = ?", (siswa_id,))
        db.commit()
        redirect_url = "/dashboard/siswa" if not kelas_id else f"/dashboard/siswa?kelas_id={kelas_id}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except Exception as e:
        logger.error(f"Error deleting siswa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting siswa: {str(e)}")

# Jadwal Routes
@router.get("/dashboard/jadwal", response_class=HTMLResponse)
async def jadwal_page(
    request: Request,
    kelas_id: int = None,
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info(f"Accessed jadwal page with kelas_id: {kelas_id}")
    try:
        cursor = db.cursor()
        
        cursor.execute("SELECT kelas_id, nama_kelas FROM kelas")
        kelas_list = cursor.fetchall()
        
        if kelas_id:
            cursor.execute("""
                SELECT j.jadwal_id, k.kelas_id, k.nama_kelas, j.hari, j.jam_mulai, j.jam_selesai, m.nama as mata_pelajaran 
                FROM kelas k 
                LEFT JOIN jadwal j ON k.kelas_id = j.kelas_id 
                LEFT JOIN mata_pelajaran m ON j.mata_pelajaran_id = m.mata_pelajaran_id
                WHERE k.kelas_id = ?
            """, (kelas_id,))
        else:
            cursor.execute("""
                SELECT j.jadwal_id, k.kelas_id, k.nama_kelas, j.hari, j.jam_mulai, j.jam_selesai, m.nama as mata_pelajaran 
                FROM kelas k 
                LEFT JOIN jadwal j ON k.kelas_id = j.kelas_id 
                LEFT JOIN mata_pelajaran m ON j.mata_pelajaran_id = m.mata_pelajaran_id
            """)
        kelas_jadwal = cursor.fetchall()
        
        cursor.execute("SELECT mata_pelajaran_id, nama FROM mata_pelajaran")
        mata_pelajaran_list = cursor.fetchall()
        
        return templates.TemplateResponse(
            "jadwal.html",
            {
                "request": request,
                "kelas_jadwal": kelas_jadwal,
                "kelas_list": kelas_list,
                "mata_pelajaran_list": mata_pelajaran_list,
                "selected_kelas_id": kelas_id
            }
        )
    except Exception as e:
        logger.error(f"Error loading jadwal page: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading jadwal page: {str(e)}")

@router.post("/dashboard/jadwal/add", response_class=HTMLResponse)
async def add_jadwal(
    request: Request,
    kelas_id: int = Form(...),
    mata_pelajaran_id: int = Form(...),
    hari: str = Form(...),
    jam_mulai: str = Form(...),
    jam_selesai: str = Form(...),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    logger.info(f"Adding jadwal for kelas_id: {kelas_id}")
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO jadwal (kelas_id, mata_pelajaran_id, hari, jam_mulai, jam_selesai) VALUES (?, ?, ?, ?, ?)",
            (kelas_id, mata_pelajaran_id, hari, jam_mulai, jam_selesai)
        )
        db.commit()
        return RedirectResponse(url=f"/dashboard/jadwal?kelas_id={kelas_id}", status_code=303)
    except Exception as e:
        logger.error(f"Error adding jadwal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding jadwal: {str(e)}")

@router.post("/dashboard/jadwal/update/{jadwal_id}", response_class=HTMLResponse)
async def update_jadwal(
    jadwal_id: int,
    request: Request,
    kelas_id: int = Form(...),
    mata_pelajaran_id: int = Form(...),
    hari: str = Form(...),
    jam_mulai: str = Form(...),
    jam_selesai: str = Form(...),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    logger.info(f"Updating jadwal ID: {jadwal_id}")
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE jadwal SET kelas_id = ?, mata_pelajaran_id = ?, hari = ?, jam_mulai = ?, jam_selesai = ? WHERE jadwal_id = ?",
            (kelas_id, mata_pelajaran_id, hari, jam_mulai, jam_selesai, jadwal_id)
        )
        db.commit()
        return RedirectResponse(url=f"/dashboard/jadwal?kelas_id={kelas_id}", status_code=303)
    except Exception as e:
        logger.error(f"Error updating jadwal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating jadwal: {str(e)}")

@router.post("/dashboard/jadwal/delete/{jadwal_id}", response_class=HTMLResponse)
async def delete_jadwal(
    jadwal_id: int,
    request: Request,
    kelas_id: int = Form(None),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    logger.info(f"Deleting jadwal ID: {jadwal_id}")
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM jadwal WHERE jadwal_id = ?", (jadwal_id,))
        db.commit()
        redirect_url = "/dashboard/jadwal" if not kelas_id else f"/dashboard/jadwal?kelas_id={kelas_id}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except Exception as e:
        logger.error(f"Error deleting jadwal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting jadwal: {str(e)}")

# Mata Pelajaran Routes
@router.get("/dashboard/mata-pelajaran", response_class=HTMLResponse)
async def mata_pelajaran_page(
    request: Request,
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info("Accessed mata pelajaran page")
    try:
        cursor = db.cursor()
        
        cursor.execute("SELECT * FROM mata_pelajaran")
        mata_pelajaran_list = cursor.fetchall()
        
        return templates.TemplateResponse(
            "mata_pelajaran.html",
            {
                "request": request,
                "mata_pelajaran_list": mata_pelajaran_list
            }
        )
    except Exception as e:
        logger.error(f"Error loading mata pelajaran page: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading mata pelajaran page: {str(e)}")

@router.post("/dashboard/mata-pelajaran/add", response_class=HTMLResponse)
async def add_mata_pelajaran(
    request: Request,
    nama: str = Form(...),
    kode: str = Form(None),
    deskripsi: str = Form(None),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    logger.info(f"Adding mata pelajaran: {nama}")
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO mata_pelajaran (nama, kode, deskripsi) VALUES (?, ?, ?)",
            (nama, kode, deskripsi)
        )
        db.commit()
        return RedirectResponse(url="/dashboard/mata-pelajaran", status_code=303)
    except Exception as e:
        logger.error(f"Error adding mata pelajaran: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding mata pelajaran: {str(e)}")

@router.post("/dashboard/mata-pelajaran/update/{mata_pelajaran_id}", response_class=HTMLResponse)
async def update_mata_pelajaran(
    mata_pelajaran_id: int,
    request: Request,
    nama: str = Form(...),
    kode: str = Form(None),
    deskripsi: str = Form(None),
    db: sqlite3.Connection = Depends(get_db_connection)
):
    logger.info(f"Updating mata pelajaran ID: {mata_pelajaran_id}")
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE mata_pelajaran SET nama = ?, kode = ?, deskripsi = ? WHERE mata_pelajaran_id = ?",
            (nama, kode, deskripsi, mata_pelajaran_id)
        )
        db.commit()
        return RedirectResponse(url="/dashboard/mata-pelajaran", status_code=303)
    except Exception as e:
        logger.error(f"Error updating mata pelajaran: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating mata pelajaran: {str(e)}")

@router.post("/dashboard/mata-pelajaran/delete/{mata_pelajaran_id}", response_class=HTMLResponse)
async def delete_mata_pelajaran(
    mata_pelajaran_id: int,
    request: Request,
    db: sqlite3.Connection = Depends(get_db_connection)
):
    logger.info(f"Deleting mata pelajaran ID: {mata_pelajaran_id}")
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (mata_pelajaran_id,))
        db.commit()
        return RedirectResponse(url="/dashboard/mata-pelajaran", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting mata pelajaran: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting mata pelajaran: {str(e)}")
    
@router.get("/store/kelas", response_class=HTMLResponse)
async def store_kelas_page(
    request: Request,
    message: str = None,
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info("Accessed store kelas page")
    try:
        cursor = db.cursor()
        # Fetch all users with role 'guru'
        cursor.execute("SELECT user_id, nama FROM users WHERE role = 'guru'")
        guru_list = cursor.fetchall()
        
        return templates.TemplateResponse(
            "store_kelas.html",
            {
                "request": request,
                "guru_list": guru_list,
                "message": message
            }
        )
    except Exception as e:
        logger.error(f"Error loading store kelas page: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading store kelas page: {str(e)}")

@router.post("/store/kelas", response_class=HTMLResponse)
async def store_kelas(
    request: Request,
    nama_kelas: str = Form(...),
    wali_kelas_id: int = Form(...),
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info(f"Storing kelas: {nama_kelas}")
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO kelas (nama_kelas, wali_kelas_id) VALUES (?, ?)",
            (nama_kelas, wali_kelas_id)
        )
        db.commit()
        return templates.TemplateResponse(
            "store_kelas.html",
            {
                "request": request,
                "message": f"Kelas {nama_kelas} berhasil disimpan!",
                "guru_list": cursor.execute("SELECT user_id, nama FROM users WHERE role = 'guru'").fetchall()
            }
        )
    except sqlite3.IntegrityError:
        logger.warning(f"Error: Kelas {nama_kelas} might already exist or invalid wali_kelas_id")
        return templates.TemplateResponse(
            "store_kelas.html",
            {
                "request": request,
                "message": "Error: Nama kelas sudah ada atau Wali Kelas ID tidak valid",
                "guru_list": cursor.execute("SELECT user_id, nama FROM users WHERE role = 'guru'").fetchall()
            }
        )
    except Exception as e:
        logger.error(f"Error storing kelas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing kelas: {str(e)}")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: sqlite3.Connection = Depends(get_db_connection),
    templates: Jinja2Templates = Depends(get_templates)
):
    logger.info("Route /dashboard accessed successfully")
    try:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading dashboard page: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading dashboard page: {str(e)}")
    
    