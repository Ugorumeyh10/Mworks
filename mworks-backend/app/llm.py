from __future__ import annotations

from urllib.parse import urlparse
import logging
import time

import httpx
from sqlalchemy.orm import Session, joinedload

from app.config import Settings
from app.models import AssistantMessage, JobApplication, Listing, Order, User
from app.scan import _SECRET

log = logging.getLogger("mworks.llm")

_HOSTS = {"api.deepseek.com"}
_SYSTEM = (
    "You are the Mworks account assistant for a Nigeria-first RPA and AI marketplace. "
    "You only know the ACCOUNT SNAPSHOT and recent chat below. "
    "Answer in plain English. No HTML. No tables. "
    "If the answer is not in the snapshot, say you do not see that on this account. "
    "Cite listing slugs and order refs (MW-) when you mention them. "
    "Amounts are Naira integers. Do not invent payouts, other users, or bank details. "
    "Do not help bypass verification, escrow, or authentication. "
    "Never repeat secrets or API keys. If a field is [redacted], say it was withheld."
)


class LlmError(RuntimeError):
    pass


def redact(text: str) -> str:
    return _SECRET.sub("[redacted]", text or "")


def _allowed_url(settings: Settings) -> str:
    base = (settings.DEEPSEEK_BASE_URL or "").strip().rstrip("/")
    parsed = urlparse(base)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in _HOSTS:
        raise LlmError("llm host is not allowed")
    return f"{base}/v1/messages"


def complete(
    settings: Settings,
    *,
    system: str,
    user: str,
    max_tokens: int = 512,
    user_limit: int = 4000,
    model: str | None = None,
    timeout: float = 20.0,
    retries: int = 3,
) -> str:
    if not settings.deepseek_enabled():
        raise LlmError("llm is disabled")
    url = _allowed_url(settings)
    chosen = (model or settings.DEEPSEEK_MODEL or "deepseek-v4-pro").strip()
    attempts = max(1, min(3, retries))
    payload = {
        "model": chosen,
        "max_tokens": max(64, min(1024, max_tokens)),
        "system": redact(system)[:8000],
        "messages": [{"role": "user", "content": redact(user)[: max(500, min(8000, user_limit))]}],
    }
    headers = {
        "x-api-key": settings.DEEPSEEK_API_KEY.strip(),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "User-Agent": "MworksAssistant/0.1",
    }
    last_err = "llm request failed"
    for attempt in range(attempts):
        try:
            with httpx.Client(timeout=max(4.0, min(20.0, timeout))) as client:
                res = client.post(url, json=payload, headers=headers)
            if res.status_code in {429, 500, 502, 503, 504} and attempt < attempts - 1:
                time.sleep(0.4 * (2**attempt))
                continue
            if res.status_code >= 400:
                log.warning("llm http %s", res.status_code)
                raise LlmError("llm request failed")
            body = res.json()
            chunks = body.get("content") if isinstance(body, dict) else None
            if not isinstance(chunks, list):
                raise LlmError("llm response was empty")
            text = "".join(
                (part.get("text") or "")
                for part in chunks
                if isinstance(part, dict) and part.get("type") == "text"
            ).strip()
            if not text:
                raise LlmError("llm response was empty")
            return text[:4000]
        except LlmError:
            raise
        except Exception:
            last_err = "llm request failed"
            if attempt < attempts - 1:
                time.sleep(0.4 * (2**attempt))
                continue
            log.warning("llm complete failed")
            raise LlmError(last_err) from None
    raise LlmError(last_err)


def account_snapshot(db: Session, user: User) -> str:
    lines = [
        f"Name: {user.name}",
        f"Role: {user.role}",
        f"Trust: {user.trust_score}",
        f"Country: {user.country}",
    ]
    listings = (
        db.query(Listing).filter(Listing.seller_id == user.id).order_by(Listing.created_at.desc()).limit(8).all()
    )
    if listings:
        lines.append("Listings:")
        for row in listings:
            lines.append(
                f"- slug={row.slug} title={row.title} status={row.status} "
                f"verified={row.verified} price_ngn={row.price_value}"
            )
    else:
        lines.append("Listings: none")
    orders = (
        db.query(Order)
        .filter((Order.buyer_id == user.id) | (Order.seller_id == user.id))
        .order_by(Order.created_at.desc())
        .limit(8)
        .all()
    )
    if orders:
        lines.append("Orders:")
        for row in orders:
            side = "seller" if row.seller_id == user.id else "buyer"
            lines.append(f"- {row.public_ref} side={side} state={row.state} amount_ngn={row.amount} kind={row.kind}")
    else:
        lines.append("Orders: none")
    apps = (
        db.query(JobApplication)
        .options(joinedload(JobApplication.job))
        .filter(JobApplication.applicant_id == user.id)
        .order_by(JobApplication.created_at.desc())
        .limit(8)
        .all()
    )
    if apps:
        lines.append("Applications:")
        for row in apps:
            title = row.job.title if row.job else "role"
            lines.append(f"- {row.public_id} job={title} status={row.status} fit={row.fit} via={row.via}")
    else:
        lines.append("Applications: none")
    return redact("\n".join(lines))[:6000]


def answer_account(db: Session, settings: Settings, user: User, question: str) -> str | None:
    if not settings.deepseek_enabled():
        return None
    history = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.user_id == user.id)
        .order_by(AssistantMessage.created_at.desc())
        .limit(8)
        .all()
    )
    history = list(reversed(history))
    chat = "\n".join(f"{row.role}: {redact(row.body)[:400]}" for row in history if row.body)
    user_block = (
        f"ACCOUNT SNAPSHOT\n{account_snapshot(db, user)}\n\n"
        f"RECENT CHAT\n{chat or '(none)'}\n\n"
        f"QUESTION\n{redact(question.strip())[:2000]}"
    )
    try:
        return complete(settings, system=_SYSTEM, user=user_block, max_tokens=512)
    except LlmError:
        return None
