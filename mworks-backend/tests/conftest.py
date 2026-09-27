import os
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_KEY_DIR = Path(__file__).resolve().parent / "_keys"
_KEY_DIR.mkdir(exist_ok=True)
_PRIV = _KEY_DIR / "jwt_private.pem"
_PUB = _KEY_DIR / "jwt_public.pem"

if not _PRIV.exists():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _PRIV.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    _PUB.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

os.environ["APP_ENV"] = "test"
os.environ["JWT_PRIVATE_KEY_PATH"] = str(_PRIV)
os.environ["JWT_PUBLIC_KEY_PATH"] = str(_PUB)
os.environ["DB_HOST"] = "localhost"
os.environ["DB_SSLMODE"] = "disable"
os.environ["S3_SECRET_KEY"] = "test"
os.environ["DEMO_USER_PASSWORD"] = "ChangeMe1a!"
os.environ["DEMO_USER_EMAIL"] = "henry@mworks.ng"
os.environ["RATE_LIMIT_AUTH_PER_MIN"] = "1000"
os.environ["RATE_LIMIT_API_PER_MIN"] = "1000"
os.environ["JOB_INGEST_ENABLED"] = "false"
os.environ["DEEPSEEK_API_KEY"] = ""

from app.config import get_settings

get_settings.cache_clear()

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
