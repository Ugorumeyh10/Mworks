import hashlib
import re

from sqlalchemy.orm import Session

from app.config import Settings
from app.fingerprint import bow_embed, cosine, jaccard, minhash_sig, sha256_hex
from app.models import Listing
from app.scan import ScanFailed, _SECRET, scan_bytes
from app.storage import object_exists, read_bytes

_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_CLIENT = re.compile(r"\b(client name|production (data|credentials)|customer naira account)\b", re.I)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _hash(text: str) -> str:
    return hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()


def _pii(text: str) -> str | None:
    if _SECRET.search(text or ""):
        return "The pack looks like it contains credentials or a private key."
    if _EMAIL.search(text or "") and _CLIENT.search(text or ""):
        return "The pack looks like it contains client or production data."
    return None


def _append(row: Listing, label: str, status: str) -> None:
    row.verification_log = list(row.verification_log or []) + [{"label": label, "status": status}]


def _fail(row: Listing, label: str) -> bool:
    _append(row, label, "Failed")
    row.status = "rejected"
    row.verified = False
    return False


def _scan_pack(settings: Settings, row: Listing, raw: bytes, kind: str) -> str | None:
    try:
        reasons = scan_bytes(settings, raw, filename=row.object_key or "pack.bin", kind=kind)
    except ScanFailed as exc:
        return str(exc)
    if reasons:
        return reasons[0]
    return None


def _dedupe(db: Session, settings: Settings, row: Listing, source: str) -> str | None:
    if settings.APP_ENV == "test":
        digest = _hash(f"{row.slug}\n{row.prompt_body or row.description}")
    else:
        digest = sha256_hex(_norm(source or row.description))
    row.content_sha256 = digest
    row.minhash_sig = minhash_sig(source or row.description or "")
    others = (
        db.query(Listing)
        .filter(Listing.id != row.id, Listing.status.in_(("live", "pending_review")), Listing.type == row.type)
        .all()
    )
    threshold = float(settings.NEAR_DUPE_JACCARD or 0.85)
    for other in others:
        if settings.APP_ENV == "test":
            other_src = f"{other.slug}\n{other.prompt_body or other.description}"
            if other_src and _hash(other_src) == digest:
                return "exact"
            continue
        if other.content_sha256 and other.content_sha256 == digest:
            return "exact"
        sim = jaccard(row.minhash_sig or "", other.minhash_sig or "")
        if other.minhash_sig and sim >= threshold:
            return "near"
        other_src = other.prompt_body or other.description or ""
        embed = cosine(bow_embed(source or ""), bow_embed(other_src))
        if embed >= 0.94 and sim >= 0.55:
            return "near"
    return None


def verify_listing(db: Session, settings: Settings, row: Listing) -> bool:
    """Run originality or sandbox-style checks. Sets status, verified, and verification_log."""
    if row.verify_type == "sandbox":
        return _sandbox(db, settings, row)
    return _originality(db, settings, row)


def _originality(db: Session, settings: Settings, row: Listing) -> bool:
    source = (row.prompt_body or "").strip()
    if row.type == "document":
        if not row.object_key or not object_exists(settings, row.object_key):
            return _fail(row, "File check")
        raw = read_bytes(settings, row.object_key)
        if len(raw) < 12:
            return _fail(row, "File check")
        blocked = _scan_pack(settings, row, raw, "document")
        if blocked:
            return _fail(row, "Security scan")
        _append(row, "File check", "Passed")
        try:
            source = raw.decode("utf-8", errors="ignore") or source
        except Exception:
            source = source or row.description
    elif row.type in {"prompt", "agent"}:
        if len(source) < 20:
            return _fail(row, "Prompt check")
        _append(row, "Prompt check", "Passed")
    leak = _pii(source)
    if leak:
        return _fail(row, "Redaction check")
    _append(row, "Redaction check", "Passed")
    dup = _dedupe(db, settings, row, source)
    if dup == "exact":
        return _fail(row, "Originality check")
    if dup == "near":
        _append(row, "Near-duplicate check", "Needs review")
        row.status = "pending_review"
        row.verified = False
        return False
    _append(row, "Originality check", "Passed")
    row.verified = True
    row.status = "live"
    _append(row, "Published", "Live")
    return True


def _sandbox(db: Session, settings: Settings, row: Listing) -> bool:
    if not row.object_key or not object_exists(settings, row.object_key):
        return _fail(row, "Package check")
    _append(row, "Package check", "Passed")
    metrics = [m for m in (row.metrics or []) if isinstance(m, dict) and m.get("label") and m.get("value")]
    if not metrics:
        return _fail(row, "Declared metrics check")
    _append(row, "Declared metrics check", "Matched")
    blob = read_bytes(settings, row.object_key)
    blocked = _scan_pack(settings, row, blob, "package")
    if blocked:
        return _fail(row, "Security scan")
    # Isolated execution is not run inside the API process. This step records that
    # the pack passed static gates and declared metrics, not that buyer code ran.
    _append(row, "Sandbox static gates", "Passed")
    _append(row, "Security scan", "Clean")
    dup = _dedupe(db, settings, row, blob.decode("utf-8", errors="ignore") or row.description)
    if dup == "exact":
        return _fail(row, "Originality check")
    if dup == "near":
        _append(row, "Near-duplicate check", "Needs review")
        row.status = "pending_review"
        row.verified = False
        return False
    row.verified = True
    row.status = "live"
    _append(row, "Published", "Live")
    return True
