# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global configuration loaded from environment variables (.env)."""

    # File-backed embeddings (CSV / optional NPY)
    EMBEDDINGS_CSV: str = "./embeddings_with_vectors.csv"
    EMBEDDINGS_NPY: str = "./embeddings_matrix.npy"
    FACE_IMAGE_DIR: str = "./worker_images"

    # YOLO model path (update to actual path on your machine)
    YOLO_MODEL_PATH: str = "./best.pt"

    # Similarity threshold for face recognition
    FACE_SIM_THRESHOLD: float = 0.5

    # Frontend origin (Vite dev server)
    FRONTEND_ORIGIN: str = "http://localhost:8080"

    # Where worker images are stored and how they are served
    MEDIA_ROOT: str = "./worker_images"
    MEDIA_BASE_URL: str = "http://localhost:8001/media"

    # NEW: where live monitoring logs are written
    # (used in main.py -> LOGS_PATH)
    LOGS_PATH: str = "./logs/live_events.log"

    # Twilio / alerts configuration
    TWILIO_ACCOUNT_SID: str = ""  # set via env/.env
    TWILIO_AUTH_TOKEN: str = ""  # set via env/.env
    TWILIO_FROM_NUMBER: str = "+18333654838"
    ALERTS_SMS_ENABLED: bool = True
    ALERTS_COOLDOWN_MINUTES: int = 15

    # Note: DB settings are now handled in app/db.py via LOCAL_DB_*
    # env vars (LOCAL_DB_HOST, LOCAL_DB_PORT, etc.), since you're
    # using local MySQL instead of GCP.

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # allow unrelated env vars like LOCAL_DB_* without errors


@lru_cache
def get_settings() -> Settings:
    return Settings()
