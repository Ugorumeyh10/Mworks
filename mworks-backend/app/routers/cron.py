import logging

from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
from app.db import SessionLocal
from app.hire import expire_videos
from app.ingest_jobs import ingest_once
from app.security import constant_eq

log = logging.getLogger("mworks")
router = APIRouter(prefix="/v1/internal", tags=["ops"])


def _cron_authorized(request: Request, secret: str) -> bool:
    token = (secret or "").strip()
    if not token:
        return False
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return constant_eq(auth.split(" ", 1)[1].strip(), token)
    return False


@router.get("/cron/ingest")
def cron_ingest(request: Request) -> dict:
    settings = get_settings()
    if not _cron_authorized(request, settings.CRON_SECRET):
        raise HTTPException(status_code=401, detail={"error": "Authentication required.", "code": "UNAUTHENTICATED"})
    if not settings.JOB_INGEST_ENABLED:
        return {"status": "skipped", "reason": "disabled"}
    db = SessionLocal()
    try:
        stats = ingest_once(db, settings)
        expired = expire_videos(db, settings)
        if expired:
            db.commit()
        return {"status": "ok", "posted": stats.get("posted"), "scanned": stats.get("scanned"), "expired_videos": expired}
    except Exception:
        db.rollback()
        log.exception("cron ingest failed")
        raise HTTPException(status_code=500, detail={"error": "Ingest failed.", "code": "INGEST_FAILED"})
    finally:
        db.close()
