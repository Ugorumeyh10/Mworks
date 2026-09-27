import logging
from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app.config import Settings, get_settings

log = logging.getLogger("mworks")


class Base(DeclarativeBase):
    pass


def _engine(settings: Settings):
    url = settings.sqlalchemy_url()
    connect_args: dict = {}
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        kwargs["poolclass"] = StaticPool
        kwargs["pool_pre_ping"] = False
    elif settings.APP_ENV not in {"local", "test"}:
        # Serverless (Vercel): do not keep pooled sockets across freezes.
        kwargs["poolclass"] = NullPool
    engine = create_engine(
        url,
        connect_args=connect_args,
        **kwargs,
    )

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _rec) -> None:
        # Never send statement_timeout as a libpq startup option (PgBouncer rejects it).
        if settings.APP_ENV == "test" or url.startswith("sqlite"):
            return
        try:
            cur = dbapi_conn.cursor()
            cur.execute("SET statement_timeout = '30s'")
            cur.close()
        except Exception:
            log.warning("statement_timeout was not applied after connect; continuing")

    return engine


_settings = get_settings()
engine = _engine(_settings)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema(bind) -> None:
    """Add columns create_all will not alter on an existing Postgres volume."""
    if str(bind.url).startswith("sqlite"):
        return
    statements = (
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_ref VARCHAR(64)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_provider VARCHAR(24)",
        "ALTER TABLE listings ADD COLUMN IF NOT EXISTS prompt_body TEXT",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_key VARCHAR(512)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source VARCHAR(32)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS external_key VARCHAR(180)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS apply_url VARCHAR(512)",
        "ALTER TABLE listings ADD COLUMN IF NOT EXISTS content_sha256 VARCHAR(64)",
        "ALTER TABLE listings ADD COLUMN IF NOT EXISTS minhash_sig TEXT",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS rank_reason VARCHAR(280)",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS cv_key VARCHAR(512)",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS interview_score INTEGER DEFAULT 0",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS interview_summary TEXT",
        "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS interview_session_id VARCHAR(24)",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS cover_url VARCHAR(512)",
        "ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS media JSON",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_jobs_external_key ON jobs (external_key)",
    )
    with bind.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def ping_db(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        log.exception("database ping failed")
        return False
