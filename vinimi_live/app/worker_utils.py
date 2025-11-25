# app/worker_utils.py
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, List

import cv2
from deepface import DeepFace

from .db import insert_embedding, get_conn


IMAGES_ROOT = os.getenv("WORKER_IMAGES_ROOT", "worker_images")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_worker_image_record(
    worker_id: int,
    img_bgr,
    name: str,
    company_id: int,
    location_id: int,
) -> str:
    """
    Save worker image to disk and create an `image` table row.
    Returns filename.
    """
    ensure_dir(IMAGES_ROOT)
    worker_dir = os.path.join(IMAGES_ROOT, str(worker_id))
    ensure_dir(worker_dir)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{worker_id}_{ts}.jpg"
    filepath = os.path.join(worker_dir, filename)

    cv2.imwrite(filepath, img_bgr)

    conn = get_conn()
    try:
        cur = conn.cursor()
        asset_id = filename  # simple 1:1 mapping
        sql = """
            INSERT INTO image (
                asset_id, filename, location_id, company_id,
                capture_datetime, worker_id, name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
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
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return filename


def compute_embedding_vgg(img_bgr) -> List[float]:
    rep = DeepFace.represent(img_path=img_bgr, model_name="VGG-Face", enforce_detection=False)
    return rep[0]["embedding"]
