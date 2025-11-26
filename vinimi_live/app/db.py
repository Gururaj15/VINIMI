# app/db.py
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pymysql
from dotenv import load_dotenv

# Load local env vars from vinimi_live/.env if present (non-fatal if missing)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

# ---------- LOCAL MYSQL CONFIG ----------
LOCAL_DB_HOST = os.getenv("LOCAL_DB_HOST", "127.0.0.1")
LOCAL_DB_PORT = int(os.getenv("LOCAL_DB_PORT", "3306"))
LOCAL_DB_USER = os.getenv("LOCAL_DB_USER", "root")
LOCAL_DB_PASS = os.getenv("LOCAL_DB_PASS", "")
LOCAL_DB_NAME = os.getenv("LOCAL_DB_NAME", "vinimi_local")

VIOLATION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS violation (
  id INT NOT NULL AUTO_INCREMENT,
  worker_id INT NULL,
  worker_name VARCHAR(255) NULL,
  phone VARCHAR(32) NULL,
  location_id INT NULL,
  location_name VARCHAR(255) NULL,
  type ENUM('HELMET') NOT NULL DEFAULT 'HELMET',
  detected_at DATETIME NOT NULL,
  frame_path VARCHAR(255) NULL,
  sms_sid VARCHAR(64) NULL,
  sms_status VARCHAR(32) NULL,
  details JSON NULL,
  PRIMARY KEY (id),
  KEY idx_worker_time (worker_id, detected_at),
  KEY idx_location_time (location_id, detected_at),
  CONSTRAINT violation_worker_fk
    FOREIGN KEY (worker_id) REFERENCES worker(id)
    ON DELETE SET NULL,
  CONSTRAINT violation_location_fk
    FOREIGN KEY (location_id) REFERENCES location(id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

ALTER_WORKER_PHONE_SQL = "ALTER TABLE worker MODIFY phone VARCHAR(32) NOT NULL;"

def get_company_by_id(company_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM company WHERE id=%s LIMIT 1", (company_id,))
            row = cur.fetchone()
            return row
    finally:
        conn.close()

def get_manager_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, password_hash, company_id FROM manager WHERE email=%s LIMIT 1",
                (email,),
            )
            return cur.fetchone()
    finally:
        conn.close()

def get_manager_by_id(manager_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, password_hash, company_id, created_at FROM manager WHERE id=%s LIMIT 1",
                (manager_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()

def insert_manager(name: str, email: str, password_hash: str, company_id: int) -> int:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO manager (name, email, password_hash, company_id)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, password_hash, company_id),
            )
            manager_id = cur.lastrowid
            conn.commit()
            return int(manager_id)
    finally:
        conn.close()

def update_manager(
    manager_id: int,
    name: Optional[str] = None,
    company_id: Optional[int] = None,
    password_hash: Optional[str] = None,
) -> bool:
    fields = []
    params = []
    if name is not None:
        fields.append("name=%s")
        params.append(name)
    if company_id is not None:
        fields.append("company_id=%s")
        params.append(company_id)
    if password_hash is not None:
        fields.append("password_hash=%s")
        params.append(password_hash)
    if not fields:
        return False
    params.append(manager_id)
    sql = f"UPDATE manager SET {', '.join(fields)} WHERE id=%s"
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return True
    finally:
        conn.close()


def get_conn() -> pymysql.connections.Connection:
    conn = pymysql.connect(
        host=LOCAL_DB_HOST,
        port=LOCAL_DB_PORT,
        user=LOCAL_DB_USER,
        password=LOCAL_DB_PASS,
        database=LOCAL_DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    return conn


def ensure_violation_table() -> None:
    """
    Ensure the violation table exists (and phone column is wide enough)
    so alert logging never fails even if migrations weren't run manually.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(VIOLATION_TABLE_SQL)
            try:
                cur.execute(ALTER_WORKER_PHONE_SQL)
            except Exception:
                pass

            legacy_alters = [
                "ALTER TABLE violation ADD COLUMN worker_name VARCHAR(255) NULL AFTER worker_id",
                "ALTER TABLE violation ADD COLUMN location_id INT NULL AFTER phone",
                "ALTER TABLE violation ADD COLUMN location_name VARCHAR(255) NULL AFTER location_id",
                "ALTER TABLE violation ADD KEY idx_location_time (location_id, detected_at)",
                (
                    "ALTER TABLE violation "
                    "ADD CONSTRAINT violation_location_fk "
                    "FOREIGN KEY (location_id) REFERENCES location(id) "
                    "ON DELETE SET NULL"
                ),
            ]
            for statement in legacy_alters:
                try:
                    cur.execute(statement)
                except Exception:
                    # Column / key / constraint may already exist.
                    pass
    finally:
        conn.close()


def get_table_as_df(table_name: str) -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql(f"SELECT * FROM `{table_name}`", conn)
    finally:
        conn.close()


# ---------- WORKER / EMBEDDINGS HELPERS ----------

def insert_worker(
    name: str,
    phone: str,
    company_id: int,
    location_id: int,
) -> int:
    """
    Insert a worker row and return its auto-increment id.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        sql = """
            INSERT INTO worker (name, phone, company_id, location_id, joined_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        joined_at = datetime.now().date()
        cur.execute(sql, (name, phone, company_id, location_id, joined_at))
        worker_id = cur.lastrowid
        conn.commit()
        return int(worker_id)
    finally:
        conn.close()


def insert_embedding(
    worker_id: int,
    embedding: List[float],
    filename: Optional[str] = None,
    asset_id: Optional[str] = None,
    name: Optional[str] = None,
    location_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> None:
    """
    Insert an embedding row using your existing `embeddings` schema.
    Embedding is stored as a comma-separated float string (not JSON).
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        emb_str = ",".join(f"{float(x):.6f}" for x in embedding)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if filename is None:
            filename = f"worker_{worker_id}_{ts}.jpg"
        if asset_id is None:
            asset_id = filename

        sql = """
            INSERT INTO embeddings (
                filename,
                asset_id,
                location_id,
                company_id,
                capture_datetime,
                name,
                worker_id,
                embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cur.execute(
            sql,
            (
                filename,
                asset_id,
                str(location_id) if location_id is not None else None,
                str(company_id) if company_id is not None else None,
                datetime.now(),
                name,
                worker_id,
                emb_str,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_workers() -> List[Dict[str, Any]]:
    """
    Return workers joined with company and location for the /api/workers endpoint.

    Matches the WorkerApi type used in the frontend:
      id, name, phone, company_id, location_id, joined_at,
      company_name, location_name
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        sql = """
            SELECT
                w.id,
                w.name,
                w.phone,
                w.company_id,
                w.location_id,
                w.joined_at,
                c.name AS company_name,
                l.name AS location_name
            FROM worker AS w
            LEFT JOIN company AS c ON w.company_id = c.id
            LEFT JOIN location AS l ON w.location_id = l.id
            ORDER BY w.id DESC
        """
        cur.execute(sql)
        rows = cur.fetchall()  # DictCursor → list[dict]
        return rows
    finally:
        conn.close()

def fetch_workers_basic() -> List[Dict[str, Any]]:
    """
    Return workers with joined company/location info.
    """
    sql = """
        SELECT
            w.id,
            w.name,
            w.phone,
            w.joined_at,
            w.company_id,
            w.location_id,
            c.name AS company_name,
            l.name AS location_name
        FROM worker w
        LEFT JOIN company c ON w.company_id = c.id
        LEFT JOIN location l ON w.location_id = l.id
        ORDER BY w.id DESC
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()


def fetch_worker_by_id(worker_id: int) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT
            w.id,
            w.name,
            w.phone,
            w.company_id,
            w.location_id,
            c.name AS company_name,
            l.name AS location_name
        FROM worker AS w
        LEFT JOIN company AS c ON w.company_id = c.id
        LEFT JOIN location AS l ON w.location_id = l.id
        WHERE w.id = %s
        LIMIT 1
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, (worker_id,))
        row = cur.fetchone()
        return row
    finally:
        conn.close()


def fetch_worker_images(worker_id: int) -> List[Dict[str, Any]]:
    """
    Return all images for a worker (used for images + violations).
    """
    sql = """
        SELECT
            id,
            filename,
            capture_datetime,
            helmet_on
        FROM image
        WHERE worker_id = %s
        ORDER BY capture_datetime DESC
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, (worker_id,))
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()


def insert_worker_image(
    worker_id: int,
    filename: str,
    location_id: int,
    company_id: int,
    name: str,
    helmet_on: bool,
) -> int:
    """
    Insert a row into `image` table for a captured worker face.
    We reuse filename as asset_id to keep things simple.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        asset_id = filename
        sql = """
            INSERT INTO image (
                asset_id,
                filename,
                location_id,
                company_id,
                capture_datetime,
                worker_id,
                name,
                helmet_on
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(
            sql,
            (
                asset_id,
                filename,
                location_id,
                company_id,
                datetime.now(),
                worker_id,
                name,
                1 if helmet_on else 0,
            ),
        )
        image_id = cur.lastrowid
        conn.commit()
        return image_id
    finally:
        conn.close()


def list_violations(limit: int = 200, sms_only: bool = False) -> List[Dict[str, Any]]:
    """
    Return violation rows enriched with worker/location info. If sms_only is True,
    limit to rows where an SMS was actually attempted or sent.
    """
    limit = max(1, min(limit, 500))
    conn = get_conn()
    try:
        cur = conn.cursor()
        sql = """
            SELECT
                v.id,
                v.worker_id,
                COALESCE(v.worker_name, w.name) AS worker_name,
                v.phone,
                COALESCE(v.location_id, w.location_id) AS location_id,
                COALESCE(v.location_name, l.name) AS location_name,
                v.detected_at,
                v.sms_status,
                v.sms_sid,
                v.frame_path,
                v.details
            FROM violation AS v
            LEFT JOIN worker AS w ON v.worker_id = w.id
            LEFT JOIN location AS l ON COALESCE(v.location_id, w.location_id) = l.id
        """
        conditions: List[str] = []
        if sms_only:
            conditions.append(
                "(COALESCE(v.sms_sid, '') <> '' OR "
                "v.sms_status IN ('sent', 'queued', 'delivered'))"
            )
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY v.detected_at DESC LIMIT %s"
        cur.execute(sql, (limit,))
        rows = cur.fetchall()
    finally:
        conn.close()

    formatted: List[Dict[str, Any]] = []
    for row in rows:
        details = row.get("details")
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                pass
        detected_at = row.get("detected_at")
        if hasattr(detected_at, "isoformat"):
            timestamp = detected_at.isoformat()
        else:
            timestamp = detected_at

        formatted.append(
            {
                "id": row.get("id"),
                "worker_id": row.get("worker_id"),
                "worker_name": row.get("worker_name") or "Unknown",
                "phone": row.get("phone"),
                "location_id": row.get("location_id"),
                "location_name": row.get("location_name") or "Unknown location",
                "timestamp": timestamp,
                "sms_status": row.get("sms_status"),
                "sms_sid": row.get("sms_sid"),
                "frame_path": row.get("frame_path"),
                "details": details,
            }
        )

    return formatted
