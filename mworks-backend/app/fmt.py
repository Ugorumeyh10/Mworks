from datetime import datetime, timezone
import re
import uuid


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(title: str, *, prefix: str = "") -> str:
    base = _SLUG_RE.sub("-", title.lower()).strip("-")[:48] or "item"
    suffix = uuid.uuid4().hex[:6]
    if prefix:
        return f"{prefix}{base}-{suffix}"
    return f"{base}-{suffix}"


def avatar(name: str) -> str:
    cleaned = (name or "?").strip()
    parts = [p for p in re.split(r"\s+", cleaned) if p]
    if len(parts) >= 2:
        return (parts[0][:1] + parts[1][:1]).upper()[:2]
    return (cleaned[:2] if len(cleaned) >= 2 else cleaned[:1] or "?").upper()


def ago(stamp: datetime | None) -> str:
    if stamp is None:
        return ""
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    seconds = int((datetime.now(timezone.utc) - stamp).total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h"
    days = hours // 24
    if days == 1:
        return "1 day ago"
    if days < 14:
        return f"{days} days ago"
    return stamp.strftime("%b %d, %Y").replace(" 0", " ")


def placed(stamp: datetime | None) -> str:
    if stamp is None:
        return ""
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.strftime("%b %d, %Y").replace(" 0", " ")
