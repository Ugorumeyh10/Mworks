from __future__ import annotations

from html import unescape
from urllib.parse import urlparse
import logging
import re

import httpx
from sqlalchemy.orm import Session

from app.config import Settings
from app.fmt import avatar, slugify
from app.models import Job, User
from app.security import hash_password

log = logging.getLogger("mworks.ingest")

BOT_EMAIL = "jobs-bot@mworks.ng"
_HOSTS = {
    "boards-api.greenhouse.io",
    "api.lever.co",
    "www.arbeitnow.com",
}
# Greenhouse "token" = public board slug from boards.greenhouse.io/{slug}. Not an API key.
_TOKEN = re.compile(r"^[a-z0-9-]{2,48}$")
_HTML = re.compile(r"<[^>]+>")
_SCRIPT = re.compile(r"<script[\s\S]*?</script>", re.I)
_STYLE = re.compile(r"<style[\s\S]*?</style>", re.I)
_SPACE = re.compile(r"\s+")
_BR = re.compile(r"<br\s*/?>", re.I)
_LI_OPEN = re.compile(r"<li\b[^>]*>", re.I)
_LI_BLOCK = re.compile(r"<li\b[^>]*>([\s\S]*?)</li>", re.I)
_LIST_BLOCK = re.compile(r"<(ul|ol)\b[^>]*>[\s\S]*?</\1>", re.I)
_HEADING = re.compile(r"<h[1-6]\b[^>]*>", re.I)
_BLOCK_CLOSE = re.compile(r"</(p|div|h[1-6]|li|tr|section|article|blockquote|header|footer)>", re.I)
_PAY = re.compile(r"\$\s*[\d,]{3,}\s*(?:[-–—]|to)\s*\$\s*[\d,]{3,}(?:\s*USD)?", re.I)
_LIST_HEADINGS = {
    "what you'll do",
    "what you’ll do",
    "what you will do",
    "what you'll bring",
    "what you’ll bring",
    "what you will bring",
    "responsibilities",
    "requirements",
    "qualifications",
}

_TITLE_HIT = re.compile(
    r"\b(rpa|uipath|power automate|automation anywhere|n8n|zapier|"
    r"hyperautomation|intelligent automation|process automation|"
    r"automation engineer|ai engineer|ai architect|machine learning|"
    r"ml engineer|mlops|llm|genai|generative ai|prompt engineer|"
    r"document intelligence|robotic process)\b",
    re.I,
)
_SOFT_HIT = re.compile(
    r"\b(automation|rpa|uipath|ai|llm|mlops|machine learning|power automate|"
    r"copilot|ocr|n8n|agentic)\b",
    re.I,
)
_SKILLS = (
    "Power Automate",
    "UiPath",
    "Python",
    "SQL",
    "OCR",
    "LLM",
    "n8n",
    "Zapier",
    "Requirements",
    "Process mapping",
    "Solution design",
    "Governance",
    "Cloud",
    "Security architecture",
)


def looks_like_markup(text: str) -> bool:
    blob = text or ""
    return "<" in blob or "&lt;" in blob


def decode_board_html(raw: str) -> str:
    text = raw or ""
    # Greenhouse JSON often HTML-encodes the whole posting before the tags.
    for _ in range(2):
        nxt = unescape(text)
        if nxt == text:
            break
        text = nxt
    return text.replace("\xa0", " ")


def _plain(raw: str, limit: int = 8000) -> str:
    text = decode_board_html(raw)
    text = _SCRIPT.sub(" ", text)
    text = _STYLE.sub(" ", text)
    text = _BR.sub("\n", text)
    text = _HEADING.sub("\n\n", text)
    text = _LI_OPEN.sub("\n• ", text)
    text = _BLOCK_CLOSE.sub("\n", text)
    text = _HTML.sub(" ", text)
    text = unescape(text)
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    lines = [_SPACE.sub(" ", line).strip() for line in text.splitlines()]
    packed: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if packed and not blank:
                packed.append("")
            blank = True
            continue
        blank = False
        packed.append(line)
    return "\n".join(packed).strip()[:limit]


def list_items(raw: str) -> list[str]:
    items: list[str] = []
    for match in _LI_BLOCK.finditer(decode_board_html(raw)):
        item = _plain(match.group(1), 400)
        if len(item) >= 12:
            items.append(item[:280])
        if len(items) >= 10:
            break
    return items


def job_copy(raw: str) -> tuple[str, list[str]]:
    html = decode_board_html(raw)
    items = list_items(html)
    description = _plain(_LIST_BLOCK.sub(" ", html), 8000)
    if len(description) < 40:
        description = _plain(html, 8000)
    if items:
        kept: list[str] = []
        for line in description.split("\n"):
            if line.strip().lower() in _LIST_HEADINGS:
                continue
            kept.append(line)
        description = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
    return description, items


def pay_range(raw: str) -> str:
    found = _PAY.search(_plain(raw, 8000))
    if not found:
        return ""
    return _SPACE.sub(" ", found.group(0)).replace("\u2014", "-").replace("\u2013", "-").strip()


def refresh_copy(row: Job, raw: str | None = None) -> None:
    blob = row.description if raw is None else raw
    if not looks_like_markup(blob or ""):
        return
    description, items = job_copy(blob)
    if len(description) >= 40:
        row.description = description
    if items and not (row.responsibilities or []):
        row.responsibilities = items
    if (row.salary or "").startswith("Listed on"):
        found = pay_range(blob)
        if found:
            row.salary = found[:120]


def is_automation_role(title: str, *, body: str = "", tags: list[str] | None = None) -> bool:
    hay_title = title or ""
    if _TITLE_HIT.search(hay_title):
        return True
    blob = " ".join([hay_title, body or "", " ".join(tags or "")])
    hits = {m.group(0).lower() for m in _SOFT_HIT.finditer(blob)}
    if "rpa" in hits or "uipath" in hits or "power automate" in hits:
        return True
    if {"ai", "llm", "machine learning", "mlops", "genai"} & hits and "automation" in hits:
        return True
    if hay_title.lower().count("ai") and ("engineer" in hay_title.lower() or "architect" in hay_title.lower()):
        return True
    return False


def classify_track(title: str, body: str = "") -> str:
    blob = f"{title} {body}".lower()
    if any(w in blob for w in ("business analyst", "process mapping", "requirements")):
        return "Business Analyst"
    if any(w in blob for w in ("project manager", "delivery manager", "programme manager", "program manager")):
        return "Project Manager"
    if any(w in blob for w in ("solution architect", "ai architect", "platform architect", "security architect")):
        return "Solution Architect"
    if any(w in blob for w in ("machine learning", "ml engineer", "llm", "genai", "ai engineer")):
        return "Solution Architect"
    return "RPA Developer"


def classify_type(raw: str) -> str:
    text = (raw or "").lower()
    if any(w in text for w in ("contract", "freelance", "contractor")):
        return "Contract"
    if any(w in text for w in ("gig", "project", "one-off", "fixed-term")):
        return "Project gig"
    return "Full-time"


def _skills(blob: str, tags: list[str] | None = None) -> list[str]:
    found: list[str] = []
    hay = f"{blob} {' '.join(tags or [])}".lower()
    for skill in _SKILLS:
        if skill.lower() in hay and skill not in found:
            found.append(skill)
        if len(found) >= 8:
            break
    return found


def ingest_bot(db: Session, settings: Settings) -> User:
    row = db.query(User).filter(User.email == BOT_EMAIL).one_or_none()
    if row:
        return row
    row = User(
        email=BOT_EMAIL,
        name="Mworks Job Bot",
        role="both",
        password_hash=hash_password(settings.DEMO_USER_PASSWORD),
        trust_score=90,
        sales_count=0,
        rating=0.0,
        review_count=0,
        country="Nigeria",
        is_admin=False,
    )
    db.add(row)
    db.flush()
    return row


def _get_json(url: str, fetch) -> dict | list | None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _HOSTS:
        log.warning("ingest skipped host %s", parsed.hostname)
        return None
    try:
        payload = fetch(url)
    except Exception:
        log.warning("ingest fetch failed %s", url)
        return None
    return payload if isinstance(payload, (dict, list)) else None


def default_fetch(url: str) -> dict | list:
    with httpx.Client(timeout=12.0, follow_redirects=True, headers={"User-Agent": "MworksJobIngest/0.1"}) as client:
        res = client.get(url)
        if res.status_code == 404:
            return {}
        res.raise_for_status()
        if len(res.content) > 1_500_000:
            raise ValueError("payload too large")
        return res.json()


def _upsert(db: Session, bot: User, item: dict, *, max_new: int, added: list[str]) -> None:
    key = (item.get("external_key") or "").strip()[:180]
    if not key:
        return
    raw_desc = item.get("description") or ""
    existing = db.query(Job).filter(Job.external_key == key).one_or_none()
    if existing:
        refresh_copy(existing, raw_desc)
        return
    if len(added) >= max_new:
        return
    title = (item.get("title") or "").strip()[:160]
    title = title.replace("\u2014", "-").replace("\u2013", "-")
    company = (item.get("company") or "Employer").strip()[:120]
    description, bullets = job_copy(raw_desc)
    if len(description) < 40:
        description = f"{title} is an AI or automation role sourced from a public career board."
    if not is_automation_role(title, body=description, tags=item.get("tags") or []):
        return
    apply = (item.get("url") or "").strip()
    if not apply.startswith("https://"):
        apply = ""
    salary = (item.get("salary") or "").strip() or pay_range(raw_desc) or "Listed on original posting"
    row = Job(
        slug=slugify(title),
        poster_id=bot.id,
        title=title,
        company=company,
        company_avatar=avatar(company)[:2],
        verified_employer=False,
        track=classify_track(title, description),
        type=classify_type(item.get("commitment") or ""),
        location=(item.get("location") or "Remote").strip()[:120] or "Remote",
        salary=salary[:120],
        salary_min=0,
        min_trust=70,
        skills=_skills(f"{title} {description}", item.get("tags")),
        about=f"Sourced from {item.get('source') or 'a public career board'}. Apply on Mworks with your trust score.",
        description=description,
        responsibilities=item.get("responsibilities") or bullets,
        applicant_count=0,
        status="live",
        source=(item.get("source") or "board")[:32],
        external_key=key,
        apply_url=apply[:512] or None,
    )
    db.add(row)
    db.flush()
    added.append(row.slug)


def _greenhouse_jobs(board: str, fetch) -> list[dict]:
    if not _TOKEN.match(board):
        return []
    listing = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", fetch)
    jobs = (listing or {}).get("jobs") if isinstance(listing, dict) else None
    if not isinstance(jobs, list):
        return []
    out: list[dict] = []
    for row in jobs[:40]:
        job_id = row.get("id")
        title = (row.get("title") or "").strip()
        if not job_id or not title:
            continue
        if not is_automation_role(title):
            continue
        detail = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}", fetch)
        if not isinstance(detail, dict):
            detail = row
        loc = ""
        if isinstance(detail.get("location"), dict):
            loc = detail["location"].get("name") or ""
        elif isinstance(row.get("location"), dict):
            loc = row["location"].get("name") or ""
        company = board.replace("-", " ").title()
        out.append(
            {
                "external_key": f"greenhouse:{board}:{job_id}",
                "source": "greenhouse",
                "title": title,
                "company": company,
                "location": loc or "Remote",
                "description": detail.get("content") or title,
                "url": detail.get("absolute_url") or row.get("absolute_url") or "",
                "commitment": "",
                "tags": [],
            }
        )
        if len(out) >= 12:
            break
    return out


def _arbeitnow_jobs(fetch) -> list[dict]:
    payload = _get_json("https://www.arbeitnow.com/api/job-board-api", fetch)
    rows = (payload or {}).get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return []
    out: list[dict] = []
    for row in rows[:80]:
        title = (row.get("title") or "").strip()
        tags = row.get("tags") or []
        if not title or not is_automation_role(title, body=row.get("description") or "", tags=tags if isinstance(tags, list) else []):
            continue
        job_types = row.get("job_types") or []
        commitment = " ".join(job_types) if isinstance(job_types, list) else str(job_types)
        slug = row.get("slug") or row.get("url") or title
        out.append(
            {
                "external_key": f"arbeitnow:{str(slug)[:120]}",
                "source": "arbeitnow",
                "title": title[:160],
                "company": (row.get("company_name") or "Employer").strip()[:120],
                "location": (row.get("location") or "Remote")[:120],
                "description": row.get("description") or title,
                "url": (row.get("url") or "")[:512],
                "commitment": commitment,
                "tags": tags if isinstance(tags, list) else [],
            }
        )
        if len(out) >= 12:
            break
    return out


def collect_jobs(settings: Settings, fetch) -> list[dict]:
    found: list[dict] = []
    for spec in settings.job_ingest_sources():
        try:
            if spec == "arbeitnow":
                found.extend(_arbeitnow_jobs(fetch))
            elif spec.startswith("greenhouse:"):
                found.extend(_greenhouse_jobs(spec.split(":", 1)[1], fetch))
        except Exception:
            log.warning("ingest source failed %s", spec, exc_info=True)
    return found


def ingest_once(db: Session, settings: Settings, fetch=None) -> dict:
    fetch = fetch or default_fetch
    bot = ingest_bot(db, settings)
    added: list[str] = []
    seen: set[str] = set()
    for item in collect_jobs(settings, fetch):
        key = item.get("external_key")
        if not key or key in seen:
            continue
        seen.add(key)
        _upsert(db, bot, item, max_new=max(1, min(40, settings.JOB_INGEST_MAX_NEW)), added=added)
    for row in db.query(Job).filter(Job.source.isnot(None)).all():
        refresh_copy(row)
    db.commit()
    return {"scanned": len(seen), "posted": len(added), "slugs": added}
