import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt

from app.config import Settings

_ALLOWED_ROLES = {"buyer", "seller", "both"}
ALGS = ["RS256"]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def issue_access_token(settings: Settings, *, sub: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iss": settings.JWT_ISS,
        "aud": settings.JWT_AUD,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_ACCESS_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, _read(settings.JWT_PRIVATE_KEY_PATH), algorithm="RS256")


def decode_access_token(settings: Settings, token: str) -> dict:
    return jwt.decode(
        token,
        _read(settings.JWT_PUBLIC_KEY_PATH),
        algorithms=ALGS,
        audience=settings.JWT_AUD,
        issuer=settings.JWT_ISS,
        options={"require": ["exp", "iss", "aud", "sub"]},
    )


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_expiry(settings: Settings) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_DAYS)


def normalize_role(role: str | None) -> str:
    value = (role or "buyer").strip().lower()
    if value not in _ALLOWED_ROLES:
        return "buyer"
    return value


def constant_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
