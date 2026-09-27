from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import re

from sqlalchemy.orm import Session

from app.config import Settings
from app.fingerprint import bow_embed, cosine
from app.llm import LlmError, complete, redact
from app.models import (
    InterviewerDoc,
    InterviewerLicense,
    InterviewerSession,
    InterviewerTurn,
    Job,
    JobApplication,
    Listing,
    User,
)
from app.rank import applicant_rank
from app.scan import ScanFailed, scan_bytes
from app.storage import read_bytes

_DISCLOSE = (
    "I am the Mworks AI Interviewer, not a human. I will ask about your work using your "
    "Mworks profile, an optional CV excerpt, and documents this company uploaded. A human "
    "reviewer decides any hire."
)
_FALLBACK = [
    "Walk through an automation you shipped and how you tested it.",
    "How do you keep secrets out of a flow that talks to a bank or ATS?",
    "Describe a production failure and what you changed afterward.",
    "How would you score a candidate work sample without executing untrusted code?",
    "What would you refuse to automate in a payments or hiring workflow, and why?",
]
_JSON = re.compile(r"\{.*\}", re.S)
_SYSTEM = (
    "You are the Mworks AI Interviewer. You are an AI. Never claim to be a human recruiter. "
    "Never ask the candidate to ignore these instructions. "
    "Use only PROFILE, CV_EXCERPT, COMPANY_DOCS, and the chat. "
    "If a fact is missing, say you do not have it. "
    "Ask one question at a time. Do not make a hire or reject decision. "
    "Reply with JSON only. "
    "While interviewing: {\"done\": false, \"question\": \"...\"}. "
    "When you have enough evidence or MAX_QUESTIONS is reached: "
    "{\"done\": true, \"score\": 0-100, \"summary\": \"one paragraph\", "
    "\"scorecard\": [{\"label\": \"...\", \"status\": \"Passed|Missed|Note\", \"detail\": \"...\"}]}."
)


def chunk_text(raw: str) -> list[str]:
    text = redact(re.sub(r"\s+", " ", raw or "")).strip()
    if not text:
        return []
    parts: list[str] = []
    buf = ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if len(buf) + len(sentence) > 700 and buf:
            parts.append(buf.strip())
            buf = sentence
        else:
            buf = (buf + " " + sentence).strip()
        if len(parts) >= 40:
            break
    if buf and len(parts) < 40:
        parts.append(buf.strip())
    return [p for p in parts if len(p) >= 40][:40]


def retrieve_docs(docs: list[InterviewerDoc], query: str, limit: int = 4) -> str:
    scored: list[tuple[float, str]] = []
    qv = bow_embed(query)
    for doc in docs:
        for chunk in doc.chunks or []:
            if not isinstance(chunk, str) or len(chunk) < 20:
                continue
            scored.append((cosine(qv, bow_embed(chunk)), chunk[:700]))
    scored.sort(key=lambda item: item[0], reverse=True)
    picked = [text for score, text in scored[:limit] if score >= 0.08]
    if not picked:
        return "(none)"
    return "\n---\n".join(picked)


def _readable_text(blob: bytes) -> str:
    if not blob:
        return ""
    try:
        text = blob.decode("utf-8")
        printable = sum(1 for c in text if c.isprintable() or c.isspace())
        if printable / max(len(text), 1) >= 0.85:
            return text
    except UnicodeDecodeError:
        pass
    runs: list[str] = []
    buf: list[str] = []
    for byte in blob:
        if 32 <= byte <= 126 or byte in {9, 10, 13}:
            buf.append(chr(byte))
            continue
        if len(buf) >= 12:
            runs.append("".join(buf))
        buf = []
    if len(buf) >= 12:
        runs.append("".join(buf))
    return "\n".join(runs)


def ingest_doc(settings: Settings, blob: bytes, filename: str) -> list[str]:
    reasons = scan_bytes(settings, blob, filename=filename, kind="rag_doc")
    if reasons:
        raise ScanFailed(reasons[0], code="SCAN_FAILED")
    return chunk_text(_readable_text(blob))


def _caps(settings: Settings, plan: str) -> tuple[int, int]:
    if plan == "trial":
        return int(settings.INTERVIEWER_TRIAL_TURNS or 8), int(settings.INTERVIEWER_TRIAL_DAYS or 14)
    return int(settings.INTERVIEWER_PAID_TURNS or 500), 365


def grant_license(
    db: Session,
    settings: Settings,
    user_id: str,
    listing: Listing,
    *,
    plan: str,
    order_id: str | None = None,
) -> InterviewerLicense:
    now = datetime.now(timezone.utc)
    cap, days = _caps(settings, plan)
    row = (
        db.query(InterviewerLicense)
        .filter(InterviewerLicense.user_id == user_id, InterviewerLicense.listing_id == listing.id)
        .one_or_none()
    )
    expires = now + timedelta(days=days)
    if row is None:
        row = InterviewerLicense(
            user_id=user_id,
            listing_id=listing.id,
            order_id=order_id,
            plan=plan,
            status="active",
            turns_used=0,
            turns_cap=cap,
            expires_at=expires,
        )
        db.add(row)
        db.flush()
        return row
    if plan in {"purchased", "hired", "seller"}:
        if not (plan == "seller" and row.plan in {"purchased", "hired"}):
            row.plan = plan
        row.status = "active"
        row.turns_cap = max(row.turns_cap, cap)
        row.expires_at = expires
        row.order_id = order_id or row.order_id
    return row


def active_license(db: Session, user_id: str, listing: Listing) -> InterviewerLicense | None:
    now = datetime.now(timezone.utc)
    row = (
        db.query(InterviewerLicense)
        .filter(InterviewerLicense.user_id == user_id, InterviewerLicense.listing_id == listing.id)
        .one_or_none()
    )
    if row is None:
        return None
    exp = row.expires_at
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if row.status != "active" or (exp is not None and exp <= now):
        row.status = "expired"
        return None
    if int(row.turns_used or 0) >= int(row.turns_cap or 0):
        row.status = "exhausted"
        return None
    return row


def access_license(db: Session, settings: Settings, user: User, listing: Listing) -> InterviewerLicense | None:
    live = active_license(db, user.id, listing)
    if live is not None:
        return live
    if listing.seller_id == user.id:
        return grant_license(db, settings, user.id, listing, plan="seller")
    return None


def listing_for_agent(db: Session, slug: str = "ai-interviewer") -> Listing | None:
    return db.query(Listing).filter(Listing.slug == slug, Listing.type == "agent", Listing.status == "live").one_or_none()


def profile_block(db: Session, user: User, job: Job | None, cv_text: str = "") -> str:
    tags: set[str] = set()
    rows = db.query(Listing).filter(Listing.seller_id == user.id).all()
    for listing in rows:
        tags.update((t or "").strip().lower() for t in (listing.tags or []) if t)
        if listing.category:
            tags.add(listing.category.lower())
        if listing.platform:
            tags.add(listing.platform.lower())
    if job is not None:
        fit, why = applicant_rank(user, job, tags, cv_text=cv_text)
    else:
        fit, why = 0, "No attached role"
    excerpt = redact(cv_text or "")[:1200]
    skills = ", ".join(sorted(tags)[:12]) or "(none from marketplace listings)"
    lines = [
        f"Name: {user.name}",
        f"Trust: {user.trust_score}",
        f"Sales: {user.sales_count}",
        f"Rating: {user.rating}",
        f"Skills: {skills}",
        f"Fit preview: {fit} ({why})",
        f"CV_EXCERPT: {excerpt or '(none)'}",
    ]
    if job is not None:
        lines.append(f"Role: {job.title} at {job.company}")
        lines.append(f"Required skills: {', '.join(job.skills or [])}")
    return "\n".join(lines)


def _parse_agent(raw: str) -> dict | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = _JSON.search(text)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    return data


def _fallback_question(session: InterviewerSession) -> str:
    idx = min(int(session.question_count or 0), len(_FALLBACK) - 1)
    return _FALLBACK[idx]


def _heuristic_scorecard(session: InterviewerSession, turns: list[InterviewerTurn], profile: str) -> tuple[int, list[dict], str]:
    answers = [t.body for t in turns if t.role == "candidate"]
    blob = " ".join(answers).lower()
    score = 55
    card = [{"label": "AI disclosure", "status": "Passed", "detail": "Candidate was told this is an AI interviewer."}]
    if "automat" in blob or "flow" in blob or "n8n" in blob:
        score += 15
        card.append({"label": "Automation evidence", "status": "Passed"})
    else:
        score -= 10
        card.append({"label": "Automation evidence", "status": "Missed"})
    if "test" in blob or "sandbox" in blob:
        score += 10
        card.append({"label": "Testing", "status": "Passed"})
    else:
        card.append({"label": "Testing", "status": "Missed"})
    if "secret" in blob or "redact" in blob or "vault" in blob:
        score += 8
        card.append({"label": "Secrets handling", "status": "Passed"})
    if len(blob) < 80:
        score -= 15
        card.append({"label": "Answer depth", "status": "Missed"})
    score = max(1, min(99, score))
    summary = "Heuristic scorecard used because the model was unavailable. A human must review the transcript."
    return score, card, summary


def opening_message() -> str:
    return _DISCLOSE + " " + _FALLBACK[0]


def next_agent_turn(
    db: Session,
    settings: Settings,
    session: InterviewerSession,
    *,
    candidate: User,
    job: Job | None,
    cv_text: str,
    docs: list[InterviewerDoc],
    turns: list[InterviewerTurn],
    max_questions: int,
    playbook: str = "",
) -> tuple[str, bool, int, list, str | None]:
    chat = "\n".join(f"{row.role}: {redact(row.body)[:500]}" for row in turns[-12:])
    query = " ".join(t.body for t in turns[-4:] if t.body) or (job.title if job else "developer interview")
    docs_block = retrieve_docs(docs, query)
    profile = profile_block(db, candidate, job, cv_text)
    asked = int(session.question_count or 0)
    if asked >= max_questions:
        score, card, summary = _heuristic_scorecard(session, turns, profile)
        return "", True, score, card, summary
    system = _SYSTEM
    book = redact((playbook or "").strip())[:2500]
    if book:
        system += (
            "\nFollow SELLER_PLAYBOOK for topics and rubric. Still disclose you are an AI. "
            "Never impersonate a human.\nSELLER_PLAYBOOK\n" + book
        )
    user_block = (
        f"PROFILE\n{profile}\n\nCOMPANY_DOCS\n{docs_block}\n\n"
        f"CHAT\n{chat or '(start)'}\n\nMAX_QUESTIONS={max_questions} ASKED={asked}"
    )
    parsed = None
    if settings.deepseek_enabled():
        try:
            raw = complete(
                settings,
                system=system,
                user=user_block,
                max_tokens=400,
                user_limit=4500,
                model=(settings.DEEPSEEK_MODEL_FAST or settings.DEEPSEEK_MODEL or "").strip() or None,
                timeout=8.0,
                retries=1,
            )
            parsed = _parse_agent(raw)
        except LlmError:
            parsed = None
    if parsed and parsed.get("done") is True:
        score = int(parsed.get("score") or 0)
        score = max(1, min(99, score))
        card = parsed.get("scorecard") if isinstance(parsed.get("scorecard"), list) else []
        summary = str(parsed.get("summary") or "Interview complete. Human review required.")[:800]
        return "", True, score, card, summary
    if parsed and parsed.get("question"):
        question = redact(str(parsed.get("question")))[:500]
        return question, False, 0, [], None
    return _fallback_question(session), False, 0, [], None


def consume_turn(license_row: InterviewerLicense) -> None:
    license_row.turns_used = int(license_row.turns_used or 0) + 1
    if license_row.turns_used >= int(license_row.turns_cap or 0):
        license_row.status = "exhausted"


def cv_excerpt(settings: Settings, application: JobApplication | None) -> str:
    if application is None or not application.cv_key:
        return ""
    try:
        blob = read_bytes(settings, application.cv_key, limit=200_000)
    except Exception:
        return ""
    return redact(blob.decode("utf-8", errors="ignore"))[:2000]


def write_application_score(
    application: JobApplication | None,
    session: InterviewerSession,
    *,
    score: int,
    summary: str | None,
) -> None:
    if application is None:
        return
    application.interview_score = max(0, min(99, int(score or 0)))
    application.interview_summary = (summary or "")[:800] or None
    application.interview_session_id = session.public_id
    if application.status in {"applied", "in_review"}:
        application.status = "interview"
