# app/face_gallery.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import os
import threading
import numpy as np
import pandas as pd
from .config import get_settings

_settings = get_settings()
_lock = threading.RLock()


class FileFaceGallery:
    """
    File-backed gallery (CSV + optional NPY), matching scaffold_vinimi logic.
    - embeddings CSV has an 'embedding' column with comma-separated floats.
    - optional NPY holds the matrix aligned row-for-row with the CSV.
    """

    base_cols = [
        "filename",
        "asset_id",
        "name",
        "worker_id",
        "phone",
        "location",
        "capture_datetime",
    ]

    def __init__(self) -> None:
        self.embeddings: np.ndarray | None = None
        self.meta_df: pd.DataFrame | None = None
        self.ids: List[str] = []
        self.meta: Dict[str, Dict[str, Any]] = {}
        self.source: str = "none"

    @property
    def asset_ids(self) -> List[str]:
        return self.ids

    @property
    def imageid_to_info(self) -> Dict[str, Dict[str, Any]]:
        return self.meta

    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in self.base_cols:
            if col not in df.columns:
                df[col] = None
        return df

    def _parse_embedding(self, raw: Any) -> Optional[np.ndarray]:
        if raw is None:
            return None
        if isinstance(raw, str):
            text = raw.strip()
            if not text or text.lower() == "embedding":
                return None
            try:
                arr = np.fromstring(text, sep=",", dtype=np.float32)
                return arr if arr.size > 0 and np.isfinite(arr).all() else None
            except Exception:
                return None
        try:
            arr = np.asarray(raw, dtype=np.float32)
            return arr if arr.size > 0 and np.isfinite(arr).all() else None
        except Exception:
            return None

    def _build_from_csv(self, df: pd.DataFrame):
        vectors: list[np.ndarray] = []
        keep_idx: list[int] = []
        ids: list[str] = []
        for i, row in df.iterrows():
            v = self._parse_embedding(row.get("embedding"))
            if v is None:
                continue
            vectors.append(v)
            aid = row.get("asset_id") or row.get("filename") or f"row_{i}"
            ids.append(str(aid))
            keep_idx.append(i)
        if not vectors:
            return None, None, None
        matrix = np.vstack(vectors).astype(np.float32, copy=False)
        df2 = df.iloc[keep_idx].reset_index(drop=True)
        return matrix, ids, df2

    def load(self) -> None:
        with _lock:
            csv_path = _settings.EMBEDDINGS_CSV
            npy_path = _settings.EMBEDDINGS_NPY
            if not os.path.exists(csv_path):
                print(f"⚠️ [FaceGallery] CSV not found: {csv_path}")
                self.embeddings = None
                self.ids = []
                self.meta = {}
                self.source = "none"
                return

            df = pd.read_csv(csv_path)
            df = self._ensure_columns(df)

            # try npy fast path
            if os.path.exists(npy_path):
                try:
                    mat = np.load(npy_path)
                    if len(df) == len(mat):
                        ids = [
                            str(df.loc[i, "asset_id"])
                            if pd.notna(df.loc[i, "asset_id"])
                            else str(df.loc[i, "filename"])
                            for i in range(len(df))
                        ]
                        self.embeddings = mat.astype(np.float32, copy=False)
                        self.ids = ids
                        self.meta_df = df
                        self.meta = {
                            str(ids[i]): df.iloc[i].to_dict() for i in range(len(ids))
                        }
                        self.source = "npy+csv"
                        print(f"✅ [FaceGallery] Loaded {len(ids)} from NPY + CSV.")
                        return
                    else:
                        print(
                            f"⚠️ [FaceGallery] NPY rows ({len(mat)}) != CSV rows ({len(df)}); falling back to CSV."
                        )
                except Exception as exc:
                    print(f"⚠️ [FaceGallery] NPY load error: {exc}; falling back to CSV.")

            matrix, ids, df2 = self._build_from_csv(df)
            if matrix is None:
                print("⚠️ [FaceGallery] No valid embeddings parsed – gallery empty.")
                self.embeddings = None
                self.ids = []
                self.meta = {}
                self.source = "none"
                return

            self.embeddings = matrix
            self.ids = ids or []
            self.meta_df = df2
            self.meta = {str(ids[i]): df2.iloc[i].to_dict() for i in range(len(ids))}
            self.source = "csv"
            print(f"✅ [FaceGallery] Loaded {len(self.ids)} embeddings from CSV.")

    def enroll(self, row: dict, embedding: np.ndarray) -> bool:
        emb_arr = np.asarray(embedding, dtype=np.float32).reshape(-1)
        with _lock:
            csv_path = _settings.EMBEDDINGS_CSV
            npy_path = _settings.EMBEDDINGS_NPY
            os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
            os.makedirs(os.path.dirname(npy_path) or ".", exist_ok=True)

            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
            else:
                df = pd.DataFrame(columns=self.base_cols + ["embedding"])
            df = self._ensure_columns(df)

            safe_row = {col: row.get(col) for col in self.base_cols}
            safe_row["embedding"] = ",".join(f"{float(x):.6f}" for x in emb_arr)
            df = pd.concat([df, pd.DataFrame([safe_row])], ignore_index=True)
            df.to_csv(csv_path, index=False)

            # rebuild matrix
            matrix, ids, df2 = self._build_from_csv(df)
            if matrix is None:
                print("⚠️ [FaceGallery] Failed to rebuild matrix after enroll.")
                return False
            np.save(npy_path, matrix.astype(np.float32, copy=False))
            self.embeddings = matrix
            self.ids = ids or []
            self.meta_df = df2
            self.meta = {str(ids[i]): df2.iloc[i].to_dict() for i in range(len(ids))}
            self.source = "npy+csv"
            print(f"✅ [FaceGallery] Enrolled new embedding. Total: {len(self.ids)}")
            return True


face_gallery = FileFaceGallery()


def reload_gallery() -> None:
    face_gallery.load()
