import logging
from urllib.parse import quote

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import Settings

log = logging.getLogger("mworks")

_ALLOWED_DOC = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
    "text/plain",
    "application/xml",
    "application/zip",
}
_ALLOWED_EXT = {".pdf", ".docx", ".md", ".txt", ".xml", ".zip", ".mp4", ".webm"}


def storage_configured(settings: Settings) -> bool:
    secret = (settings.S3_SECRET_KEY or "").strip()
    endpoint = (settings.S3_ENDPOINT or "").strip().lower()
    if not secret or not endpoint:
        return False
    if "localhost" in endpoint or "127.0.0.1" in endpoint:
        return settings.APP_ENV == "local"
    return True


def s3_client(settings: Settings, *, public: bool = False):
    endpoint = settings.s3_presign_endpoint() if public else settings.S3_ENDPOINT
    region = (settings.S3_REGION or "us-east-1").strip() or "us-east-1"
    if endpoint and "r2.cloudflarestorage.com" in endpoint.lower() and region == "us-east-1":
        region = "auto"
    return boto3.client(
        "s3",
        endpoint_url=endpoint or None,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=region,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )


def ensure_bucket(settings: Settings) -> None:
    if settings.APP_ENV == "test":
        return
    if not storage_configured(settings):
        log.info("object storage skipped; uploads need a remote S3 endpoint")
        return
    last_err = None
    attempts = 2 if settings.APP_ENV not in {"local"} else 8
    for _attempt in range(attempts):
        try:
            client = s3_client(settings)
            existing = {b["Name"] for b in client.list_buckets().get("Buckets", [])}
            if settings.S3_BUCKET not in existing:
                client.create_bucket(Bucket=settings.S3_BUCKET)
            last_err = None
            break
        except (BotoCoreError, ClientError, Exception) as exc:
            last_err = exc
            import time

            time.sleep(1)
    if last_err is not None:
        log.warning("object storage is not ready; uploads will fail until MinIO/R2 is up: %s", last_err)
        return
    origins = settings.cors_origin_list()
    if not origins:
        return
    try:
        s3_client(settings).put_bucket_cors(
            Bucket=settings.S3_BUCKET,
            CORSConfiguration={
                "CORSRules": [
                    {
                        "AllowedOrigins": origins,
                        "AllowedMethods": ["GET", "PUT", "HEAD"],
                        "AllowedHeaders": ["*"],
                        "ExposeHeaders": ["ETag", "x-amz-request-id"],
                        "MaxAgeSeconds": 3000,
                    }
                ]
            },
        )
    except (BotoCoreError, ClientError, Exception) as exc:
        log.warning("object storage CORS could not be applied: %s", exc)


def validate_upload(filename: str, content_type: str, kind: str, size_bytes: int | None = None) -> None:
    from app.scan import sniff_kind

    sniff_kind(filename, content_type, kind, size_bytes)


def owned_object_key(public_id: str, key: str, *, kinds: set[str]) -> str:
    cleaned = key.strip().replace("\\", "/")
    if not cleaned or ".." in cleaned or cleaned.startswith("/") or "//" in cleaned:
        raise ValueError("invalid object key")
    parts = cleaned.split("/")
    if len(parts) < 3:
        raise ValueError("invalid object key")
    if parts[0] not in kinds or parts[1] != public_id:
        raise ValueError("invalid object key")
    if not any(parts[-1].lower().endswith(ext) for ext in _ALLOWED_EXT | {".mp4", ".webm", ".jpg", ".jpeg", ".png", ".webp", ".gif"}):
        raise ValueError("invalid object key")
    return cleaned


def put_bytes(settings: Settings, *, key: str, body: bytes, content_type: str) -> bool:
    if settings.APP_ENV == "test":
        return True
    try:
        s3_client(settings).put_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
        return True
    except (BotoCoreError, ClientError, Exception):
        log.warning("could not store seed object %s", key)
        return False


def object_exists(settings: Settings, key: str) -> bool:
    if settings.APP_ENV == "test":
        return True
    try:
        s3_client(settings).head_object(Bucket=settings.S3_BUCKET, Key=key)
        return True
    except (BotoCoreError, ClientError, Exception):
        return False


def filename_from_key(key: str) -> str:
    name = key.rsplit("/", 1)[-1]
    return name.split("-", 1)[-1] if "-" in name else name


def presign_put(settings: Settings, *, key: str, content_type: str) -> str:
    if settings.APP_ENV == "test":
        return f"https://storage.test/{quote(key)}?upload=1"
    client = s3_client(settings, public=True)
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=600,
    )


def presign_get_inline(settings: Settings, *, key: str, content_type: str = "") -> str:
    if settings.APP_ENV == "test":
        return f"https://storage.test/{quote(key)}?inline=1"
    client = s3_client(settings, public=True)
    params = {"Bucket": settings.S3_BUCKET, "Key": key, "ResponseContentDisposition": "inline"}
    if content_type:
        params["ResponseContentType"] = content_type
    return client.generate_presigned_url("get_object", Params=params, ExpiresIn=3600)


def presign_get(settings: Settings, *, key: str, filename: str) -> str:
    if settings.APP_ENV == "test":
        return f"https://storage.test/{quote(key)}?name={quote(filename)}"
    client = s3_client(settings, public=True)
    disposition = f'attachment; filename="{quote(filename)}"'
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": key,
            "ResponseContentDisposition": disposition,
        },
        ExpiresIn=120,
    )


def safe_key(prefix: str, filename: str) -> str:
    base = quote(filename.replace("..", "").replace("/", "-").replace("\\", "-"))[:120]
    return f"{prefix}/{base}"


def read_bytes(settings: Settings, key: str, limit: int = 2_000_000) -> bytes:
    if settings.APP_ENV == "test":
        return b"sandbox package contents for verification"
    try:
        obj = s3_client(settings).get_object(Bucket=settings.S3_BUCKET, Key=key)
        return obj["Body"].read(limit)
    except (BotoCoreError, ClientError, Exception):
        return b""
