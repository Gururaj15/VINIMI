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
import os
import base64
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import deque
import requests

from .video.face_recognition_video import analyze_video_face_recognition

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
def _env_flag(name: str, default: str = "true") -> bool:
    return (os.getenv(name, default) or "").strip().lower() in ("1", "true", "yes", "on")


VLM_BASE = os.getenv("VLM_BASE", "https://router.huggingface.co/v1")
_model_raw = os.getenv("VLM_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")
VLM_MODEL = _model_raw.split("=", 1)[1] if _model_raw.lower().startswith("vlm_model=") else _model_raw
VLM_TIMEOUT = float(os.getenv("VLM_TIMEOUT", "120"))
VLM_ENABLED = _env_flag("VLM_ENABLED", "true")
VLM_API_KEY = os.getenv("HF_API_KEY") or os.getenv("VLM_API_KEY")
# Registration flow
REG_TARGET_SAMPLES = int(os.getenv("REG_TARGET_SAMPLES", "7"))
REG_SESSION_TIMEOUT = int(os.getenv("REG_SESSION_TIMEOUT", "120"))
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
        faces = result.get("faces") or []
        ts = datetime.utcnow().isoformat() + "Z"
        records = []
        records.append({
            "ts": ts,
            "name": person.get("name") or "Unknown",
            "worker_id": person.get("worker_id"),
            "company_id": person.get("company_id"),
            "location_id": person.get("location_id"),
            "helmet_on": bool(ppe.get("helmet_on")),
            "is_unknown": not person.get("worker_id"),
            "similarity": person.get("similarity"),
            "role": "primary",
        })
        for idx, face in enumerate(faces):
            face_ppe = (face.get("ppe") or {})
            records.append({
                "ts": ts,
                "name": face.get("name") or "Unknown",
                "worker_id": face.get("worker_id"),
                "helmet_on": face_ppe.get("helmet_on", ppe.get("helmet_on")),
                "similarity": face.get("similarity"),
                "face_index": idx,
                "role": "face",
            })
        day_file = LOGS_DIR / f"{ts[:10]}.log"
        with day_file.open("a", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(_json_safe(rec), default=str) + "\n")
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
        _json_safe({
            "source": source,
            "worker_id": person.get("worker_id"),
            "name": person.get("name"),
            "helmet_on": ppe.get("helmet_on"),
            "camera_id": result.get("camera_id"),
        }),
    )
    for idx, face in enumerate(result.get("faces") or []):
        face_ppe = (face.get("ppe") or {})
        log_event(
            "detection.face",
            _json_safe({
                "source": source,
                "face_index": idx,
                "worker_id": face.get("worker_id"),
                "name": face.get("name"),
                "helmet_on": face_ppe.get("helmet_on", ppe.get("helmet_on")),
                "similarity": face.get("similarity"),
                "camera_id": result.get("camera_id"),
            }),
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

    return _json_safe(result)


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



# In-memory registration sessions
registration_sessions: dict[str, dict] = {}

@app.get("/api/live/recent-alerts")
def recent_alerts(limit: int = 20) -> list[dict]:
    """Return SMS alerts pulled from the recent alerts cache (file-backed)."""
    limit = max(1, min(limit, 200))
    return get_recent_alert_entries(limit)


# ---------------- Guided Registration Endpoints -----------------


@app.post("/api/workers/register/start")
def register_start(payload: dict):
    _prune_sessions()
    sess = _new_session()
    return {
        "session_id": sess["session_id"],
        "status": "collecting",
        "next_instruction": "Face the camera directly and stay still.",
        "target_samples": sess["target_samples"],
    }


def _extract_best_face(img_bgr: np.ndarray):
    try:
        faces = DeepFace.extract_faces(img_path=img_bgr, enforce_detection=False, detector_backend="opencv", align=False)
    except Exception:
        faces = []
    if not faces:
        return None
    # pick largest
    best = max(faces, key=lambda f: (f.get("facial_area") or {}).get("w", 0) * (f.get("facial_area") or {}).get("h", 0))
    fa = best.get("facial_area") or {}
    x, y, w, h = int(fa.get("x", 0)), int(fa.get("y", 0)), int(fa.get("w", 0)), int(fa.get("h", 0))
    x = max(0, x); y = max(0, y)
    crop = img_bgr[y:y+h, x:x+w].copy() if h > 0 and w > 0 else img_bgr
    emb = best.get("embedding") or []
    if not emb:
        try:
            rep = DeepFace.represent(img_path=crop, model_name="VGG-Face", enforce_detection=False)
            emb = rep[0]["embedding"] if rep else []
        except Exception:
            emb = []
    return crop, emb


@app.post("/api/workers/register/capture")
async def register_capture(session_id: str = Form(...), pose_hint: Optional[str] = Form(None), frame: UploadFile = File(...)):
    sess = _get_session(session_id)
    if not sess:
        return JSONResponse(status_code=404, content={"error": "Session not found or expired"})
    try:
        data = await frame.read()
        nparr = np.frombuffer(data, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return JSONResponse(status_code=400, content={"error": "Could not decode image"})
        res = _extract_best_face(img_bgr)
        if not res:
            return {
                "status": "no_face",
                "next_instruction": "We couldn’t see your face. Move closer and face the camera.",
                "collected": len(sess["collected"]),
                "target": sess["target_samples"],
            }
        crop, emb = res
        if not emb:
            return {
                "status": "no_face",
                "next_instruction": "Face not clear. Try again.",
                "collected": len(sess["collected"]),
                "target": sess["target_samples"],
            }
        emb_arr = np.asarray(emb, dtype=np.float32).reshape(-1)
        _add_sample(sess, emb_arr.tolist(), pose_hint, crop)
        if len(sess["collected"]) >= sess["target_samples"]:
            return {
                "status": "enough_samples",
                "next_instruction": "Enough samples captured. Please confirm worker details.",
                "collected": len(sess["collected"]),
                "target": sess["target_samples"],
            }
        return {
            "status": "collecting",
            "next_instruction": "Turn slightly and hold still for another capture.",
            "collected": len(sess["collected"]),
            "target": sess["target_samples"],
        }
    except Exception as exc:
        print("⚠️ [register_capture]", exc)
        return JSONResponse(status_code=500, content={"error": "Capture failed"})


@app.post("/api/workers/register/complete")
async def register_complete(
    session_id: str = Form(...),
    name: str = Form(...),
    phone: str = Form(""),
    company_id: str = Form(""),
    location_id: str = Form(""),
):
    sess = _get_session(session_id)
    if not sess:
        return JSONResponse(status_code=404, content={"error": "Session not found or expired"})
    try:
        if not sess.get("collected"):
            return JSONResponse(status_code=400, content={"error": "No samples collected"})
        embs = [np.asarray(s["embedding"], dtype=np.float32) for s in sess["collected"]]
        agg = np.mean(embs, axis=0)
        emb_csv = ",".join(str(float(x)) for x in agg)

        # convert IDs safely
        try:
            company_id_int = int(company_id) if str(company_id).strip() else 0
        except ValueError:
            return JSONResponse(status_code=400, content={"error": "Invalid company_id"})
        try:
            location_id_int = int(location_id) if str(location_id).strip() else 0
        except ValueError:
            return JSONResponse(status_code=400, content={"error": "Invalid location_id"})

        # save representative image
        img_dir = MEDIA_ROOT / "registered"
        img_dir.mkdir(parents=True, exist_ok=True)
        img_path = img_dir / f"worker_{session_id}.jpg"
        rep = sess["collected"][0].get("frame_bgr")
        if rep is not None:
            cv2.imwrite(str(img_path), rep)
        filename = img_path.name

        # append to embeddings CSV
        csv_path = Path(settings.EMBEDDINGS_CSV)
        row = {
            "filename": filename,
            "id": "",
            "asset_id": session_id,
            "location_id": location_id or "",
            "company_id": company_id or "",
            "capture_datetime": datetime.utcnow().isoformat(),
            "name": name,
            "worker_id": "",
            "embedding": emb_csv,
            "phone": phone,
            "location": location_id or "",
        }
        import pandas as pd

        try:
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            else:
                df = pd.DataFrame([row])
            df.to_csv(csv_path, index=False)
        except Exception as exc:
            print("⚠️ [register_complete] failed to write CSV:", exc)
            return JSONResponse(status_code=500, content={"error": "Failed to save embedding"})

        # also persist to database worker / image / embedding tables
        try:
            worker_id_db = insert_worker(
                name=name,
                phone=phone or "",
                company_id=company_id_int,
                location_id=location_id_int,
            )
            insert_worker_image(
                worker_id=worker_id_db,
                filename=filename,
                location_id=location_id_int,
                company_id=company_id_int,
                name=name,
                helmet_on=True,
            )
            insert_embedding(
                worker_id=worker_id_db,
                embedding=agg.tolist(),
                filename=filename,
                asset_id=session_id,
                name=name,
                location_id=location_id_int,
                company_id=company_id_int,
            )
        except Exception as exc:
            print("⚠️ [register_complete] DB append failed:", exc)
            return JSONResponse(status_code=500, content={"error": "Failed to save worker to DB"})

        # refresh gallery
        try:
            reload_gallery()
        except Exception as exc:
            print("⚠️ [register_complete] reload_gallery error:", exc)

        registration_sessions.pop(session_id, None)
        return {
            "status": "ok",
            "message": "Worker enrolled successfully.",
            "worker_id": worker_id_db,
        }
    except Exception as exc:
        print("⚠️ [register_complete]", exc)
        return JSONResponse(status_code=500, content={"error": "Registration failed"})


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
                out.append(_json_safe(obj))
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


def _resize_image_for_vlm(img_bgr: np.ndarray, max_dim: int = 512) -> bytes:
    """
    Downscale large images to keep VLM latency lower and responses more stable.
    Returns JPEG bytes.
    """
    h, w = img_bgr.shape[:2]
    scale = min(1.0, max_dim / max(h, w))
    if scale < 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        img_bgr = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise ValueError("Failed to encode image for VLM")
    return buf.tobytes()


def _json_safe(obj):
    """
    Recursively replace NaN/inf floats with None so JSON serialization never fails.
    """
    if isinstance(obj, float):
        if not np.isfinite(obj):
            return None
        return obj
    if isinstance(obj, (np.generic,)):
        return _json_safe(obj.item())
    if isinstance(obj, np.ndarray):
        return _json_safe(obj.tolist())
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(x) for x in obj]
    return obj


# ---------------- Registration Sessions -----------------





def _prune_sessions():
    now = time.time()
    to_delete = []
    for sid, sess in registration_sessions.items():
        if now - sess.get("created_at", now) > REG_SESSION_TIMEOUT:
            to_delete.append(sid)
    for sid in to_delete:
        registration_sessions.pop(sid, None)


def _new_session(target_samples: int | None = None) -> dict:
    sid = str(uuid.uuid4())
    session = {
        "session_id": sid,
        "created_at": time.time(),
        "target_samples": target_samples or REG_TARGET_SAMPLES,
        "collected": [],
    }
    registration_sessions[sid] = session
    return session


def _get_session(session_id: str) -> Optional[dict]:
    _prune_sessions()
    return registration_sessions.get(session_id)


def _add_sample(session: dict, embedding: list[float], pose: Optional[str], frame_bgr: np.ndarray):
    session["collected"].append({"embedding": embedding, "pose": pose, "frame_bgr": frame_bgr})


def _call_vlm(image_bytes: bytes, question: str, detector_facts: dict) -> str:
    """
    Call the configured vision LLM via HTTP (HF router, OpenAI-compatible chat).
    """
    if not VLM_ENABLED or not VLM_MODEL:
        return ""
    if not VLM_API_KEY or not VLM_BASE:
        return ""
    try:
        b64_img = base64.b64encode(image_bytes).decode() if image_bytes else ""
        content_text = question.strip() or "Describe the safety status in this image."
        facts_json_pretty = json.dumps(detector_facts or {}, indent=2, default=str)[:4000]
        facts_note = (
            "Here are structured detection facts from VINIMI's detectors as JSON. "
            "If a worker name/helmet flag is present, trust it."
        )
        user_content: list[dict[str, object]] = [
            {
                "type": "text",
                "text": (
                    f"{facts_note}\n```json\n{facts_json_pretty}\n```\n\n"
                    f"User question: {content_text}\n"
                    "Using BOTH the image and these JSON facts, answer. "
                    "For identity/PPE, trust JSON over pixels."
                ),
            }
        ]
        if b64_img:
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})

        system_prompt = (
            "You are VINIMI, an AI assistant for PPE (helmet) compliance and worker identification "
            "on industrial/construction sites. You receive (1) an image frame and (2) structured JSON facts "
            "from detectors (face recognition + helmet detector). Rules: "
            "- For identity/PPE/company/location/similarity questions, ALWAYS trust the JSON facts over the raw pixels. "
            "- For general description, use both the image and JSON. "
            "- If is_unknown=true, do NOT invent a name; say the worker is unknown. "
            "- Answer concisely in 1–3 sentences unless asked otherwise."
        )

        payload = {
            "model": VLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 256,
        }
        log_fields = {
            "name": (detector_facts or {}).get("person", {}).get("name") or detector_facts.get("name"),
            "helmet_on": (detector_facts or {}).get("ppe", {}).get("helmet_on") or detector_facts.get("helmet_on"),
            "is_unknown": (detector_facts or {}).get("person", {}).get("worker_id") is None
            if detector_facts
            else None,
        }
        print(f"[VLM] calling model={VLM_MODEL} with detector facts: {log_fields}")
        resp = requests.post(
            f"{VLM_BASE.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {VLM_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=VLM_TIMEOUT,
        )
        if resp.status_code != 200:
            print("⚠️ [VLM call failed] status", resp.status_code, resp.text)
            return ""
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        return (choices[0].get("message") or {}).get("content") or ""
    except Exception as exc:
        print("⚠️ [VLM call failed]:", exc)
        return ""


@app.post("/api/ask-vlm")
async def ask_vlm(question: str = Form(""), frame: UploadFile | None = File(None)):
    """
    Analyze an uploaded frame (helmet + face recognition) and, if available,
    ask a local Ollama vision model (VLM) to answer the user's question.
    """
    try:
        analysis: dict = {}
        img_bytes: bytes | None = None

        is_video = False
        video_facts = None

        if frame is not None:
            data = await frame.read()
            content_type = frame.content_type or ""
            if content_type.startswith("video/"):
                is_video = True
                videos_dir = MEDIA_ROOT / "videos"
                videos_dir.mkdir(parents=True, exist_ok=True)
                filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{frame.filename}"
                video_path = videos_dir / filename
                with open(video_path, "wb") as f:
                    f.write(data)

                try:
                    video_result = analyze_video_face_recognition(
                        str(video_path),
                        n_segments=5,
                        similarity_threshold=settings.FACE_SIM_THRESHOLD,
                        save_annotated=False,
                        media_root=MEDIA_ROOT,
                        sample_frames=10,
                        embeddings_csv_path=settings.EMBEDDINGS_CSV,
                    )
                    video_facts = {
                        "mode": "video",
                        "majority": video_result.get("majority"),
                        "segments": video_result.get("segments"),
                        "annotated_video_url": video_result.get("annotated_video_url"),
                        "video_url": f"{settings.MEDIA_BASE_URL}/videos/{video_path.name}",
                        "snapshot_url": video_result.get("snapshot_url"),
                    }
                    majority = video_result.get("majority") or {}
                    rep_frame = video_result.get("representative_frame")
                    if rep_frame is not None:
                        try:
                            img_bytes = _resize_image_for_vlm(rep_frame)
                        except Exception:
                            img_bytes = None
                    else:
                        img_bytes = None

                    analysis = {"video_facts": video_facts}
                    maj_name = majority.get("name")
                    if maj_name and maj_name != "Unknown":
                        analysis["person"] = {
                            "name": maj_name,
                            "worker_id": None,
                            "similarity": majority.get("similarity"),
                            "location": majority.get("location"),
                            "helmet_on": majority.get("helmet_on"),
                        }
                except Exception as exc:
                    print("⚠️ [video analyze error]:", exc)
                    analysis = {"video_facts": {"error": str(exc)}}
            else:
                nparr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    return JSONResponse(status_code=400, content={"error": "Could not decode image"})

                analysis = analyze_frame_bgr(img)
                try:
                    img_bytes = _resize_image_for_vlm(img)
                except Exception:
                    img_bytes = data  # fallback if resize fails

        answer = ""
        if VLM_ENABLED and VLM_MODEL and img_bytes is not None:
            answer = _call_vlm(img_bytes or b"", question or "", analysis)
        # If the model is disabled or punts, fall back to deterministic facts (images only)
        if not is_video:
            person_name = (analysis.get("person") or {}).get("name") or "Unknown"
            helmet_flag = (analysis.get("ppe") or {}).get("helmet_on")
            if (not answer or "not enough visual detail" in answer.lower()) and person_name != "Unknown":
                sim = (analysis.get("person") or {}).get("similarity")
                sim_txt = f" (similarity {sim:.2f})" if sim is not None else ""
                helmet_txt = (
                    " Helmet on." if helmet_flag else " Helmet off."
                    if helmet_flag is not None else ""
                )
                answer = f"Detected worker: {person_name}{sim_txt}.{helmet_txt}".strip()
        if not answer:
            if is_video and video_facts:
                maj = (video_facts.get("majority") or {})
                name = maj.get("name") or "Unknown"
                helmet_flag = maj.get("helmet_on")
                helmet_txt = (
                    "helmet on" if helmet_flag else "helmet off" if helmet_flag is not None else "helmet status unknown"
                )
                answer = f"Video analysis: detected worker {name} ({helmet_txt})."
            else:
                person_name = (analysis.get("person") or {}).get("name") or "Unknown"
                helmet_flag = (analysis.get("ppe") or {}).get("helmet_on")
                helmet_txt = (
                    "Helmet on" if helmet_flag else "Helmet off" if helmet_flag is not None else "Helmet status unknown"
                )
                answer = f"Detected worker: {person_name}. {helmet_txt}."
        resp = {"answer": answer, "analysis": _json_safe(analysis)}
        if is_video:
            resp["video_facts"] = _json_safe(video_facts or {})
            snap = (video_facts or {}).get("snapshot_url")
            if snap:
                resp["analysis"] = {**resp["analysis"], "image_url": snap}
        return resp
    except Exception as e:
        print("Error in /api/ask-vlm:", e)
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
