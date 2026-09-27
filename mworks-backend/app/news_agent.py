"""Newsroom agent: pulls latest tech headlines from public RSS/Atom feeds and
publishes short, attributed summaries with pictures or video when the feed
includes them. Bodies are original summaries plus a link to the source."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urlparse
from xml.etree import ElementTree
import json
import logging
import re

import httpx
from sqlalchemy.orm import Session

from app.blog_media import cover_from, https_ok, normalize_media, youtube_id
from app.config import Settings
from app.fmt import slugify
from app.llm import LlmError, complete, redact
from app.models import BlogPost

log = logging.getLogger("mworks.news")

FEEDS = [
    ("TechCabal", "https://techcabal.com/feed/"),
    ("Techpoint Africa", "https://techpoint.africa/feed/"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("Hacker News", "https://hnrss.org/frontpage"),
]
_HOSTS = {"techcabal.com", "techpoint.africa", "www.theverge.com", "hnrss.org"}
_ARTICLE_HOSTS = {
    "techcabal.com",
    "www.techcabal.com",
    "techpoint.africa",
    "www.techpoint.africa",
    "www.theverge.com",
    "www.youtube.com",
    "youtu.be",
}
_HTML = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")
_IMG_SRC = re.compile(r"<img[^>]+src=['\"]([^'\"]+)['\"]", re.I)
_OG_IMAGE = re.compile(
    r'<meta[^>]+(?:property|name)=[\'"]og:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
    re.I,
)
_OG_IMAGE_REV = re.compile(
    r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+(?:property|name)=[\'"]og:image[\'"]',
    re.I,
)
_OG_VIDEO = re.compile(
    r'<meta[^>]+(?:property|name)=[\'"]og:video(?::url)?[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
    re.I,
)
_MAX_PER_RUN = 4

_SUMMARY_SYSTEM = (
    "You are the Mworks newsroom assistant for a Nigeria-first RPA and AI marketplace. "
    "Rewrite the headline and snippet below into a short original blog draft. "
    "Reply with JSON only: {\"excerpt\": \"one friendly sentence, max 40 words\", "
    "\"body\": \"two short paragraphs in plain English on what happened and why it matters "
    "to African builders and automation teams\"}. "
    "Do not copy sentences from the snippet. Do not invent facts that are not in the snippet. "
    "No HTML. No hashtags."
)

_TEST_ITEMS = [
    {
        "source_name": "TechCabal",
        "source_url": "https://techcabal.com/sample/agentic-payments",
        "title": "Nigerian fintechs pilot agentic payment reconciliation",
        "snippet": "Several Lagos fintechs are piloting AI agents that reconcile settlement files overnight, cutting manual close-cycle work.",
        "media": [
            {"kind": "image", "url": "https://techcabal.com/wp-content/uploads/sample-agentic.jpg"},
        ],
    },
    {
        "source_name": "The Verge",
        "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "A new open-weight model tops coding benchmarks",
        "snippet": "An open-weight model released this week beats larger closed models on common coding benchmarks while running on a single GPU.",
        "media": [
            {"kind": "youtube", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        ],
    },
]


def _clean(text: str) -> str:
    return _SPACE.sub(" ", _HTML.sub(" ", unescape(text or ""))).strip()


def _tag(el: ElementTree.Element) -> str:
    return el.tag.rsplit("}", 1)[-1].lower()


def _attr(el: ElementTree.Element, *names: str) -> str:
    for name in names:
        val = el.get(name)
        if val:
            return val.strip()
        for key, value in el.attrib.items():
            if key.rsplit("}", 1)[-1].lower() == name.lower() and value:
                return value.strip()
    return ""


def _media_from_html(raw: str) -> list[dict]:
    found: list[dict] = []
    for src in _IMG_SRC.findall(raw or ""):
        url = unescape(src).strip()
        if https_ok(url):
            found.append({"kind": "image", "url": url})
    yt = youtube_id(raw or "")
    if yt:
        found.append({"kind": "youtube", "url": f"https://www.youtube.com/watch?v={yt}"})
    return found


def _media_from_node(node: ElementTree.Element, link: str) -> list[dict]:
    found: list[dict] = []
    html_blob = ""
    for child in node.iter():
        tag = _tag(child)
        url = _attr(child, "url", "href")
        mime = (_attr(child, "type") or "").lower()
        medium = (_attr(child, "medium") or "").lower()
        if tag in {"enclosure", "content", "thumbnail"} and url:
            if mime.startswith("video") or medium == "video" or url.lower().endswith((".mp4", ".webm")):
                found.append({"kind": "video", "url": url})
            elif mime.startswith("image") or medium == "image" or tag == "thumbnail":
                found.append({"kind": "image", "url": url})
            elif youtube_id(url):
                found.append({"kind": "youtube", "url": url})
        if tag in {"description", "summary", "encoded", "content"}:
            html_blob += child.text or ""
            html_blob += "".join(ElementTree.tostring(el, encoding="unicode") for el in list(child))
    found.extend(_media_from_html(html_blob))
    if youtube_id(link):
        found.append({"kind": "youtube", "url": link})
    return normalize_media(found)


def _parse_feed(source_name: str, raw: bytes) -> list[dict]:
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError:
        return []
    items: list[dict] = []
    nodes = [el for el in root.iter() if _tag(el) in {"item", "entry"}]
    for node in nodes[:10]:
        title = ""
        link = ""
        snippet = ""
        for child in node:
            tag = _tag(child)
            if tag == "title":
                title = _clean(child.text or "")
            elif tag == "link":
                link = (child.get("href") or child.text or "").strip()
            elif tag in {"description", "summary", "content"} and not snippet:
                snippet = _clean(child.text or "")
        if not title or not link:
            continue
        items.append(
            {
                "source_name": source_name,
                "source_url": link[:512],
                "title": title[:180],
                "snippet": snippet[:600],
                "media": _media_from_node(node, link),
            }
        )
    return items


def _fetch_one(source_name: str, url: str) -> list[dict]:
    host = (urlparse(url).hostname or "").lower()
    if host not in _HOSTS:
        return []
    try:
        with httpx.Client(timeout=5.0, follow_redirects=True) as client:
            res = client.get(url, headers={"User-Agent": "MworksNewsroom/0.1"})
        if res.status_code != 200:
            return []
        return _parse_feed(source_name, res.content)
    except Exception:
        log.warning("news feed failed source=%s", source_name)
        return []


def _og_media(url: str) -> list[dict]:
    host = (urlparse(url).hostname or "").lower()
    if host not in _ARTICLE_HOSTS:
        return []
    try:
        with httpx.Client(timeout=4.0, follow_redirects=True) as client:
            res = client.get(url, headers={"User-Agent": "MworksNewsroom/0.1"})
        if res.status_code != 200 or not res.headers.get("content-type", "").startswith("text/html"):
            return []
        html = res.text[:80_000]
        found: list[dict] = []
        for match in list(_OG_IMAGE.finditer(html))[:2] + list(_OG_IMAGE_REV.finditer(html))[:2]:
            found.append({"kind": "image", "url": unescape(match.group(1).strip())})
        for match in _OG_VIDEO.finditer(html):
            found.append({"kind": "video", "url": unescape(match.group(1).strip())})
        yt = youtube_id(html)
        if yt:
            found.append({"kind": "youtube", "url": f"https://www.youtube.com/watch?v={yt}"})
        return normalize_media(found, limit=3)
    except Exception:
        return []


def _mix_sources(items: list[dict]) -> list[dict]:
    buckets: dict[str, list[dict]] = {}
    order: list[str] = []
    for item in items:
        name = item["source_name"]
        if name not in buckets:
            buckets[name] = []
            order.append(name)
        buckets[name].append(item)
    mixed: list[dict] = []
    while buckets:
        for name in list(order):
            bucket = buckets.get(name)
            if not bucket:
                buckets.pop(name, None)
                continue
            mixed.append(bucket.pop(0))
            if not bucket:
                buckets.pop(name, None)
    return mixed


def fetch_feed_items(settings: Settings) -> list[dict]:
    if settings.APP_ENV == "test":
        return list(_TEST_ITEMS)
    items: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(FEEDS)) as pool:
        futs = [pool.submit(_fetch_one, name, url) for name, url in FEEDS]
        for fut in as_completed(futs):
            items.extend(fut.result() or [])
    return _mix_sources(items)


_JSON = re.compile(r"\{.*\}", re.S)


def _draft_copy(settings: Settings, item: dict) -> tuple[str, str]:
    fallback_excerpt = (item["snippet"] or item["title"])[:280]
    fallback_body = (
        f"{item['snippet'] or item['title']}\n\n"
        f"Read the full story at {item['source_name']}."
    )
    if not settings.deepseek_enabled():
        return fallback_excerpt, fallback_body
    try:
        raw = complete(
            settings,
            system=_SUMMARY_SYSTEM,
            user=f"HEADLINE: {item['title']}\nSNIPPET: {item['snippet']}\nSOURCE: {item['source_name']}",
            max_tokens=400,
            model=(settings.DEEPSEEK_MODEL_FAST or "").strip() or None,
            timeout=8.0,
            retries=1,
        )
        match = _JSON.search(raw or "")
        if match:
            data = json.loads(match.group(0))
            excerpt = redact(str(data.get("excerpt") or ""))[:280].strip()
            body = redact(str(data.get("body") or ""))[:4000].strip()
            if excerpt and body:
                return excerpt, body
    except (LlmError, ValueError):
        pass
    return fallback_excerpt, fallback_body


def _publish_agent_drafts(db: Session) -> None:
    now = datetime.now(timezone.utc)
    rows = db.query(BlogPost).filter(BlogPost.source == "agent", BlogPost.status == "draft").all()
    for row in rows:
        row.status = "published"
        if row.published_at is None:
            row.published_at = now


def run_news_agent(db: Session, settings: Settings) -> tuple[int, int]:
    """Write and auto-publish posts from feed items. Returns (created, skipped)."""
    _publish_agent_drafts(db)
    created = 0
    skipped = 0
    now = datetime.now(timezone.utc)
    for item in fetch_feed_items(settings):
        if created >= _MAX_PER_RUN:
            break
        exists = db.query(BlogPost).filter(BlogPost.source_url == item["source_url"]).one_or_none()
        if exists is not None:
            skipped += 1
            if settings.APP_ENV != "test" and not (exists.media or []):
                incoming = normalize_media(item.get("media") or []) or _og_media(item["source_url"])
                if incoming:
                    exists.media = incoming
                    exists.cover_url = cover_from(incoming)
            continue
        excerpt, body = _draft_copy(settings, item)
        media = list(item.get("media") or [])
        if settings.APP_ENV != "test" and not media:
            media = _og_media(item["source_url"])
        media = normalize_media(media)
        words = len(body.split())
        db.add(
            BlogPost(
                slug=slugify(item["title"]),
                title=item["title"],
                excerpt=excerpt,
                body=body,
                category="Tech news",
                tags=["News", item["source_name"]],
                source="agent",
                source_name=item["source_name"],
                source_url=item["source_url"],
                status="published",
                cover_url=cover_from(media),
                media=media,
                read_minutes=max(1, min(12, round(words / 180) or 1)),
                published_at=now,
            )
        )
        created += 1
    db.commit()
    return created, skipped
