# app/detection.py
from datetime import datetime
from typing import Any, Dict, List
import os
import tempfile

import cv2
import numpy as np
from ultralytics import YOLO
from deepface import DeepFace

from .config import get_settings
from .face_gallery import face_gallery

settings = get_settings()

yolo_model: YOLO | None = None


def init_models() -> None:
    global yolo_model
    if yolo_model is None:
        yolo_model = YOLO(settings.YOLO_MODEL_PATH)
    if face_gallery.embeddings is None or not face_gallery.imageid_to_info:
        try:
            face_gallery.load()
        except Exception as exc:
            print("⚠️ [FaceGallery] load failed:", exc)


def _ensure_gallery() -> bool:
    if face_gallery.embeddings is None or not face_gallery.asset_ids:
        try:
            face_gallery.load()
        except Exception as exc:
            print("⚠️ [FaceGallery] load failed:", exc)
    return face_gallery.embeddings is not None and bool(face_gallery.asset_ids)


def _cosine_sim(query_emb: np.ndarray, gallery: np.ndarray) -> np.ndarray:
    q = np.asarray(query_emb, dtype=np.float32)
    q_norm = np.linalg.norm(q)
    if not np.isfinite(q_norm) or q_norm < 1e-6:
        return np.zeros((gallery.shape[0],), dtype=np.float32)
    q = q / (q_norm + 1e-8)

    g = np.asarray(gallery, dtype=np.float32)
    norms = np.linalg.norm(g, axis=1)
    safe = (norms > 1e-6) & np.isfinite(norms)
    g_normed = np.zeros_like(g, dtype=np.float32)
    g_normed[safe] = g[safe] / (norms[safe, None] + 1e-8)
    return g_normed @ q


def _normalize_face(face_img: np.ndarray) -> np.ndarray:
    img_bgr = np.asarray(face_img)
    if img_bgr.dtype != np.uint8:
        img = np.asarray(img_bgr, dtype="float32")
        max_val = float(np.max(img)) if img.size else 0.0
        if max_val <= 1.5:
            img *= 255.0
        img_bgr = np.clip(img, 0, 255).astype("uint8")
    else:
        img_bgr = np.ascontiguousarray(img_bgr)
    if img_bgr.ndim == 2:
        img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_GRAY2BGR)
    return img_bgr


def recognize_face(face_img: np.ndarray) -> Dict[str, Any]:
    default = {
        "name": "Unknown",
        "phone": "Unknown",
        "location": "Unknown",
        "address": "Unknown",
        "company": "Unknown",
        "worker_id": None,
        "location_id": None,
        "company_id": None,
    }
    if not _ensure_gallery():
        return default

    try:
        img_bgr = _normalize_face(face_img)
        reps = DeepFace.represent(
            img_path=img_bgr,
            model_name="VGG-Face",
            enforce_detection=False,
        )
        if not reps or not isinstance(reps, list):
            return default
        emb = np.array(reps[0]["embedding"], dtype=np.float32)
        if emb.size == 0 or not np.isfinite(emb).all():
            return default
        sims = _cosine_sim(emb, face_gallery.embeddings)
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])
        if np.isfinite(best_sim) and best_sim >= settings.FACE_SIM_THRESHOLD:
            asset = face_gallery.asset_ids[best_idx]
            return face_gallery.imageid_to_info.get(str(asset), default) | {"similarity": best_sim}
    except Exception as exc:
        print("⚠️ [recognize_face]", exc)
    return default


def helmet_detect(frame_bgr: np.ndarray) -> bool:
    if yolo_model is None:
        return False
    results = yolo_model(frame_bgr, conf=0.25)
    res = results[0] if results else None
    if not res or res.boxes is None:
        return False
    names = res.names
    best_conf = 0.0
    best_label = None
    for box in res.boxes:
        conf = float(box.conf[0].item())
        if conf < 0.2:
            continue
        label = names[int(box.cls[0].item())]
        if conf > best_conf:
            best_conf = conf
            best_label = label
    if not best_label:
        return False
    candidate = best_label.lower().replace("-", "").replace("_", "")
    return "no" not in candidate and ("helmet" in candidate or "hardhat" in candidate)


def _extract_faces(frame_bgr: np.ndarray) -> List[Dict[str, Any]]:
    return DeepFace.extract_faces(
        img_path=frame_bgr,
        enforce_detection=False,
        detector_backend="opencv",
        align=False,
    )


def analyze_frame_bgr(frame_bgr: np.ndarray) -> Dict[str, Any]:
    init_models()
    faces_raw = _extract_faces(frame_bgr)
    faces: List[Dict[str, Any]] = []

    # Filter out obviously bad boxes (too small or too large)
    h_img, w_img = frame_bgr.shape[:2]
    min_area = 60 * 60
    max_area = 0.6 * w_img * h_img
    for f in faces_raw or []:
        fa = f.get("facial_area") or {}
        w = fa.get("w", 0)
        h = fa.get("h", 0)
        x = fa.get("x", 0)
        y = fa.get("y", 0)
        area = w * h
        if area < min_area or area > max_area:
            continue
        # ensure box within image bounds
        if w <= 0 or h <= 0 or x < -w_img * 0.1 or y < -h_img * 0.1:
            continue
        faces.append(f)

    helmet_on = helmet_detect(frame_bgr)

    faces_out: List[Dict[str, Any]] = []
    person_info: Dict[str, Any] = {
        "name": "Unknown",
        "phone": "Unknown",
        "location": "Unknown",
        "address": "Unknown",
        "company": "Unknown",
        "worker_id": None,
        "location_id": None,
        "company_id": None,
    }

    if faces:
        areas = [(face["facial_area"]["w"] * face["facial_area"]["h"]) for face in faces]
        primary_idx = int(np.argmax(areas))
        for idx, face in enumerate(faces):
            info = recognize_face(face["face"])
            fa = face["facial_area"]
            faces_out.append(
                {
                    "x": int(fa["x"]),
                    "y": int(fa["y"]),
                    "w": int(fa["w"]),
                    "h": int(fa["h"]),
                    "name": info.get("name", "Unknown"),
                    "similarity": info.get("similarity"),
                    "ppe": {"helmet_on": helmet_on},
                }
            )
            if idx == primary_idx:
                person_info = info

    return {
        "person": person_info,
        "ppe": {"helmet_on": helmet_on},
        "faces": faces_out,
        "detected_at": datetime.utcnow().isoformat(),
    }
