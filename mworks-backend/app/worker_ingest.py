import logging
import time

from app.config import get_settings
from app.db import Base, SessionLocal, engine, ensure_schema
from app.ingest_jobs import ingest_once

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("mworks.ingest")


def main() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    ensure_schema(engine)
    interval = settings.job_ingest_interval()
    log.info("job ingest loop interval=%ss sources=%s", interval, settings.job_ingest_sources())
    while True:
        if not settings.JOB_INGEST_ENABLED:
            time.sleep(interval)
            continue
        db = SessionLocal()
        try:
            stats = ingest_once(db, settings)
            log.info("job ingest posted=%s scanned=%s", stats.get("posted"), stats.get("scanned"))
            from app.hire import expire_videos

            expired = expire_videos(db, settings)
            if expired:
                db.commit()
                log.info("expired video answers=%s", expired)
        except Exception:
            db.rollback()
            log.exception("job ingest cycle failed")
        finally:
            db.close()
        time.sleep(interval)


if __name__ == "__main__":
    main()
