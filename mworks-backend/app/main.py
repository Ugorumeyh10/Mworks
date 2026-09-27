from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base, SessionLocal, engine, ensure_schema
from app.errors import install_error_handlers
from app.routers import assistant, auth, blog, feed, health, hire, interviewer, jobs, listings, messages, orders, trust
from app.seed import seed
from app.storage import ensure_bucket

log = logging.getLogger("mworks")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema(engine)
    ensure_bucket(settings)
    db: Session = SessionLocal()
    try:
        seed(db, settings)
    except Exception:
        log.exception("seed failed")
        db.rollback()
    finally:
        db.close()
    log.info("mworks api started env=%s sslmode=%s", settings.APP_ENV, settings.resolved_sslmode())
    yield


app = FastAPI(
    title="Mworks API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled() else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.docs_enabled() else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

install_error_handlers(app)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(listings.router)
app.include_router(listings.me_router)
app.include_router(orders.router)
app.include_router(jobs.router)
app.include_router(messages.router)
app.include_router(assistant.router)
app.include_router(feed.router)
app.include_router(trust.router)
app.include_router(hire.router)
app.include_router(interviewer.router)
app.include_router(blog.router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if request.method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
        return JSONResponse(
            status_code=405,
            content={"error": "Method not allowed.", "code": "METHOD_NOT_ALLOWED"},
            headers={"Allow": "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"},
        )
    length = request.headers.get("content-length")
    if length and request.headers.get("content-type", "").startswith("application/json"):
        try:
            if int(length) > settings.JSON_BODY_MAX_BYTES:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Payload is too large.", "code": "PAYLOAD_TOO_LARGE"},
                )
        except ValueError:
            return JSONResponse(status_code=400, content={"error": "Invalid request.", "code": "BAD_REQUEST"})
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if "server" in response.headers:
        del response.headers["server"]
    return response
