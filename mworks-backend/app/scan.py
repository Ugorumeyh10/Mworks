from __future__ import annotations

from io import BytesIO
from urllib.parse import urlparse
from zipfile import BadZipFile, ZipFile
import logging
import re
import socket
import struct

from app.config import Settings

_SECRET = re.compile(
    r"(akia[0-9a-z]{16}|sk_live_[a-z0-9]+|-----begin (rsa )?private key-----|password\s*[:=]\s*\S+|api[_-]?key\s*[:=]\s*\S+)",
    re.I,
)

log = logging.getLogger("mworks.scan")

# Fail-closed signature pack. Not a substitute for ClamAV in production, but
# always runs, never calls a model, and rejects known-bad bytes.
EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
_MZ = b"MZ"
_ELF = b"\x7fELF"
_OLE = b"\xd0\xcf\x11\xe0"
_MACROS = re.compile(rb"vbaProject\.bin|word/vbaData|xl/vbaProject|ppt/vbaProject", re.I)
_TRAVERSAL = re.compile(rb"(^|/|\\)\.\.(/|\\)")
_PS_ENC = re.compile(rb"powershell[^\n]{0,80}-enc(odedcommand)?", re.I)
# Built-in YARA-style rules. No model, no untrusted code execution.
_YARA = (
    (re.compile(rb"(?i)frombase64string|invoke-expression|\biex\s*\("), "Encoded script dropper"),
    (re.compile(rb"(?i)<!entity[^>]{0,80}system"), "XML external entity"),
    (re.compile(rb"(?i)createobject\(\s*[\"']wscript\.shell"), "WScript shell"),
    (re.compile(rb"(?i)\b(eval|exec)\(\s*(base64|compile|__import__)"), "Dynamic code loader"),
)
_MACRO_EXT = {".docm", ".xlsm", ".pptm", ".dotm", ".xltm", ".doc", ".xls", ".ppt"}
_VIDEO_EXT = {".mp4", ".webm"}
_VIDEO_MIME = {"video/mp4", "video/webm"}
_CV_EXT = {".pdf", ".docx", ".md", ".txt"}
_KIND_EXT = {
    "document": {".pdf", ".docx", ".md", ".txt", ".xml", ".zip"},
    "package": {".zip", ".xml"},
    "preview": {".pdf", ".md", ".txt"},
    "delivery": {".pdf", ".docx", ".md", ".txt", ".xml", ".zip"},
    "cv": _CV_EXT,
    "interview_artifact": {".zip", ".xml", ".md", ".txt"},
    "interview_video": _VIDEO_EXT,
    "rag_doc": {".pdf", ".docx", ".md", ".txt"},
    "blog_image": {".jpg", ".jpeg", ".png", ".webp", ".gif"},
    "blog_video": _VIDEO_EXT,
}
_KIND_MIME = {
    "document": {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
        "text/plain",
        "application/xml",
        "application/zip",
    },
    "package": {"application/zip", "application/xml", "text/xml", "text/plain"},
    "preview": {"application/pdf", "text/markdown", "text/plain"},
    "delivery": {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
        "text/plain",
        "application/xml",
        "application/zip",
    },
    "cv": {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
        "text/plain",
    },
    "interview_artifact": {"application/zip", "application/xml", "text/markdown", "text/plain", "text/xml"},
    "interview_video": _VIDEO_MIME,
    "rag_doc": {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
        "text/plain",
    },
    "blog_image": {"image/jpeg", "image/png", "image/webp", "image/gif"},
    "blog_video": _VIDEO_MIME,
}
_KIND_MAX = {
    "document": 12_000_000,
    "package": 20_000_000,
    "preview": 4_000_000,
    "delivery": 20_000_000,
    "cv": 5_000_000,
    "interview_artifact": 8_000_000,
    "interview_video": 40_000_000,
    "rag_doc": 4_000_000,
    "blog_image": 8_000_000,
    "blog_video": 20_000_000,
}
SELLER_KINDS = {"document", "package", "preview", "delivery"}
AUTH_KINDS = {"cv", "interview_artifact", "interview_video", "rag_doc", "blog_image", "blog_video"}
ALL_KINDS = SELLER_KINDS | AUTH_KINDS


class ScanFailed(ValueError):
    def __init__(self, message: str, *, code: str = "SCAN_FAILED"):
        super().__init__(message)
        self.code = code


def kind_limits(kind: str) -> tuple[set[str], set[str], int]:
    if kind not in ALL_KINDS:
        raise ScanFailed("invalid upload kind", code="BAD_FILE")
    return _KIND_EXT[kind], _KIND_MIME[kind], _KIND_MAX[kind]


def sniff_kind(filename: str, content_type: str, kind: str, size_bytes: int | None) -> None:
    exts, mimes, max_bytes = kind_limits(kind)
    name = filename.lower()
    if not any(name.endswith(ext) for ext in exts):
        raise ScanFailed("file type is not allowed", code="BAD_FILE")
    if name.endswith(tuple(_MACRO_EXT)):
        raise ScanFailed("macro-enabled office files are not allowed", code="MACRO_BLOCKED")
    ctype = (content_type or "").split(";")[0].strip().lower()
    if kind in {"interview_video", "blog_video", "blog_image"}:
        if ctype not in mimes:
            raise ScanFailed("content type is not allowed", code="BAD_FILE")
    elif ctype not in mimes and not ctype.startswith("text/"):
        raise ScanFailed("content type is not allowed", code="BAD_FILE")
    if size_bytes is not None and (size_bytes < 1 or size_bytes > max_bytes):
        raise ScanFailed("file is too large", code="TOO_LARGE")


def _clamd_scan(settings: Settings, blob: bytes) -> str | None:
    host = (settings.CLAMD_HOST or "").strip()
    if not host:
        return None
    parsed = urlparse(f"tcp://{host}")
    hostname = (parsed.hostname or host).lower()
    if hostname not in {"clamav", "localhost", "127.0.0.1"}:
        raise ScanFailed("scanner host is not allowed", code="SCAN_DOWN")
    port = settings.CLAMD_PORT or 3310
    try:
        sock = socket.create_connection((hostname, port), timeout=4)
    except OSError:
        return "unavailable"
    try:
        sock.sendall(b"nINSTREAM\n")
        view = memoryview(blob)
        offset = 0
        while offset < len(view):
            chunk = view[offset : offset + 2048]
            sock.sendall(struct.pack(">I", len(chunk)) + chunk.tobytes())
            offset += 2048
        sock.sendall(struct.pack(">I", 0))
        sock.settimeout(8)
        reply = sock.recv(4096).decode("utf-8", errors="ignore")
    except OSError:
        return "unavailable"
    finally:
        try:
            sock.close()
        except OSError:
            pass
    if "FOUND" in reply.upper():
        return reply.strip()[:180]
    if "ERROR" in reply.upper():
        return "unavailable"
    return None


def scan_bytes(settings: Settings, blob: bytes, *, filename: str = "pack.bin", kind: str = "document") -> list[str]:
    """Return reasons if dirty. Empty list means clean. Never calls a model."""
    reasons: list[str] = []
    _, _, max_bytes = kind_limits(kind)
    if len(blob) > max_bytes:
        raise ScanFailed("file is too large", code="TOO_LARGE")
    if len(blob) < 8 and kind != "cv":
        reasons.append("File is empty or too small.")
    if blob[:2] == _MZ or blob[:4] == _ELF:
        reasons.append("Executable binaries are not allowed.")
    if blob[:4] == _OLE:
        reasons.append("OLE compound files with possible macros are not allowed.")
    if EICAR in blob:
        reasons.append("Antivirus test signature was detected.")
    if _PS_ENC.search(blob):
        reasons.append("Encoded PowerShell was detected.")
    for rule, label in _YARA:
        if rule.search(blob):
            reasons.append(f"{label} signature was detected.")
            break
    if _SECRET.search(blob.decode("utf-8", errors="ignore")):
        reasons.append("Credentials or a private key were detected.")
    name = filename.lower()
    if name.endswith(tuple(_MACRO_EXT)):
        reasons.append("Macro-enabled office files are not allowed.")
    if blob[:2] == b"PK":
        try:
            zf = ZipFile(BytesIO(blob))
        except BadZipFile:
            reasons.append("Zip archive is corrupt.")
        else:
            names = zf.namelist()
            if len(names) > 400:
                reasons.append("Zip archive has too many entries.")
            uncompressed = 0
            for info in zf.infolist():
                uncompressed += max(0, info.file_size)
                if info.file_size > max_bytes:
                    reasons.append("Zip entry is too large.")
                    break
                raw_name = info.filename.encode("utf-8", errors="ignore")
                if _TRAVERSAL.search(raw_name) or info.filename.startswith("/"):
                    reasons.append("Zip path traversal was detected.")
                    break
                if _MACROS.search(raw_name):
                    reasons.append("Office macros inside the zip are not allowed.")
                    break
            if uncompressed > max_bytes * 8:
                reasons.append("Zip compression ratio looks unsafe.")
            zf.close()
    if settings.clamav_required() and not (settings.CLAMD_HOST or "").strip():
        raise ScanFailed("Malware scanner is unavailable.", code="SCAN_DOWN")
    if (settings.CLAMD_HOST or "").strip():
        hit = _clamd_scan(settings, blob)
        if hit == "unavailable":
            if settings.clamav_required():
                raise ScanFailed("Malware scanner is unavailable.", code="SCAN_DOWN")
            log.warning("clamav unavailable; builtin signatures still applied")
        elif hit:
            reasons.append("Malware scanner flagged this file.")
    return reasons
