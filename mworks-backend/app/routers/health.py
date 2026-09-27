from fastapi import APIRouter

from app.config import get_settings
from app.db import SessionLocal, ping_db

router = APIRouter(tags=["ops"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": get_settings().APP_NAME}


@router.get("/ready")
def ready() -> dict:
    db = SessionLocal()
    try:
        ok = ping_db(db)
    finally:
        db.close()
    if not ok:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail={"error": "Service unavailable.", "code": "NOT_READY"})
    return {"status": "ok", "database": "ok"}
