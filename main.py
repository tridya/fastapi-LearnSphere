import os
import json
from datetime import datetime
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import firebase_admin
from firebase_admin import credentials, messaging
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
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
    description="API untuk aplikasi LearnSphere dengan Notifikasi",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# --- Firebase Configuration ---
SERVICE_ACCOUNT_KEY_PATH = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
HOLIDAYS_JSON_PATH = os.path.join(os.path.dirname(__file__), "calendar.json")

if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
    print(f"ERROR: Service account key not found at {SERVICE_ACCOUNT_KEY_PATH}")
    print("Please download it from Firebase Console > Project Settings > Service accounts")
    exit(1)

try:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    exit(1)

# Initialize scheduler for holiday notifications
scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")

# --- Pydantic Models ---
class NotificationPayload(BaseModel):
    topic: str
    title: str
    body: str
    data_message: str | None = None

# --- Function to Send Scheduled Notification ---
async def send_scheduled_notification(topic: str, title: str, body: str, data_message: str = None):
    if not topic.startswith("/topics/"):
        target_topic = f"/topics/{topic.strip()}"
    else:
        target_topic = topic.strip()

    print(f"Sending scheduled notification to topic: {target_topic}")
    print(f"Title: {title}, Body: {body}, Data: {data_message}")

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data={"data_message_content": data_message} if data_message else None,
        topic=target_topic,
    )

    try:
        response = messaging.send(message)
        print(f"Successfully sent scheduled message: {response}")
        return {"status": "success", "message_id": response}
    except Exception as e:
        print(f"Error sending scheduled message: {e}")
        return {"status": "error", "detail": str(e)}

# --- Load Holidays and Schedule Notifications ---
def load_holidays_and_schedule():
    if not os.path.exists(HOLIDAYS_JSON_PATH):
        print(f"ERROR: Holidays JSON file not found at {HOLIDAYS_JSON_PATH}")
        return

    with open(HOLIDAYS_JSON_PATH, "r") as f:
        holidays = json.load(f)

    # Filter hanya hari libur (holiday: true) dan skip metadata 'info'
    for date, data in holidays.items():
        if isinstance(data, dict) and data.get("holiday", False):
            holiday_name = data["summary"][0] if data["summary"] else "Hari Libur"
            description = data["description"][0] if data["description"] else "Hari libur nasional"
            
            # Jadwalkan notifikasi pada pukul 08:00 WIB
            schedule_time = datetime.strptime(f"{date} 18:03:00", "%Y-%m-%d %H:%M:%S")
            if schedule_time > datetime.now():
                scheduler.add_job(
                    send_scheduled_notification,
                    trigger=DateTrigger(run_date=schedule_time, timezone="Asia/Jakarta"),
                    args=["test_topic", f"Libur: {holiday_name}", f"Selamat hari {holiday_name}! {description}", None]
                )
                print(f"Scheduled notification for {holiday_name} on {schedule_time}")

# --- Routes from LearnSphere ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serves the main HTML page for LearnSphere."""
    return templates.TemplateResponse("index.html", {"request": request})

# --- Routes from Notification ---
@app.post("/send-notification")
async def send_fcm_notification(
    topic: str = Form(...),
    title: str = Form(...),
    body: str = Form(...),
    data_message: str = Form(None)
):
    """
    Sends a notification to the specified FCM topic.
    Receives data from an HTML form.
    """
    if not topic.startswith("/topics/"):
        target_topic = f"/topics/{topic.strip()}"
    else:
        target_topic = topic.strip()

    print(f"Attempting to send to topic: {target_topic}")
    print(f"Title: {title}, Body: {body}, Data: {data_message}")

    message_payload = {
        "title": title,
        "body": body,
    }
    if data_message:
        message_payload["data_message_content"] = data_message

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=message_payload if data_message else None,
        topic=target_topic,
    )

    try:
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
        return JSONResponse(
            content={"status": "success", "message_id": response, "detail": f"Notification sent to topic: {target_topic}"},
            status_code=200
        )
    except firebase_admin.exceptions.FirebaseError as e:
        print(f"Error sending message: {e}")
        error_detail = str(e)
        if hasattr(e, 'code'):
            error_detail = f"Code: {e.code}, Message: {str(e)}"
            if e.code == 'NOT_FOUND':
                error_detail += ". This can happen if the topic does not exist or has no subscribers."
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send notification: {error_detail}"
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# --- Startup Event ---
@app.on_event("startup")
async def on_startup():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized.")
    load_holidays_and_schedule()
    scheduler.start()
    print("Scheduler started.")

# --- Shutdown Event ---
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler stopped.")

# Include routers from LearnSphere
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)