from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.db import get_db
from app.deps import optional_user
from app.fmt import avatar as av
from app.models import FeedEvent, Job, Listing, User
from app.rank import feed_score, listing_quality
from app.rate_limit import rate_limit
from app.schemas import FeedEventIn, FeedPostOut

router = APIRouter(prefix="/v1/feed", tags=["feed"])

TRAINING = [
    {
        "id": "training:semicolon-12",
        "type": "training",
        "title": "Cohort 12 Showcase - Semicolon Africa",
        "caption": "Top RPA graduates this cohort. Each carries a verified trust score from marketplace projects.",
        "href": "/partners/semicolon",
        "seller": {"name": "Semicolon Africa", "avatar": "SA", "trust": 90},
        "likes": 512,
        "comments": 61,
    }
]


def _listing_post(row: Listing, clicks: int, hides: int) -> FeedPostOut:
    quality, why = listing_quality(row)
    seller = row.seller
    return FeedPostOut(
        id=f"listing:{row.slug}",
        type=row.type,
        title=row.title,
        caption=row.blurb,
        href=f"/listing/{row.slug}",
        priceValue=row.price_value,
        verified=row.verified,
        qualityScore=quality,
        rankReason=why,
        score=round(feed_score(row, clicks, hides), 6),
        seller={"name": seller.name, "avatar": av(seller.name), "trust": seller.trust_score} if seller else None,
        likes=clicks,
        comments=row.review_count,
        meta=row.category,
    )


@router.get("", response_model=list[FeedPostOut])
def list_feed(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    tab: str = Query(default="for_you", max_length=24),
    user: User | None = Depends(optional_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    tab = (tab or "for_you").lower()
    if tab not in {"for_you", "jobs", "training", "following"}:
        raise HTTPException(status_code=400, detail={"error": "Unknown feed tab.", "code": "BAD_REQUEST"})
    events = db.query(FeedEvent).all()
    clicks: dict[str, int] = {}
    hides: dict[str, int] = {}
    for ev in events:
        if ev.kind == "hide":
            hides[ev.post_key] = hides.get(ev.post_key, 0) + 1
        else:
            clicks[ev.post_key] = clicks.get(ev.post_key, 0) + 1

    if tab == "training":
        return [FeedPostOut.model_validate(row) for row in TRAINING]
    if tab == "jobs":
        jobs = db.query(Job).filter(Job.status == "live").order_by(Job.created_at.desc()).limit(40).all()
        return [
            FeedPostOut(
                id=f"job:{job.slug}",
                type="job",
                title=job.title,
                caption=job.description[:240],
                href=f"/jobs/board/{job.slug}",
                meta=f"{job.location} · {job.salary}",
                likes=clicks.get(f"job:{job.slug}", 0),
                comments=job.applicant_count,
                score=float(job.min_trust),
            )
            for job in jobs
        ]
    listings = (
        db.query(Listing)
        .options(joinedload(Listing.seller))
        .filter(Listing.status == "live")
        .limit(80)
        .all()
    )
    posts = [_listing_post(row, clicks.get(f"listing:{row.slug}", 0), hides.get(f"listing:{row.slug}", 0)) for row in listings]
    posts.sort(key=lambda p: p.score, reverse=True)
    if tab == "following" and user is not None:
        posts = [p for p in posts if p.seller and p.seller.trust >= 80]
    return posts[:50]


@router.post("/events", status_code=201)
def record_event(
    body: FeedEventIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(optional_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    key = (body.post_key or "").strip()[:160]
    if not key or ":" not in key:
        raise HTTPException(status_code=400, detail={"error": "Invalid post.", "code": "BAD_REQUEST"})
    db.add(FeedEvent(user_id=user.id if user else None, post_key=key, kind=body.kind))
    db.commit()
    return {"status": "ok"}
