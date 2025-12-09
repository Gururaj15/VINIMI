from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd
from deepface import DeepFace

from ..config import get_settings
from ..detection import analyze_frame_bgr

settings = get_settings()


_embeddings_loaded = False
_embeddings: np.ndarray | None = None
_filenames: np.ndarray | None = None
_imageid_to_info: Dict[str, Dict] = {}


def _get_imageid(filename: str) -> str:
    return os.path.splitext(os.path.basename(str(filename)))[0]


def _ensure_embeddings_loaded(embeddings_csv_path: str) -> bool:
    global _embeddings_loaded, _embeddings, _filenames, _imageid_to_info
    if _embeddings_loaded:
        return True
    if not os.path.exists(embeddings_csv_path):
        print(f"⚠️ [video] embeddings CSV not found: {embeddings_csv_path}")
        return False
    try:
        emb_df = pd.read_csv(embeddings_csv_path)
    except Exception as exc:
        print(f"⚠️ [video] failed to read embeddings CSV: {exc}")
        return False
    if "filename" not in emb_df.columns or "embedding" not in emb_df.columns:
        print("⚠️ [video] embeddings CSV must contain filename and embedding columns")
        return False
    _filenames = emb_df["filename"].values
    try:
        _embeddings = np.vstack([
            np.fromstring(str(row["embedding"]), sep=",")
            for _, row in emb_df.iterrows()
        ]).astype(np.float32, copy=False)
    except Exception as exc:
        print(f"⚠️ [video] failed to parse embeddings: {exc}")
        return False
    _imageid_to_info = {}
    for _, row in emb_df.iterrows():
        img_id = _get_imageid(row["filename"])
        _imageid_to_info[img_id] = {
            "name": row.get("name", "Unknown") if "name" in emb_df.columns else "Unknown",
            "phone": row.get("phone", "Unknown") if "phone" in emb_df.columns else "Unknown",
            "location": row.get("location", "Unknown") if "location" in emb_df.columns else "Unknown",
        }
    _embeddings_loaded = True
    return True


def _cosine_sim(query: np.ndarray, gallery: np.ndarray) -> np.ndarray:
    q = np.asarray(query, dtype=np.float32)
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


def _select_best_face(
    faces: List[Tuple[int, int, int, int]],
    img_shape: Tuple[int, int, int],
    method: str = "largest",
) -> Optional[Tuple[int, int, int, int]]:
    if len(faces) == 0:
        return None
    if len(faces) == 1:
        return faces[0]
    if method == "largest":
        return max(faces, key=lambda box: box[2] * box[3])
    # fallback: closest to center
    h, w = img_shape[:2]
    cx, cy = w / 2, h / 2
    def center_distance(box):
        x, y, bw, bh = box
        fx, fy = x + bw / 2, y + bh / 2
        return (fx - cx) ** 2 + (fy - cy) ** 2
    return min(faces, key=center_distance)


def _recognize_face(frame_bgr: np.ndarray, threshold: float, embeddings_csv: str) -> Tuple[Dict[str, str], Optional[Tuple[int, int, int, int]], float]:
    if not _ensure_embeddings_loaded(embeddings_csv) or _embeddings is None or _filenames is None:
        return {"name": "Unknown", "phone": "Unknown", "location": "Unknown"}, None, 0.0

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    if len(faces) == 0:
        return {"name": "Unknown", "phone": "Unknown", "location": "Unknown"}, None, 0.0

    best_face = _select_best_face(list(faces), frame_bgr.shape, method="largest")
    if best_face is None:
        return {"name": "Unknown", "phone": "Unknown", "location": "Unknown"}, None, 0.0

    temp_path = "temp_video_frame.jpg"
    cv2.imwrite(temp_path, frame_bgr)

    try:
        rep = DeepFace.represent(img_path=temp_path, model_name="VGG-Face", enforce_detection=False)
        if not rep:
            return {"name": "Unknown", "phone": "Unknown", "location": "Unknown"}, best_face, 0.0

        test_embedding = rep[0]["embedding"]
        test_emb_norm = np.array(test_embedding, dtype=np.float32)
        test_emb_norm = test_emb_norm / (np.linalg.norm(test_emb_norm) + 1e-8)

        emb_norm = _embeddings / (np.linalg.norm(_embeddings, axis=1, keepdims=True) + 1e-8)
        sims = emb_norm @ test_emb_norm

        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])
        identified_imageid = _get_imageid(_filenames[best_idx])
        person_info = _imageid_to_info.get(
            identified_imageid,
            {"name": "Unknown", "phone": "Unknown", "location": "Unknown"},
        )

        if best_sim >= threshold and np.isfinite(best_sim):
            return person_info, best_face, best_sim
        else:
            return {"name": "Unknown", "phone": "Unknown", "location": "Unknown"}, best_face, best_sim
    except Exception as e:
        print(f"Face recognition error: {e}")
        return {"name": "Unknown", "phone": "Unknown", "location": "Unknown"}, best_face, 0.0
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def analyze_video_face_recognition(
    video_path: str,
    n_segments: int = 5,  # kept for compatibility, but sampling is driven by sample_frames
    similarity_threshold: float = 0.4,
    save_annotated: bool = False,
    media_root: Path | None = None,
    sample_frames: int = 10,
    embeddings_csv_path: Optional[str] = None,
) -> Dict:
    emb_path = embeddings_csv_path or settings.EMBEDDINGS_CSV
    if not _ensure_embeddings_loaded(emb_path):
        raise RuntimeError("Could not load embeddings from CSV")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    sample_frames = max(1, sample_frames)
    interval = max(1, total_frames // sample_frames)
    key_frames = [min(i * interval, total_frames - 1) for i in range(sample_frames)]

    segments: List[Dict] = []
    majority_frame = None
    segment_boxes: List[Optional[Tuple[int, int, int, int]]] = []
    segment_sims: List[float] = []
    for idx, kf in enumerate(key_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, kf)
        ok, frame = cap.read()
        if not ok:
            segments.append({"segment": idx + 1, "t_sec": kf / fps, "name": "Unknown", "similarity": 0.0})
            continue
        info, face_box, sim = _recognize_face(frame, threshold=similarity_threshold, embeddings_csv=emb_path)
        det = analyze_frame_bgr(frame)
        helmet_flag = (det.get("ppe") or {}).get("helmet_on") if isinstance(det, dict) else None
        segments.append(
            {
                "segment": idx + 1,
                "t_sec": round(kf / fps, 2),
                "name": info.get("name", "Unknown"),
                "similarity": float(sim),
                "phone": info.get("phone"),
                "location": info.get("location"),
                "frame_index": int(kf),
                "helmet_on": helmet_flag,
                "face_box": face_box,
            }
        )
        if info.get("name") != "Unknown" and majority_frame is None:
            majority_frame = frame.copy()
        segment_boxes.append(face_box)
        segment_sims.append(float(sim))

    names_voted = [s["name"] for s in segments if s.get("name") and s["name"] != "Unknown"]
    majority_info = {
        "name": "Unknown",
        "phone": "Unknown",
        "location": "Unknown",
        "similarity": None,
        "segments_with_that_name": 0,
        "total_segments": len(segments),
        "frame_names": [s.get("name", "Unknown") for s in segments],
        "helmet_on": None,
    }
    majority_idx: Optional[int] = None
    if names_voted:
        most_common_name, count = Counter(names_voted).most_common(1)[0]
        majority_info["name"] = most_common_name
        majority_info["segments_with_that_name"] = count
        for seg in segments:
            if seg.get("name") == most_common_name:
                majority_info["phone"] = seg.get("phone")
                majority_info["location"] = seg.get("location")
                majority_info["similarity"] = seg.get("similarity")
                majority_info["helmet_on"] = seg.get("helmet_on")
                majority_idx = seg.get("segment")
                if majority_frame is None:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, seg.get("frame_index", 0))
                    ok, frame = cap.read()
                    if ok:
                        majority_frame = frame.copy()
                break

    annotated_url = None
    if save_annotated and media_root is not None:
        videos_dir = Path(media_root) / "videos"
        videos_dir.mkdir(parents=True, exist_ok=True)
        out_path = videos_dir / (Path(video_path).stem + "_annotated.mp4")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
        frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            current_segment = min(frame_idx // interval, len(segments) - 1)
            seg_info = segments[current_segment]
            name = seg_info.get("name", "Unknown")
            sim = seg_info.get("similarity") or 0.0
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            label = f"{name} ({sim:.2f})" if sim else name
            cv2.putText(frame, label, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            out.write(frame)
            frame_idx += 1
        out.release()
        annotated_url = f"{settings.MEDIA_BASE_URL}/videos/{out_path.name}"

    cap.release()

    rep_frame = majority_frame
    if rep_frame is None:
        cap2 = cv2.VideoCapture(video_path)
        mid = total_frames // 2
        cap2.set(cv2.CAP_PROP_POS_FRAMES, mid)
        ok, frame = cap2.read()
        if ok:
            rep_frame = frame.copy()
        cap2.release()

    snapshot_url = None
    if rep_frame is not None and media_root is not None:
        try:
            videos_dir = Path(media_root) / "videos"
            videos_dir.mkdir(parents=True, exist_ok=True)
            snap_path = videos_dir / f"{Path(video_path).stem}_snapshot.jpg"
            frame_draw = rep_frame.copy()
            if majority_idx is not None and 0 < majority_idx <= len(segment_boxes):
                box = segment_boxes[majority_idx - 1]
                sim_val = segment_sims[majority_idx - 1] if majority_idx - 1 < len(segment_sims) else None
                if box is not None:
                    x, y, w, h = box
                    helmet_on = majority_info.get("helmet_on")
                    color = (0, 255, 0) if helmet_on else (0, 0, 255)
                    cv2.rectangle(frame_draw, (x, y), (x + w, y + h), color, 2)
                    label = majority_info.get("name", "Unknown")
                    if sim_val is not None:
                        label = f"{label} ({sim_val:.2f})"
                    cv2.putText(frame_draw, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.imwrite(str(snap_path), frame_draw)
            snapshot_url = f"{settings.MEDIA_BASE_URL}/videos/{snap_path.name}"
        except Exception as exc:
            print(f"⚠️ [video] snapshot save error: {exc}")

    return {
        "mode": "video",
        "majority": majority_info,
        "segments": segments,
        "annotated_video_url": annotated_url,
        "representative_frame": rep_frame,  # numpy array BGR or None
        "snapshot_url": snapshot_url,
    }
