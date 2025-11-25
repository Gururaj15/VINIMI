# app/alerts.py
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, List
from collections import deque
from threading import Lock

import phonenumbers
from twilio.base.exceptions import TwilioException
from twilio.rest import Client

from .config import get_settings
from .db import get_conn

settings = get_settings()

EVENTS_LOG_PATH = Path("logs/events.log")
EVENTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

RECENT_ALERTS_PATH = Path("logs/recent_alerts.log")
RECENT_ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
RECENT_ALERTS_MAX = 200
_recent_alerts: deque[Dict[str, Any]] = deque(maxlen=RECENT_ALERTS_MAX)
_recent_alerts_lock = Lock()

events_logger = logging.getLogger("vinimi_events")
events_logger.setLevel(logging.INFO)
if not any(
    isinstance(h, logging.FileHandler) and h.baseFilename == str(EVENTS_LOG_PATH)
    for h in events_logger.handlers
):
    handler = logging.FileHandler(EVENTS_LOG_PATH)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s\t%(message)s")
    handler.setFormatter(formatter)
    events_logger.addHandler(handler)


def log_event(kind: str, payload: Dict[str, Any]) -> None:
    try:
        record = {"type": kind, **payload}
        events_logger.info(json.dumps(record, default=str))
    except Exception:
        events_logger.exception("Failed to log event")


def _normalize_recent_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = {
        "id": entry.get("id")
        or f"log-{datetime.utcnow().isoformat()}-{entry.get('worker_id') or 'unknown'}",
        "timestamp": entry.get("timestamp") or datetime.utcnow().isoformat(),
        "worker_id": entry.get("worker_id"),
        "worker_name": entry.get("worker_name") or "Unknown",
        "phone": entry.get("phone"),
        "location_id": entry.get("location_id"),
        "location_name": entry.get("location_name") or "Unknown location",
        "sms_status": entry.get("sms_status"),
        "sms_sid": entry.get("sms_sid"),
        "details": entry.get("details") or {},
    }
    return cleaned


def _append_recent_alert(entry: Dict[str, Any]) -> None:
    cleaned = _normalize_recent_entry(entry)
    with _recent_alerts_lock:
        _recent_alerts.appendleft(cleaned)
    try:
        with RECENT_ALERTS_PATH.open("a") as fh:
            fh.write(json.dumps(cleaned, default=str) + "\n")
    except Exception as exc:
        log_event("alert.stream_write_error", {"error": str(exc)})


def load_recent_alerts_cache() -> None:
    if not RECENT_ALERTS_PATH.exists():
        return
    lines = deque(maxlen=RECENT_ALERTS_MAX)
    try:
        with RECENT_ALERTS_PATH.open("r") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    lines.append(line)
    except Exception:
        return

    entries: List[Dict[str, Any]] = []
    for line in reversed(lines):
        try:
            entry = json.loads(line)
            entries.append(_normalize_recent_entry(entry))
        except Exception:
            continue

    with _recent_alerts_lock:
        _recent_alerts.clear()
        for entry in entries:
            _recent_alerts.append(entry)


def get_recent_alert_entries(limit: int) -> List[Dict[str, Any]]:
    limit = max(1, min(limit, RECENT_ALERTS_MAX))
    with _recent_alerts_lock:
        return list(list(_recent_alerts)[:limit])


def add_recent_alert_entry(entry: Dict[str, Any]) -> None:
    _append_recent_alert(entry)


def normalize_phone(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    try:
        raw = raw.strip()
        region = None if raw.startswith("+") else "US"
        parsed = phonenumbers.parse(raw, region)
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return None


def should_rate_limit(worker_id: int, minutes: int) -> bool:
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM violation
                WHERE worker_id = %s
                  AND type = 'HELMET'
                  AND detected_at >= %s
                LIMIT 1
                """,
                (worker_id, cutoff),
            )
            return cur.fetchone() is not None
    except Exception as exc:
        log_event(
            "alert.rate_limit_error",
            {"worker_id": worker_id, "error": str(exc)},
        )
        return False
    finally:
        if conn is not None:
            conn.close()


def record_violation(
    worker_id: Optional[int],
    phone: Optional[str],
    frame_path: Optional[str],
    sms_sid: Optional[str],
    sms_status: Optional[str],
    details: Optional[Dict[str, Any]],
    *,
    worker_name: Optional[str] = None,
    location_id: Optional[int] = None,
    location_name: Optional[str] = None,
) -> int:
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO violation (
                    worker_id,
                    worker_name,
                    phone,
                    location_id,
                    location_name,
                    type,
                    detected_at,
                    frame_path,
                    sms_sid,
                    sms_status,
                    details
                )
                VALUES (%s, %s, %s, %s, %s, 'HELMET', %s, %s, %s, %s, %s)
                """,
                (
                    worker_id,
                    worker_name,
                    phone,
                    location_id,
                    location_name,
                    datetime.utcnow(),
                    frame_path,
                    sms_sid,
                    sms_status,
                    json.dumps(details or {}, default=str),
                ),
            )
        conn.commit()
        return int(cur.lastrowid)
    except Exception as exc:
        log_event(
            "alert.violation_error",
            {
                "worker_id": worker_id,
                "sms_status": sms_status,
                "error": str(exc),
            },
        )
        return -1
    finally:
        if conn is not None:
            conn.close()


def update_violation_status(
    violation_id: int,
    sms_status: str,
    sms_sid: Optional[str] = None,
    phone: Optional[str] = None,
) -> None:
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            fields = ["sms_status = %s"]
            params: list[Any] = [sms_status]
            if sms_sid is not None:
                fields.append("sms_sid = %s")
                params.append(sms_sid)
            if phone is not None:
                fields.append("phone = %s")
                params.append(phone)

            params.append(violation_id)
            sql = f"UPDATE violation SET {', '.join(fields)} WHERE id = %s"
            cur.execute(sql, params)
        conn.commit()
    except Exception as exc:
        log_event(
            "alert.update_violation_error",
            {"violation_id": violation_id, "error": str(exc)},
        )
    finally:
        if conn is not None:
            conn.close()


def send_sms(phone_e164: str, message: str) -> tuple[Optional[str], str]:
    if (
        not settings.TWILIO_ACCOUNT_SID
        or not settings.TWILIO_AUTH_TOKEN
        or not settings.TWILIO_FROM_NUMBER
    ):
        return None, "not_configured"

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    try:
        msg = client.messages.create(
            to=phone_e164,
            from_=settings.TWILIO_FROM_NUMBER,
            body=message[:160],
        )
        return msg.sid, msg.status or "sent"
    except TwilioException as exc:
        log_event(
            "alert.sms_error",
            {"phone": phone_e164, "error": str(exc)},
        )
        return None, "twilio_error"


def maybe_send_helmet_alert(
    violation_id: int,
    worker_id: int,
    phone_raw: Optional[str],
    frame_path: Optional[str],
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    try:
        if not settings.ALERTS_SMS_ENABLED:
            update_violation_status(violation_id, "disabled")
            log_event(
                "alert.skipped",
                {"worker_id": worker_id, "reason": "disabled"},
            )
            return "disabled"

        phone_e164 = normalize_phone(phone_raw or "")
        if not phone_e164:
            update_violation_status(violation_id, "no_phone")
            log_event(
                "alert.skipped",
                {"worker_id": worker_id, "reason": "invalid_phone", "raw": phone_raw},
            )
            return "no_phone"

        cooldown = max(1, settings.ALERTS_COOLDOWN_MINUTES)
        if should_rate_limit(worker_id, cooldown):
            update_violation_status(violation_id, "rate_limited", phone=phone_e164)
            log_event(
                "alert.skipped",
                {"worker_id": worker_id, "reason": "rate_limited"},
            )
            return "rate_limited"

        detection_time = datetime.utcnow().strftime("%H:%M UTC")
        worker_name = (extra or {}).get("name") or "worker"
        message = (
            f"VINIMI: Helmet not detected for {worker_name} at {detection_time}. "
            "Please wear a hard hat."
        )[:155]

        sid, status = send_sms(phone_e164, message)
        final_status = status or "sent"
        update_violation_status(
            violation_id,
            final_status,
            sms_sid=sid,
            phone=phone_e164,
        )
        add_recent_alert_entry(
            {
                "worker_id": worker_id,
                "worker_name": worker_name,
                "phone": phone_e164,
                "location_id": extra.get("location_id") if extra else None,
                "location_name": (extra or {}).get("location_name"),
                "sms_status": final_status,
                "sms_sid": sid,
                "details": {**(extra or {}), "type": "helmet_alert"},
                "timestamp": (extra or {}).get("detected_at") or datetime.utcnow().isoformat(),
            }
        )
        log_event(
            "alert.sent",
            {"worker_id": worker_id, "status": status, "sid": sid},
        )
        return status
    except Exception as exc:
        log_event(
            "alert.error",
            {"worker_id": worker_id, "error": str(exc)},
        )
        update_violation_status(violation_id, "error")
        return "error"
