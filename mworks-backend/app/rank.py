from __future__ import annotations

from datetime import datetime, timezone
import math
import re

from sqlalchemy.orm import Session

from app.models import Job, Listing, Order, User

_SKILL = re.compile(r"\b(python|sql|uipath|power automate|n8n|zapier|ocr|llm|rpa|excel|pandas)\b", re.I)


def _age_days(stamp: datetime | None) -> float:
    if stamp is None:
        return 30.0
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - stamp).total_seconds() / 86400)


def listing_quality(row: Listing, db: Session | None = None) -> tuple[int, str]:
    seller = row.seller
    trust = int(getattr(seller, "trust_score", 50) or 50) if seller else 50
    sales = int(getattr(seller, "sales_count", 0) or 0) if seller else 0
    rating = float(row.rating or 0)
    metrics = [m for m in (row.metrics or []) if isinstance(m, dict) and m.get("label")]
    refunds = 0
    if db is not None:
        refunds = (
            db.query(Order)
            .filter(Order.listing_id == row.id, Order.state.in_(("refunded", "cancelled")))
            .count()
        )
    recency = math.exp(-_age_days(row.created_at) / 45.0)
    score = 12
    score += 28 if row.verified else 0
    score += min(18, len(metrics) * 6)
    score += min(16, sales)
    score += min(12, int(rating * 2.4))
    score += min(10, trust // 12)
    score += int(8 * recency)
    score -= min(24, refunds * 8)
    score = max(0, min(100, score))
    why = "Verified" if row.verified else "Unverified"
    if metrics:
        why += ", sandbox metrics"
    if sales:
        why += f", {sales} sales"
    if refunds:
        why += f", {refunds} refunds"
    return score, why


def feed_score(row: Listing, clicks: int, hides: int) -> float:
    quality, _ = listing_quality(row)
    seller = row.seller
    trust = (int(getattr(seller, "trust_score", 50) or 50) if seller else 50) / 100.0
    p_click = 0.05 + 0.4 * (min(clicks, 40) / 40.0)
    p_buy = 0.02 + 0.35 * (quality / 100.0)
    spam = 0.55 if not row.verified else min(0.4, hides / 20.0)
    return max(0.0, p_click * p_buy * trust * (1.0 - spam))


def applicant_rank(user: User, job: Job, tags: set[str], note: str = "", cv_text: str = "") -> tuple[int, str]:
    score = 40
    gap = user.trust_score - job.min_trust
    if gap >= 0:
        score += min(22, 8 + gap // 2)
    else:
        score -= min(18, abs(gap) // 2)
    score += min(12, int(user.sales_count or 0))
    score += min(8, int((user.rating or 0) * 1.6))
    skills = [(s or "").strip().lower() for s in (job.skills or []) if s]
    hay = tags | {m.group(0).lower() for m in _SKILL.finditer(cv_text or "")}
    hits = 0
    if skills:
        hits = sum(1 for s in skills if s in hay or any(s in t or t in s for t in hay))
        score += min(16, hits * 5)
    if (note or "").strip():
        score += 4
    score = max(1, min(99, score))
    bits = [f"Trust {user.trust_score}"]
    if user.sales_count:
        bits.append(f"{user.sales_count} sales")
    if hits:
        bits.append(f"{hits} skill hits")
    if cv_text:
        bits.append("CV used as extra signal")
    return score, "; ".join(bits)
