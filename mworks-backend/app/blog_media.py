"""Allowlisted media URLs for the newsroom. No HTML, no arbitrary hosts."""

from __future__ import annotations

from urllib.parse import urlparse
import re

_YT = re.compile(
    r"(?:youtube\.com/(?:watch\?[^<\s]*v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)
_LOCAL = re.compile(r"^/[a-zA-Z0-9._/-]+\.(?:jpe?g|png|webp|gif|mp4|webm)$", re.I)
_IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif")
_VID_EXT = (".mp4", ".webm")
_OBJECT = re.compile(r"^blog_(image|video)/[a-z0-9]+/[A-Za-z0-9._%+-]+$")

MEDIA_HOSTS = {
    "techcabal.com",
    "www.techcabal.com",
    "techpoint.africa",
    "www.techpoint.africa",
    "cdn.vox-cdn.com",
    "www.theverge.com",
    "platform.theverge.com",
    "i0.wp.com",
    "i1.wp.com",
    "i2.wp.com",
    "i.wp.com",
    "www.youtube.com",
    "youtube.com",
    "youtu.be",
    "www.youtube-nocookie.com",
    "i.ytimg.com",
    "img.youtube.com",
}


def youtube_id(url: str) -> str | None:
    match = _YT.search(url or "")
    return match.group(1) if match else None


def is_object_key(url: str) -> bool:
    return bool(_OBJECT.match((url or "").strip()))


def _host_ok(host: str) -> bool:
    host = (host or "").lower()
    if host in MEDIA_HOSTS:
        return True
    return host.endswith(".wp.com") or host.endswith(".vox-cdn.com")


def https_ok(url: str) -> bool:
    parsed = urlparse(url or "")
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return False
    return _host_ok(parsed.hostname or "")


def classify_url(url: str) -> str | None:
    raw = (url or "").strip()
    if not raw:
        return None
    if youtube_id(raw):
        return "youtube"
    path = urlparse(raw).path.lower()
    if any(path.endswith(ext) for ext in _VID_EXT):
        return "video"
    if any(path.endswith(ext) for ext in _IMG_EXT) or "image" in path or "/photo" in path:
        return "image"
    if is_object_key(raw):
        return "video" if raw.startswith("blog_video/") else "image"
    if _LOCAL.match(raw):
        return "video" if raw.lower().endswith((".mp4", ".webm")) else "image"
    return "image" if https_ok(raw) else None


def normalize_item(raw: dict | str) -> dict | None:
    if isinstance(raw, str):
        raw = {"url": raw}
    if not isinstance(raw, dict):
        return None
    url = str(raw.get("url") or "").strip()[:512]
    if not url:
        return None
    yt = youtube_id(url)
    if yt:
        return {"kind": "youtube", "url": f"https://www.youtube.com/watch?v={yt}"}
    if is_object_key(url):
        kind = "video" if url.startswith("blog_video/") else "image"
        return {"kind": kind, "url": url}
    if _LOCAL.match(url):
        kind = "video" if url.lower().endswith((".mp4", ".webm")) else "image"
        return {"kind": kind, "url": url}
    if not https_ok(url):
        return None
    kind = str(raw.get("kind") or classify_url(url) or "image")
    if kind not in {"image", "video", "youtube"}:
        kind = "image"
    return {"kind": kind, "url": url}


def normalize_media(items: list | None, *, limit: int = 6) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for item in items or []:
        row = normalize_item(item)
        if row is None or row["url"] in seen:
            continue
        seen.add(row["url"])
        out.append(row)
        if len(out) >= limit:
            break
    return out


def cover_from(media: list[dict]) -> str | None:
    for row in media:
        if row.get("kind") == "image":
            return row["url"]
    for row in media:
        if row.get("kind") == "youtube":
            vid = youtube_id(row["url"])
            if vid:
                return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    return None
