from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging
from typing import List, Optional
import sqlite3
from datetime import datetime, date
from app.schemas.rekapan_siswa import (
    RekapanSiswaCreate,
    RekapanSiswaResponse,
    StatusRekapanSiswa,
    KelasResponse,
    MataPelajaranResponse,
)
from app.schemas.jadwal import JadwalResponse
from app.schemas.user import UserInDB
from app.schemas.siswa import SiswaResponse
from app.dependencies import get_db_connection, get_current_user

router = APIRouter(prefix="/api/rekapan-siswa", tags=["rekapan_siswa"])

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Teacher Endpoints ---

@router.post("/daily", response_model=RekapanSiswaResponse)
async def create_rekapan_siswa(
    rekapan: RekapanSiswaCreate,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received POST request to /api/rekapan-siswa/daily with data: {rekapan}")
    if current_user["role"] != "guru":
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru")
        raise HTTPException(status_code=403, detail="Only teachers can create reports")
    
    cursor = db.cursor()

    # Validate siswa_id
    cursor.execute("SELECT nama, orang_tua_id FROM siswa WHERE siswa_id = ?", (rekapan.siswa_id,))
    siswa = cursor.fetchone()
    if not siswa:
        logger.error(f"Invalid siswa_id: {rekapan.siswa_id}")
        raise HTTPException(status_code=404, detail=f"Student with ID {rekapan.siswa_id} not found")
    
    # Use current_user['user_id'] as guru_id
    guru_id = current_user["user_id"]
    
    # Validate mata_pelajaran_id and fetch all required fields
    cursor.execute(
        "SELECT mata_pelajaran_id, nama, kode, deskripsi FROM mata_pelajaran WHERE mata_pelajaran_id = ?",
        (rekapan.mata_pelajaran_id,)
    )
    mata_pelajaran = cursor.fetchone()
    if not mata_pelajaran:
        logger.error(f"Invalid mata_pelajaran_id: {rekapan.mata_pelajaran_id}")
        raise HTTPException(status_code=404, detail=f"Subject with ID {rekapan.mata_pelajaran_id} not found")
    
    # Check for duplicate rekapan for today
    cursor.execute(
        """
        SELECT * FROM rekapan_siswa 
        WHERE siswa_id = ? AND mata_pelajaran_id = ? AND DATE(tanggal) = DATE('now')
        """,
        (rekapan.siswa_id, rekapan.mata_pelajaran_id)
    )
    if cursor.fetchone():
        logger.error(f"Duplicate rekapan for siswa_id: {rekapan.siswa_id}, mata_pelajaran_id: {rekapan.mata_pelajaran_id}")
        raise HTTPException(status_code=400, detail="Report for this student and subject already exists for today")
    
    # Insert rekapan
    tanggal = datetime.now().isoformat()
    try:
        cursor.execute(
            """
            INSERT INTO rekapan_siswa (siswa_id, guru_id, mata_pelajaran_id, rating, catatan, tanggal) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (rekapan.siswa_id, guru_id, rekapan.mata_pelajaran_id, rekapan.rating, rekapan.catatan, tanggal)
        )
        db.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error while inserting rekapan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save report: {str(e)}")
    
    # Fetch the newly created rekapan
    cursor.execute("SELECT * FROM rekapan_siswa WHERE report_id = ?", (cursor.lastrowid,))
    new_rekapan = cursor.fetchone()
    if not new_rekapan:
        logger.error("Failed to retrieve newly created rekapan")
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created report")
    
    # Create notification for parent if applicable
    if siswa[1]:  # orang_tua_id
        deskripsi = f"Daily report for {siswa[0]} on subject {mata_pelajaran[1]} has been created: {rekapan.rating}"
        try:
            cursor.execute(
                """
                INSERT INTO notifikasi (siswa_id, orang_tua_id, jenis, deskripsi, status, tanggal)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (rekapan.siswa_id, siswa[1], "Rekapan", deskripsi, "unread", tanggal)
            )
            db.commit()
            logger.info(f"Notification created for orang_tua_id: {siswa[1]}")
        except sqlite3.Error as e:
            logger.error(f"Failed to create notification for orang_tua_id {siswa[1]}: {str(e)}")
            pass
    
    logger.info(f"Created rekapan report_id: {new_rekapan[0]} for siswa_id: {rekapan.siswa_id}")
    return RekapanSiswaResponse(
        report_id=new_rekapan[0],
        siswa_id=new_rekapan[1],
        guru_id=new_rekapan[2],
        mata_pelajaran_id=new_rekapan[3],
        rating=new_rekapan[5],
        catatan=new_rekapan[6],
        tanggal=new_rekapan[4],
        nama_siswa=siswa[0],
        mata_pelajaran=MataPelajaranResponse(
            mata_pelajaran_id=mata_pelajaran[0],
            nama=mata_pelajaran[1],
            kode=mata_pelajaran[2],
            deskripsi=mata_pelajaran[3]
        )
    )

@router.get("/daily/{kelas_id}", response_model=List[RekapanSiswaResponse])
async def get_daily_rekapan_siswa(
    kelas_id: int,
    tanggal: date = Query(..., description="Date for reports (format: YYYY-MM-DD)"),
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received GET request to /api/rekapan-siswa/daily/{kelas_id} with tanggal: {tanggal}")
    if current_user["role"] != "guru":
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru")
        raise HTTPException(status_code=403, detail="Only teachers can view reports")
    
    cursor = db.cursor()

    # Validate that user is the class teacher
    cursor.execute(
        "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
        (kelas_id, current_user["user_id"])
    )
    kelas = cursor.fetchone()
    if not kelas:
        logger.error(f"User {current_user['user_id']} is not the class teacher for kelas_id: {kelas_id}")
        raise HTTPException(status_code=403, detail="You are not the class teacher for this class")

    # Fetch reports for the class and date
    cursor.execute(
        """
        SELECT rs.*, s.nama AS nama_siswa, mp.nama AS mata_pelajaran_nama, mp.kode, mp.deskripsi
        FROM rekapan_siswa rs
        JOIN siswa s ON rs.siswa_id = s.siswa_id
        JOIN mata_pelajaran mp ON rs.mata_pelajaran_id = mp.mata_pelajaran_id
        WHERE s.kelas_id = ? AND DATE(rs.tanggal) = ?
        """,
        (kelas_id, tanggal)
    )
    rekapan_list = cursor.fetchall()
    logger.info(f"Found {len(rekapan_list)} reports for kelas_id: {kelas_id}, tanggal: {tanggal}")

    return [
        RekapanSiswaResponse(
            report_id=row[0],
            siswa_id=row[1],
            guru_id=row[2],
            mata_pelajaran_id=row[3],
            rating=row[5],
            catatan=row[6],
            tanggal=row[4],
            nama_siswa=row[7],
            mata_pelajaran=MataPelajaranResponse(
                mata_pelajaran_id=row[3],
                nama=row[8],
                kode=row[9],
                deskripsi=row[10]
            )
        ) for row in rekapan_list
    ]

@router.get("/rekapan/kelas/{kelas_id}/mata_pelajaran/{mata_pelajaran_id}", response_model=List[StatusRekapanSiswa])
async def get_rekapan_siswa_by_kelas(
    kelas_id: int,
    mata_pelajaran_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received GET request to /api/rekapan-siswa/rekapan/kelas/{kelas_id}/mata_pelajaran/{mata_pelajaran_id}")
    if current_user["role"] != "guru":
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru")
        raise HTTPException(status_code=403, detail="Only teachers can view reports")
    
    cursor = db.cursor()

    # Validate that user is the class teacher
    cursor.execute(
        "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
        (kelas_id, current_user["user_id"])
    )
    kelas = cursor.fetchone()
    if not kelas:
        logger.error(f"User {current_user['user_id']} is not the class teacher for kelas_id: {kelas_id}")
        raise HTTPException(status_code=403, detail="You are not the class teacher for this class")

    # Validate kelas_id
    cursor.execute("SELECT * FROM kelas WHERE kelas_id = ?", (kelas_id,))
    if not cursor.fetchone():
        logger.error(f"Invalid kelas_id: {kelas_id}")
        raise HTTPException(status_code=404, detail=f"Class with ID {kelas_id} not found")

    # Validate mata_pelajaran_id
    cursor.execute("SELECT nama FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (mata_pelajaran_id,))
    mata_pelajaran = cursor.fetchone()
    if not mata_pelajaran:
        logger.error(f"Invalid mata_pelajaran_id: {mata_pelajaran_id}")
        raise HTTPException(status_code=404, detail=f"Subject with ID {mata_pelajaran_id} not found")

    # Fetch students in the class
    cursor.execute("SELECT siswa_id, nama FROM siswa WHERE kelas_id = ?", (kelas_id,))
    siswa_list = cursor.fetchall()
    logger.info(f"Found {len(siswa_list)} students for kelas_id: {kelas_id}")

    results = []
    for siswa in siswa_list:
        cursor.execute(
            """
            SELECT * FROM rekapan_siswa
            WHERE siswa_id = ? AND guru_id = ? AND mata_pelajaran_id = ? AND DATE(tanggal) = DATE('now')
            """,
            (siswa[0], current_user["user_id"], mata_pelajaran_id)
        )
        rekapan = cursor.fetchone()
        result_item = StatusRekapanSiswa(
            siswa_id=siswa[0],
            nama_siswa=siswa[1],
            sudah_dibuat=bool(rekapan),
            rekapan=RekapanSiswaResponse(
                report_id=rekapan[0],
                siswa_id=rekapan[1],
                guru_id=rekapan[2],
                mata_pelajaran_id=rekapan[3],
                rating=rekapan[5],
                catatan=rekapan[6],
                tanggal=rekapan[4],
                nama_siswa=siswa[1],
                mata_pelajaran=MataPelajaranResponse(
                    mata_pelajaran_id=mata_pelajaran_id,
                    nama=mata_pelajaran[0],
                    kode=None,
                    deskripsi=None
                )
            ) if rekapan else None
        )
        results.append(result_item)

    logger.info(f"Returning {len(results)} report statuses for kelas_id: {kelas_id}, mata_pelajaran_id: {mata_pelajaran_id}")
    return results

@router.get("/jadwal/kelas/{kelas_id}", response_model=List[JadwalResponse])
async def get_jadwal_siswa_by_kelas(
    kelas_id: int,
    hari: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received GET request to /api/rekapan-siswa/jadwal/kelas/{kelas_id} with hari: {hari}")
    if current_user["role"] != "guru":
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru")
        raise HTTPException(status_code=403, detail="Only teachers can view schedules")
    
    cursor = db.cursor()

    # Validate that user is the class teacher
    cursor.execute(
        "SELECT * FROM kelas WHERE kelas_id = ? AND wali_kelas_id = ?",
        (kelas_id, current_user["user_id"])
    )
    kelas = cursor.fetchone()
    if not kelas:
        logger.error(f"User {current_user['user_id']} is not the class teacher for kelas_id: {kelas_id}")
        raise HTTPException(status_code=403, detail="You are not the class teacher for this class")

    # If hari is not provided, use current day
    if not hari:
        now = datetime.now()
        hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][now.weekday()]
        if hari == "Minggu":
            logger.info(f"No schedule available for hari: {hari}")
            return []

    # Validate hari
    valid_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
    if hari not in valid_hari:
        logger.error(f"Invalid hari: {hari}")
        raise HTTPException(status_code=400, detail="Invalid day. Use: Senin, Selasa, Rabu, Kamis, Jumat, Sabtu")

    # Fetch schedule for the class on the given day
    cursor.execute(
        """
        SELECT j.* FROM jadwal j
        WHERE j.kelas_id = ? AND j.hari = ?
        """,
        (kelas_id, hari)
    )
    jadwal_list = cursor.fetchall()
    logger.info(f"Found {len(jadwal_list)} schedules for kelas_id: {kelas_id}, hari: {hari}")

    if not jadwal_list:
        return []

    # Prepare response with enriched data
    result = []
    for jadwal in jadwal_list:
        # Fetch subject details
        cursor.execute("SELECT * FROM mata_pelajaran WHERE mata_pelajaran_id = ?", (jadwal[2],))
        mata_pelajaran = cursor.fetchone()
        if not mata_pelajaran:
            logger.error(f"Subject not found for mata_pelajaran_id: {jadwal[2]}")
            continue

        # Fetch class teacher details
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (kelas[2],))
        wali_kelas = cursor.fetchone()
        if not wali_kelas:
            logger.error(f"Class teacher not found for user_id: {kelas[2]}")
            continue

        result.append(JadwalResponse(
            jadwal_id=jadwal[0],
            kelas_id=jadwal[1],
            hari=jadwal[3],
            jam_mulai=str(jadwal[4]),
            jam_selesai=str(jadwal[5]),
            mata_pelajaran_id=jadwal[2],
            mata_pelajaran=MataPelajaranResponse(
                mata_pelajaran_id=mata_pelajaran[0],
                nama=mata_pelajaran[1],
                kode=mata_pelajaran[2],
                deskripsi=mata_pelajaran[3]
            ),
            wali_kelas=UserInDB(
                user_id=wali_kelas[0],
                nama=wali_kelas[1],
                username=wali_kelas[2],
                role=wali_kelas[3],
                password=wali_kelas[4],
                created_at=str(wali_kelas[5])
            )
        ))

    logger.info(f"Returning {len(result)} schedules for kelas_id: {kelas_id}, hari: {hari}")
    return result

@router.get("/kelas", response_model=List[KelasResponse])
async def get_kelas_list(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received GET request to /api/rekapan-siswa/kelas")
    if current_user["role"] != "guru":
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru")
        raise HTTPException(status_code=403, detail="Only teachers can view class list")
    
    cursor = db.cursor()
    cursor.execute("SELECT kelas_id, nama_kelas, wali_kelas_id FROM kelas WHERE wali_kelas_id = ?", (current_user["user_id"],))
    kelas_list = cursor.fetchall()
    logger.info(f"Returning {len(kelas_list)} classes for user {current_user['user_id']}")
    
    return [KelasResponse(kelas_id=k[0], nama_kelas=k[1], wali_kelas_id=k[2]) for k in kelas_list]

@router.get("/mata_pelajaran", response_model=List[MataPelajaranResponse])
async def get_mata_pelajaran_list(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received GET request to /api/rekapan-siswa/mata_pelajaran for user {current_user['user_id']}")
    if current_user["role"] not in ["guru", "orang_tua"]:
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru or orang_tua")
        raise HTTPException(status_code=403, detail="Only teachers or parents can view subjects")
    
    cursor = db.cursor()
    
    if current_user["role"] == "orang_tua":
        # Verify parent role
        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = ? AND role = 'orang_tua'",
            (current_user["user_id"],)
        )
        user = cursor.fetchone()
        if not user:
            logger.error(f"No parent record found for user_id: {current_user['user_id']}")
            raise HTTPException(status_code=404, detail="Parent account not found")
        
        # Fetch kelas_id of the student's class
        cursor.execute(
            "SELECT DISTINCT kelas_id FROM siswa WHERE orang_tua_id = ?",
            (current_user["user_id"],)
        )
        kelas_list = cursor.fetchall()
        if not kelas_list:
            logger.info(f"No students found for user_id: {current_user['user_id']}")
            return []
        
        kelas_ids = [kelas[0] for kelas in kelas_list]
        
        # Fetch subjects linked to the student's class via jadwal
        cursor.execute(
            """
            SELECT DISTINCT mp.mata_pelajaran_id, mp.nama, mp.kode, mp.deskripsi
            FROM mata_pelajaran mp
            JOIN jadwal j ON mp.mata_pelajaran_id = j.mata_pelajaran_id
            WHERE j.kelas_id IN ({})
            """.format(','.join('?' * len(kelas_ids))),
            kelas_ids
        )
        mata_pelajaran_list = cursor.fetchall()
    else:  # role == "guru"
        # Fetch all subjects for teacher
        cursor.execute("SELECT mata_pelajaran_id, nama, kode, deskripsi FROM mata_pelajaran")
        mata_pelajaran_list = cursor.fetchall()
    
    logger.info(f"Returning {len(mata_pelajaran_list)} subjects for user {current_user['user_id']}")
    
    return [
        MataPelajaranResponse(
            mata_pelajaran_id=mp[0],
            nama=mp[1],
            kode=mp[2],
            deskripsi=mp[3]
        ) for mp in mata_pelajaran_list
    ]

@router.delete("/{report_id}", response_model=dict)
async def delete_rekapan_siswa(
    report_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received DELETE request to /api/rekapan-siswa/{report_id}")
    if current_user["role"] != "guru":
        logger.error(f"Access denied for user {current_user['user_id']}: not a guru")
        raise HTTPException(status_code=403, detail="Only teachers can delete reports")
    
    cursor = db.cursor()

    # Check if report exists
    cursor.execute("SELECT * FROM rekapan_siswa WHERE report_id = ?", (report_id,))
    rekapan = cursor.fetchone()
    if not rekapan:
        logger.error(f"Report not found for report_id: {report_id}")
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Delete report
    cursor.execute("DELETE FROM rekapan_siswa WHERE report_id = ?", (report_id,))
    db.commit()
    
    logger.info(f"Deleted report report_id: {report_id}")
    return {"message": "Report successfully deleted"}

# --- Parent Endpoints ---

@router.get("/siswa", response_model=List[SiswaResponse])
async def get_siswa_orang_tua(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received GET request to /api/rekapan-siswa/siswa for user {current_user['user_id']}")
    if current_user["role"] != "orang_tua":
        logger.error(f"Access denied for user {current_user['user_id']}: not an orang_tua")
        raise HTTPException(status_code=403, detail="Only parents can access student data")
    
    cursor = db.cursor()
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ? AND role = 'orang_tua'",
        (current_user["user_id"],)
    )
    parent = cursor.fetchone()
    if not parent:
        logger.error(f"No parent record found for user_id: {current_user['user_id']}")
        raise HTTPException(status_code=404, detail="Parent account not found")
    
    orang_tua_id = parent[0]
    cursor.execute(
        """
        SELECT s.siswa_id, s.nama, s.kelas_id, s.orang_tua_id, s.kode_siswa, k.nama_kelas
        FROM siswa s
        LEFT JOIN kelas k ON s.kelas_id = k.kelas_id
        WHERE s.orang_tua_id = ?
        """,
        (orang_tua_id,)
    )
    siswa_list = cursor.fetchall()
    
    if not siswa_list:
        logger.info(f"No students found for orang_tua_id: {orang_tua_id}")
        return []
    
    logger.info(f"Found {len(siswa_list)} students for orang_tua_id: {orang_tua_id}")
    return [
        SiswaResponse(
            siswa_id=row[0],
            nama=row[1],
            kelas_id=row[2],
            orang_tua_id=row[3],
            kode_siswa=row[4],
            nama_kelas=row[5]
        ) for row in siswa_list
    ]

@router.get("/siswa/{siswa_id}", response_model=SiswaResponse)
async def get_siswa_by_id(
    siswa_id: int,
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received GET request to /api/rekapan-siswa/siswa/{siswa_id} for user {current_user['user_id']}")
    if current_user["role"] != "orang_tua":
        logger.error(f"Access denied for user {current_user['user_id']}: not an orang_tua")
        raise HTTPException(status_code=403, detail="Only parents can access student data")
    
    cursor = db.cursor()
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ? AND role = 'orang_tua'",
        (current_user["user_id"],)
    )
    parent = cursor.fetchone()
    if not parent:
        logger.error(f"No parent record found for user_id: {current_user['user_id']}")
        raise HTTPException(status_code=404, detail="Parent account not found")
    
    orang_tua_id = parent[0]
    cursor.execute(
        """
        SELECT s.siswa_id, s.nama, s.kelas_id, s.orang_tua_id, s.kode_siswa, k.nama_kelas
        FROM siswa s
        LEFT JOIN kelas k ON s.kelas_id = k.kelas_id
        WHERE s.siswa_id = ? AND s.orang_tua_id = ?
        """,
        (siswa_id, orang_tua_id)
    )
    siswa = cursor.fetchone()
    
    if not siswa:
        logger.error(f"No student found for siswa_id: {siswa_id} and orang_tua_id: {orang_tua_id}")
        raise HTTPException(status_code=403, detail="Student is not linked to this parent account")
    
    logger.info(f"Found student siswa_id={siswa_id} for orang_tua_id={orang_tua_id}")
    return SiswaResponse(
        siswa_id=siswa[0],
        nama=siswa[1],
        kelas_id=siswa[2],
        orang_tua_id=siswa[3],
        kode_siswa=siswa[4],
        nama_kelas=siswa[5]
    )

@router.get("/rekapan", response_model=List[RekapanSiswaResponse])
async def get_rekapan_siswa_orangtua(
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    mata_pelajaran_id: Optional[int] = Query(None, description="Filter by subject ID"),
    siswa_id: Optional[int] = Query(None, description="Filter by student ID")
):
    logger.debug(f"Received GET request to /api/rekapan-siswa/rekapan for user {current_user['user_id']} "
                 f"with filters: start_date={start_date}, end_date={end_date}, mata_pelajaran_id={mata_pelajaran_id}, siswa_id={siswa_id}")
    
    if current_user["role"] != "orang_tua":
        logger.error(f"Access denied for user {current_user['user_id']}: not an orang_tua")
        raise HTTPException(status_code=403, detail="Only parents can access reports")
    
    cursor = db.cursor()
    
    # Verify that the user is a parent
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ? AND role = 'orang_tua'",
        (current_user["user_id"],)
    )
    parent = cursor.fetchone()
    if not parent:
        logger.error(f"No parent record found for user_id: {current_user['user_id']}")
        raise HTTPException(status_code=404, detail="Parent account not found")
    
    orang_tua_id = parent[0]
    
    # Fetch students linked to the orang_tua_id
    cursor.execute(
        """
        SELECT siswa_id, nama FROM siswa WHERE orang_tua_id = ?
        """,
        (orang_tua_id,)
    )
    siswa_list = cursor.fetchall()
    if not siswa_list:
        logger.info(f"No students found for orang_tua_id: {orang_tua_id}")
        return []
    
    siswa_ids = [row[0] for row in siswa_list]
    siswa_names = {row[0]: row[1] for row in siswa_list}
    
    # Validate siswa_id if provided
    if siswa_id and siswa_id not in siswa_ids:
        logger.error(f"Invalid siswa_id: {siswa_id} for orang_tua_id: {orang_tua_id}")
        raise HTTPException(status_code=403, detail="Student is not linked to this parent account")
    
    # Build the query for rekapan_siswa with optional filters
    query = """
        SELECT rs.report_id, rs.siswa_id, rs.guru_id, rs.mata_pelajaran_id, rs.tanggal, 
               rs.rating, rs.catatan
        FROM rekapan_siswa rs
        WHERE rs.siswa_id IN ({})
    """.format(','.join('?' * (1 if siswa_id else len(siswa_ids))))
    params = [siswa_id] if siswa_id else siswa_ids
    
    # Add date range filters
    if start_date:
        query += " AND DATE(rs.tanggal) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(rs.tanggal) <= ?"
        params.append(end_date)
    if mata_pelajaran_id:
        query += " AND rs.mata_pelajaran_id = ?"
        params.append(mata_pelajaran_id)
    
    query += " ORDER BY rs.tanggal DESC"
    
    # Execute the query
    cursor.execute(query, params)
    rekapan_list = cursor.fetchall()
    if not rekapan_list:
        logger.info(f"No reports found for orang_tua_id: {orang_tua_id} with applied filters")
        return []
    
    # Prepare response with enriched data
    result = []
    for rekapan in rekapan_list:
        # Fetch subject details
        cursor.execute(
            """
            SELECT mata_pelajaran_id, nama, kode, deskripsi 
            FROM mata_pelajaran 
            WHERE mata_pelajaran_id = ?
            """,
            (rekapan[3],)
        )
        mata_pelajaran = cursor.fetchone()
        
        result.append(RekapanSiswaResponse(
            report_id=rekapan[0],
            siswa_id=rekapan[1],
            guru_id=rekapan[2],
            mata_pelajaran_id=rekapan[3],
            rating=rekapan[5],
            catatan=rekapan[6],
            tanggal=rekapan[4],
            nama_siswa=siswa_names.get(rekapan[1], "Unknown"),
            mata_pelajaran=MataPelajaranResponse(
                mata_pelajaran_id=mata_pelajaran[0],
                nama=mata_pelajaran[1],
                kode=mata_pelajaran[2],
                deskripsi=mata_pelajaran[3]
            ) if mata_pelajaran else None
        ))
    
    logger.info(f"Found {len(result)} reports for orang_tua_id: {orang_tua_id}")
    return result

@router.get("/orangtua/{siswa_id}/jadwal", response_model=List[JadwalResponse])
async def get_jadwal_siswa_orangtua(
    siswa_id: int,
    hari: Optional[str] = Query(None, description="Day of the week (e.g., Senin, Selasa)"),
    db: sqlite3.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user)
):
    logger.debug(f"Received GET request to /api/rekapan-siswa/orangtua/{siswa_id}/jadwal for user {current_user['user_id']} "
                 f"with hari: {hari}")
    
    if current_user["role"] != "orang_tua":
        logger.error(f"Access denied for user {current_user['user_id']}: not an orang_tua")
        raise HTTPException(status_code=403, detail="Only parents can access schedules")
    
    cursor = db.cursor()
    
    # Verify that the user is a parent
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ? AND role = 'orang_tua'",
        (current_user["user_id"],)
    )
    parent = cursor.fetchone()
    if not parent:
        logger.error(f"No parent record found for user_id: {current_user['user_id']}")
        raise HTTPException(status_code=404, detail="Parent account not found")
    
    orang_tua_id = parent[0]
    
    # Validate that the siswa_id is linked to the orang_tua_id and get kelas_id
    cursor.execute(
        """
        SELECT s.siswa_id, s.nama, s.kelas_id, k.nama_kelas
        FROM siswa s
        LEFT JOIN kelas k ON s.kelas_id = k.kelas_id
        WHERE s.siswa_id = ? AND s.orang_tua_id = ?
        """,
        (siswa_id, orang_tua_id)
    )
    siswa = cursor.fetchone()
    if not siswa:
        logger.error(f"Siswa_id {siswa_id} not linked to orang_tua_id {orang_tua_id}")
        raise HTTPException(status_code=403, detail="Student is not linked to this parent account")
    
    kelas_id = siswa[2]
    if not kelas_id:
        logger.info(f"No class assigned to siswa_id: {siswa_id}")
        return []

    # Build query for jadwal
    query = "SELECT j.* FROM jadwal j WHERE j.kelas_id = ?"
    params = [kelas_id]
    
    if hari:
        # Validate hari
        valid_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
        if hari not in valid_hari:
            logger.error(f"Invalid hari: {hari}")
            raise HTTPException(status_code=400, detail="Invalid day. Use: Senin, Selasa, Rabu, Kamis, Jumat, Sabtu")
        query += " AND j.hari = ?"
        params.append(hari)
    
    # Fetch schedule
    cursor.execute(query, params)
    jadwal_list = cursor.fetchall()
    logger.info(f"Found {len(jadwal_list)} schedules for kelas_id: {kelas_id}, hari: {hari}")

    if not jadwal_list:
        return []

    # Prepare response with enriched data
    result = []
    for jadwal in jadwal_list:
        # Fetch subject details
        cursor.execute(
            """
            SELECT mata_pelajaran_id, nama, kode, deskripsi 
            FROM mata_pelajaran 
            WHERE mata_pelajaran_id = ?
            """,
            (jadwal[2],)
        )
        mata_pelajaran = cursor.fetchone()
        if not mata_pelajaran:
            logger.error(f"Subject not found for mata_pelajaran_id: {jadwal[2]}")
            continue

        # Fetch class teacher details
        cursor.execute(
            """
            SELECT user_id, nama, username, role, password, created_at 
            FROM users 
            WHERE user_id = (SELECT wali_kelas_id FROM kelas WHERE kelas_id = ?)
            """,
            (kelas_id,)
        )
        wali_kelas = cursor.fetchone()
        if not wali_kelas:
            logger.error(f"Class teacher not found for kelas_id: {kelas_id}")
            continue

        result.append(JadwalResponse(
            jadwal_id=jadwal[0],
            kelas_id=jadwal[1],
            hari=jadwal[3],
            jam_mulai=str(jadwal[4]),
            jam_selesai=str(jadwal[5]),
            mata_pelajaran_id=jadwal[2],
            mata_pelajaran=MataPelajaranResponse(
                mata_pelajaran_id=mata_pelajaran[0],
                nama=mata_pelajaran[1],
                kode=mata_pelajaran[2],
                deskripsi=mata_pelajaran[3]
            ),
            wali_kelas=UserInDB(
                user_id=wali_kelas[0],
                nama=wali_kelas[1],
                username=wali_kelas[2],
                role=wali_kelas[3],
                password=wali_kelas[4],
                created_at=str(wali_kelas[5])
            )
        ))

    logger.info(f"Returning {len(result)} schedules for siswa_id: {siswa_id}, kelas_id: {kelas_id}, hari: {hari}")
    return result