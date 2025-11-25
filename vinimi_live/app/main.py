# app/main.py
from fastapi import (
    BackgroundTasks,
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    Body,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from deepface import DeepFace
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import hashlib
import csv
from io import StringIO, BytesIO
from fastapi.responses import StreamingResponse

import numpy as np
import cv2
import traceback
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import deque

from .db import (
    insert_worker,
    insert_embedding,
    insert_worker_image,
    fetch_workers_basic,
    fetch_worker_images,
    fetch_worker_by_id,
    get_conn,
    get_manager_by_email,
    insert_manager,
    get_manager_by_id,
    update_manager,
    get_company_by_id,
    ensure_violation_table,
    list_violations,
)
from .face_gallery import face_gallery, reload_gallery
from .config import get_settings
from .detection import analyze_frame_bgr, init_models
from .alerts import (
    log_event,
    maybe_send_helmet_alert,
    normalize_phone,
    record_violation,
    send_sms,
    load_recent_alerts_cache,
    get_recent_alert_entries,
    add_recent_alert_entry,
)

settings = get_settings()
# where to store worker images
MEDIA_ROOT = Path(settings.MEDIA_ROOT)
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
# live event logs (rolling per day)
LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
# where we store cropped face images for each worker
WORKER_IMAGE_DIR = Path("worker_images")
WORKER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
VIOLATIONS_DIR = MEDIA_ROOT / "violations"
VIOLATIONS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="VINIMI Live Detection API")
models = init_models()
# serve images at http://localhost:8001/media/...
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AlertsTestPayload(BaseModel):
    phone: str
    message: str = "VINIMI: test SMS from VINIMI dashboard."
    worker_id: Optional[int] = None
    worker_name: Optional[str] = None

class ManagerSignup(BaseModel):
    name: str
    email: str
    password: str
    company_id: int

class ManagerLogin(BaseModel):
    email: str
    password: str

class ManagerAuthPayload(BaseModel):
    name: Optional[str] = None
    email: str
    password: str
    company_id: int


def log_live_event(result: dict) -> None:
    """
    Append a single-line JSON record describing the live detection result.
    Written to logs/YYYY-MM-DD.log.
    """
    try:
        person = result.get("person", {}) or {}
        ppe = result.get("ppe", {}) or {}
        ts = datetime.utcnow().isoformat() + "Z"
        record = {
            "ts": ts,
            "name": person.get("name") or "Unknown",
            "worker_id": person.get("worker_id"),
            "company_id": person.get("company_id"),
            "location_id": person.get("location_id"),
            "helmet_on": bool(ppe.get("helmet_on")),
            "is_unknown": not person.get("worker_id"),
            "similarity": person.get("similarity"),
        }
        day_file = LOGS_DIR / f"{ts[:10]}.log"
        with day_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception as e:
        print("⚠️ log_live_event error:", e)


def save_violation_snapshot(frame_bgr: np.ndarray, worker_id: int) -> Optional[str]:
    try:
        ts = datetime.utcnow()
        day_dir = VIOLATIONS_DIR / ts.strftime("%Y%m%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{ts.strftime('%H%M%S')}_worker_{worker_id}.jpg"
        path = day_dir / filename
        success = cv2.imwrite(str(path), frame_bgr)
        if success:
            return str(path)
    except Exception as exc:
        log_event(
            "snapshot.error",
            {"worker_id": worker_id, "error": str(exc)},
        )
    return None


def log_detection_summary(source: str, result: dict) -> None:
    person = result.get("person", {}) or {}
    ppe = result.get("ppe", {}) or {}
    log_event(
        "detection",
        {
            "source": source,
            "worker_id": person.get("worker_id"),
            "name": person.get("name"),
            "helmet_on": ppe.get("helmet_on"),
            "camera_id": result.get("camera_id"),
        },
    )


def schedule_helmet_alert(
    background_tasks: BackgroundTasks,
    frame_bgr: np.ndarray,
    result: dict,
    source: str,
) -> None:
    try:
        person = result.get("person", {}) or {}
        ppe = result.get("ppe", {}) or {}
        worker_id = person.get("worker_id")
        helmet_on = bool(ppe.get("helmet_on", True))
        if helmet_on:
            return

        snapshot_path = save_violation_snapshot(frame_bgr, worker_id or 0)
        loc_id = person.get("location_id")
        location_name = person.get("location") or None
        if not location_name and loc_id:
            location_name = _get_location_names([loc_id]).get(loc_id)
        if not location_name:
            location_name = "Unknown location"

        extra = {
            "name": person.get("name"),
            "company_id": person.get("company_id"),
            "location_id": person.get("location_id"),
             "location_name": location_name,
            "source": source,
            "camera_id": result.get("camera_id"),
            "detected_at": result.get("detected_at"),
        }

        initial_status = "pending" if worker_id else "unknown_worker"
        violation_id = record_violation(
            worker_id=worker_id,
            worker_name=person.get("name"),
            phone=person.get("phone"),
            frame_path=snapshot_path,
            sms_sid=None,
            sms_status=initial_status,
            details=extra,
            location_id=loc_id,
            location_name=location_name,
        )
        if violation_id <= 0:
            return

        if not worker_id:
            log_event(
                "alert.skipped",
                {"worker_id": None, "reason": "unknown_worker"},
            )
            return

        background_tasks.add_task(
            maybe_send_helmet_alert,
            violation_id,
            worker_id,
            person.get("phone"),
            snapshot_path,
            extra,
        )
    except Exception as exc:
        log_event("alert.schedule_error", {"error": str(exc)})


def _get_location_names(location_ids: list[int]) -> dict[int, str]:
    """
    Helper to map location_id -> location.name for live alert responses.
    """
    if not location_ids:
        return {}

    placeholders = ",".join(["%s"] * len(location_ids))
    sql = f"SELECT id, name FROM location WHERE id IN ({placeholders})"
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, location_ids)
            rows = cur.fetchall()
    finally:
        conn.close()

    return {row["id"]: row["name"] for row in rows}

@app.on_event("startup")
def on_startup() -> None:
    ensure_violation_table()
    load_recent_alerts_cache()
    init_models()
    print("✅ YOLO model and face gallery loaded")


def _public_manager(mgr: dict) -> dict:
    if not mgr:
        return {}
    return {
        "id": mgr.get("id"),
        "name": mgr.get("name"),
        "email": mgr.get("email"),
        "company_id": mgr.get("company_id"),
        "created_at": mgr.get("created_at"),
    }


@app.post("/api/manager/signup")
def manager_signup(payload: ManagerSignup):
    existing = get_manager_by_email(payload.email)
    if existing:
        return JSONResponse(status_code=409, content={"error": "Email already exists"})
    mid = insert_manager(payload.name, payload.email, payload.password, payload.company_id)
    mgr = get_manager_by_id(mid)
    return _public_manager(mgr)


@app.post("/api/manager/login")
def manager_login(payload: ManagerLogin):
    mgr = get_manager_by_email(payload.email)
    if not mgr or mgr.get("password_hash") != payload.password:
        return JSONResponse(status_code=401, content={"error": "Invalid email or password"})
    return _public_manager(mgr)


@app.get("/api/manager/{manager_id}")
def manager_get(manager_id: int):
    mgr = get_manager_by_id(manager_id)
    if not mgr:
        raise HTTPException(status_code=404, detail="Manager not found")
    return _public_manager(mgr)


@app.put("/api/manager/{manager_id}")
def manager_update(manager_id: int, payload: dict = Body(...)):
    mgr = get_manager_by_id(manager_id)
    if not mgr:
        raise HTTPException(status_code=404, detail="Manager not found")
    name = payload.get("name")
    company_id = payload.get("company_id")
    password = payload.get("password")
    update_manager(manager_id, name=name, company_id=company_id, password_hash=password)
    mgr2 = get_manager_by_id(manager_id)
    return _public_manager(mgr2)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/api/live/frame")
async def live_frame(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    data = await file.read()
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Could not decode frame"},
        )

    # analyze the frame
    result = analyze_frame_bgr(frame)

    # Logging
    log_live_event(result)
    log_detection_summary("live_frame", result)

    # Schedule alerts if needed
    schedule_helmet_alert(background_tasks, frame, result, "live_frame")

    return result


@app.post("/api/alerts/test")
def send_test_sms(payload: AlertsTestPayload) -> dict:
    if not settings.ALERTS_SMS_ENABLED:
        raise HTTPException(status_code=400, detail="SMS alerts disabled")

    phone = normalize_phone(payload.phone)
    if not phone:
        raise HTTPException(status_code=422, detail="Invalid phone number")

    message = (payload.message or "").strip() or "VINIMI: test SMS alert."
    trimmed_message = message[:160]
    sid, status = send_sms(phone, trimmed_message)
    if status == "not_configured":
        raise HTTPException(status_code=503, detail="Twilio credentials not configured")

    worker_name = (payload.worker_name or "").strip() or "Manual alert"
    worker_id = payload.worker_id

    record_violation(
        worker_id=worker_id,
        worker_name=worker_name,
        phone=phone,
        frame_path=None,
        sms_sid=sid,
        sms_status=status,
        details={"type": "test_sms", "message": trimmed_message},
    )
    add_recent_alert_entry(
        {
            "worker_id": worker_id,
            "worker_name": worker_name,
            "phone": phone,
            "location_name": "Manual trigger",
            "sms_status": status,
            "sms_sid": sid,
            "details": {"type": "test_sms"},
        }
    )

    log_event(
        "alert.test_sms",
        {
            "phone": phone,
            "status": status,
            "sid": sid,
        },
    )
    return {"status": status, "sid": sid}



@app.get("/api/live/recent-alerts")
def recent_alerts(limit: int = 20) -> list[dict]:
    """Return SMS alerts pulled from the recent alerts cache (file-backed)."""
    limit = max(1, min(limit, 200))
    return get_recent_alert_entries(limit)

# --- Auth endpoints (simple token) ---
def _hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

@app.post("/auth/signup")
def auth_signup(payload: ManagerAuthPayload):
    if not payload.name:
        return JSONResponse(status_code=422, content={"detail": "Name is required"})
    company = get_company_by_id(payload.company_id)
    if not company:
        return JSONResponse(status_code=404, content={"detail": "Company not found"})
    existing = get_manager_by_email(payload.email)
    if existing:
        return JSONResponse(status_code=400, content={"detail": "Email already registered"})
    pw_hash = _hash_password(payload.password)
    manager_id = insert_manager(payload.name, payload.email, pw_hash, payload.company_id)
    return {
        "status": "ok",
        "manager": {"id": manager_id, "name": payload.name, "email": payload.email, "company_id": payload.company_id},
    }

@app.post("/auth/login")
def auth_login(payload: ManagerAuthPayload):
    mgr = get_manager_by_email(payload.email)
    if not mgr:
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})
    pw_hash = _hash_password(payload.password)
    if mgr.get("password_hash") != pw_hash:
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})
    return {
        "status": "ok",
        "manager": {"id": mgr["id"], "name": mgr["name"], "email": mgr["email"], "company_id": mgr["company_id"]},
    }


@app.get("/api/logs/today")
def get_logs_today() -> JSONResponse:
    today = datetime.utcnow().date().isoformat()
    path = LOGS_DIR / f"{today}.log"
    if not path.exists():
        return JSONResponse(content={"log": ""})
    text = path.read_text(encoding="utf-8")
    return JSONResponse(content={"log": text})


@app.get("/api/logs/today.pdf")
def get_logs_today_pdf():
    today = datetime.utcnow().date().isoformat()
    log_path = LOGS_DIR / f"{today}.log"
    if not log_path.exists():
        text = "No logs for today."
    else:
        text = log_path.read_text(encoding="utf-8")

    pdf_bytes_path = LOGS_DIR / f"{today}.pdf"
    c = canvas.Canvas(str(pdf_bytes_path), pagesize=letter)
    width, height = letter
    y = height - 40
    c.setFont("Helvetica", 10)
    for line in text.splitlines() or ["No logs for today."]:
        if y < 40:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 40
        c.drawString(40, y, line[:180])
        y -= 14
    c.save()
    return FileResponse(pdf_bytes_path, media_type="application/pdf", filename=f"{today}.pdf")

# --------- Log utilities ---------
def _list_logs() -> list[str]:
    if not LOGS_DIR.exists():
        return []
    raw = [p.name for p in LOGS_DIR.iterdir() if p.is_file() and p.suffix == ".log"]
    today_name = f"{datetime.utcnow().date().isoformat()}.log"
    date_files = []
    other_files = []
    for f in raw:
        if f == today_name:
            continue
        try:
            # date formatted?
            datetime.strptime(f.replace(".log", ""), "%Y-%m-%d")
            date_files.append(f)
        except Exception:
            other_files.append(f)
    date_files = sorted(date_files, reverse=True)
    other_files = sorted(other_files, reverse=True)
    ordered = []
    if today_name in raw:
        ordered.append(today_name)
    ordered.extend(date_files)
    ordered.extend(other_files)
    return ordered

def _resolve_log_file(name: Optional[str]) -> Optional[Path]:
    if name:
        p = LOGS_DIR / name
        return p if p.exists() else None
    # default: today or latest
    today = LOGS_DIR / f"{datetime.utcnow().date().isoformat()}.log"
    if today.exists():
        return today
    files = _list_logs()
    if files:
        return LOGS_DIR / files[0]
    return None

def _tail_json(path: Path, lines: int = 200) -> list[dict]:
    lines = max(1, min(lines, 2000))
    dq = deque(maxlen=lines)
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            dq.append(ln.rstrip("\n"))
    out: list[dict] = []
    for ln in dq:
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out

@app.get("/api/logs/list")
def api_logs_list():
    return _list_logs()

@app.get("/api/logs/tail")
def api_logs_tail(file: Optional[str] = None, lines: int = 200):
    path = _resolve_log_file(file)
    if not path:
        return JSONResponse(status_code=404, content={"error": "No log file found"})
    data = _tail_json(path, lines=lines)
    return data

def _rows_from_log(path: Path) -> list[dict]:
    return _tail_json(path, lines=10_000)

@app.get("/api/logs/download")
def api_logs_download(file: Optional[str] = None, format: str = "csv"):
    path = _resolve_log_file(file)
    if not path:
        return JSONResponse(status_code=404, content={"error": "No log file found"})
    rows = _rows_from_log(path)

    fmt = format.lower()
    if fmt == "json":
        buf = BytesIO(json.dumps(rows).encode("utf-8"))
        headers = {"Content-Disposition": f'attachment; filename="{path.stem}.json"'}
        return StreamingResponse(buf, media_type="application/json", headers=headers)

    if fmt == "csv":
        sio = StringIO()
        writer = csv.writer(sio)
        writer.writerow(
            ["ts", "name", "worker_id", "company_id", "location_id", "helmet_on", "is_unknown", "similarity"]
        )
        for r in rows:
            writer.writerow([
                r.get("ts"),
                r.get("name"),
                r.get("worker_id"),
                r.get("company_id"),
                r.get("location_id"),
                r.get("helmet_on"),
                r.get("is_unknown"),
                r.get("similarity"),
            ])
        buf = BytesIO(sio.getvalue().encode("utf-8"))
        headers = {"Content-Disposition": f'attachment; filename="{path.stem}.csv"'}
        return StreamingResponse(buf, media_type="text/csv", headers=headers)

    if fmt == "pdf":
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from dateutil import tz

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter)
        styles = getSampleStyleSheet()
        data = [["Time", "Name", "Worker ID", "Location ID", "Helmet", "Unknown", "Similarity"]]

        local = tz.tzlocal()
        for r in rows:
            ts = r.get("ts")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(local)
                ts_disp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                ts_disp = str(ts)
            data.append([
                ts_disp,
                r.get("name") or "Unknown",
                r.get("worker_id") or "–",
                r.get("location_id") or "–",
                "Yes" if r.get("helmet_on") else "No",
                "Yes" if r.get("is_unknown") else "No",
                f"{float(r.get('similarity',0)):.3f}" if r.get("similarity") is not None else "",
            ])

        table = Table(data, colWidths=[1.6*inch, 1.4*inch, 0.9*inch, 1.0*inch, 0.7*inch, 0.9*inch, 0.9*inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey]),
        ]))

        header = Paragraph("VINIMI — Live Logs", styles["Heading2"])
        doc.build([header, table])
        buf.seek(0)
        headers = {"Content-Disposition": f'attachment; filename="{path.stem}.pdf"'}
        return StreamingResponse(buf, media_type="application/pdf", headers=headers)

    return JSONResponse(status_code=400, content={"error": "Unsupported format"})

@app.get("/api/violations")
def api_violations(limit: int = 200) -> list[dict]:
    """Return the latest helmet violations regardless of SMS status."""
    limit = max(1, min(limit, 500))
    return list_violations(limit=limit, sms_only=False)


@app.post("/api/detect/frame")
async def detect_frame(frame: UploadFile = File(...)):
    try:
        data = await frame.read()
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return JSONResponse(status_code=400, content={"error": "Could not decode image"})

        result = analyze_frame_bgr(img)
        return result
    except Exception as e:
        print("Error in /api/detect/frame:", e)
        return JSONResponse(status_code=500, content={"error": "Internal server error"})
    
# app/main.py

@app.get("/api/workers")
def list_workers() -> list[dict]:
    """
    Return workers along with their images and derived violations.

    JSON shape matches the WorkerApi, WorkerImage, WorkerViolation
    types you used on the frontend.
    """
    workers_raw = fetch_workers_basic()
    result: list[dict] = []

    for row in workers_raw:
        wid = row["id"]
        images_raw = fetch_worker_images(wid)

        images: list[dict] = []
        violations: list[dict] = []

        for img in images_raw:
            fname = img["filename"]
            url = f"{settings.MEDIA_BASE_URL}/worker_{wid}/{fname}"
            helmet_on = bool(img.get("helmet_on", 1))
            captured_at = img.get("capture_datetime")

            if hasattr(captured_at, "strftime"):
                captured_str = captured_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                captured_str = str(captured_at) if captured_at is not None else ""

            images.append(
                {
                    "id": img["id"],
                    "url": url,
                    "captured_at": captured_str,
                    "helmet_on": helmet_on,
                    "type": "Face Capture",
                }
            )

            # each image with helmet_on == False is treated as a violation
            if not helmet_on:
                violations.append(
                    {
                        "id": img["id"],
                        "timestamp": captured_str,
                        "location_name": row.get("location_name"),
                        "reason": "Helmet not worn",
                        "severity": "high",
                        "image_url": url,
                    }
                )

        result.append(
            {
                "id": wid,
                "name": row["name"],
                "phone": row["phone"],
                "location_name": row.get("location_name"),
                "company_name": row.get("company_name"),
                "joined_at": (
                    row["joined_at"].isoformat()
                    if hasattr(row["joined_at"], "isoformat")
                    else str(row["joined_at"])
                ),
                "images": images,
                "violations": violations,
            }
        )

    return result


@app.get("/api/workers/{worker_id}")
def get_worker(worker_id: int):
    row = fetch_worker_by_id(worker_id)
    if not row:
        raise HTTPException(status_code=404, detail="Worker not found")
    return row


def _list_media_urls(worker_id: int) -> list[dict]:
    """
    List media from MEDIA_ROOT/worker_{id}/ as /media/... urls.
    """
    folder = MEDIA_ROOT / f"worker_{worker_id}"
    if not folder.exists():
        return []
    items: list[dict] = []
    for fname in sorted(folder.iterdir()):
        if not fname.is_file():
            continue
        rel_url = f"/media/worker_{worker_id}/{fname.name}"
        captured = datetime.utcfromtimestamp(fname.stat().st_mtime).isoformat() + "Z"
        items.append(
            {
                "filename": fname.name,
                "url": f"{settings.MEDIA_BASE_URL}/worker_{worker_id}/{fname.name}",
                "captured_at": captured,
            }
        )
    return items


@app.get("/api/workers/{worker_id}/media")
def worker_media(worker_id: int):
    return _list_media_urls(worker_id)


@app.get("/api/workers/{worker_id}/violations")
def worker_violations(worker_id: int):
    sql = """
        SELECT id, detected_at, frame_path, sms_status, sms_sid, details
        FROM violation
        WHERE worker_id = %s
        ORDER BY detected_at DESC
        LIMIT 200
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (worker_id,))
            rows = cur.fetchall()
    finally:
        conn.close()
    formatted = []
    for r in rows:
        detected_at = r.get("detected_at")
        ts = detected_at.isoformat() if hasattr(detected_at, "isoformat") else str(detected_at)
        formatted.append(
            {
                "id": r.get("id"),
                "timestamp": ts,
                "frame_path": r.get("frame_path"),
                "sms_status": r.get("sms_status"),
                "sms_sid": r.get("sms_sid"),
                "details": r.get("details"),
            }
        )
    return formatted


# app/main.py

@app.post("/api/workers/register")
async def register_worker(
    face: UploadFile = File(...),
    name: str = Form(...),
    phone: str = Form(""),
    company_id: int = Form(...),
    location_id: int = Form(...),
    # frontend can send "true"/"false"; default is helmet_on = True
    helmet_on: bool = Form(True),
):
    """
    Register a new worker from an 'Unknown' detection.

    - Saves the worker in MySQL
    - Saves a face image file into MEDIA_ROOT/worker_{id}/
    - Computes embedding with DeepFace
    - Saves embedding linked to worker
    - Inserts an `image` row with helmet_on flag
    - Refreshes in-memory face gallery
    """
    try:
        # 1) read image bytes
        data = await face.read()
        nparr = np.frombuffer(data, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return JSONResponse(
                status_code=400,
                content={"error": "Could not decode face image"},
            )

        # 2) compute embedding (same model as detection)
        rep = DeepFace.represent(
            img_path=img_bgr,
            model_name="VGG-Face",
            enforce_detection=False,
        )
        embedding = rep[0]["embedding"]
        if not embedding or not np.isfinite(embedding).all():
            return JSONResponse(status_code=400, content={"error": "Invalid embedding"})

        # 3) insert worker
        worker_id = insert_worker(
            name=name,
            phone=phone,
            company_id=company_id,
            location_id=location_id,
        )

        # 4) save face image file
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"worker_{worker_id}_{ts}.jpg"
        worker_dir = MEDIA_ROOT / f"worker_{worker_id}"
        worker_dir.mkdir(parents=True, exist_ok=True)
        img_path = worker_dir / filename
        cv2.imwrite(str(img_path), img_bgr)

        # 5) insert image row (used for images tab + violations)
        insert_worker_image(
            worker_id=worker_id,
            filename=filename,
            location_id=location_id,
            company_id=company_id,
            name=name,
            helmet_on=helmet_on,
        )

        # 6) insert embedding in DB (comma-separated)
        insert_embedding(
            worker_id=worker_id,
            embedding=embedding,
            filename=filename,      # tie embedding to this image
            asset_id=filename,
            name=name,
            location_id=location_id,
            company_id=company_id,
        )

        # 7) also append to file-backed gallery for live recognition
        face_gallery.enroll(
            {
                "filename": str(img_path),
                "asset_id": filename,
                "name": name,
                "worker_id": worker_id,
                "location": location_id,
                "capture_datetime": datetime.now().isoformat(),
            },
            np.asarray(embedding, dtype=np.float32),
        )

        # 8) refresh gallery so new worker is recognized immediately
        reload_gallery()

        return {
            "status": "ok",
            "worker_id": worker_id,
            "message": f"Registered worker {name} and updated gallery",
        }

    except Exception as e:
        print("Error in /api/workers/register:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )
