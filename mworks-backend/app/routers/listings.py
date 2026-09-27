from datetime import datetime, timezone
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.db import get_db
from app.deps import optional_user, require_user
from app.models import Listing, User
from app.rank import listing_quality
from app.rate_limit import rate_limit
from app.schemas import ListingCreateIn, ListingOut, SellerCard
from app.storage import object_exists, owned_object_key
from app.verify import verify_listing

router = APIRouter(prefix="/v1/listings", tags=["listings"])

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(title: str) -> str:
    base = _SLUG_RE.sub("-", title.lower()).strip("-")[:48] or "listing"
    return f"{base}-{uuid.uuid4().hex[:6]}"


def _avatar(name: str) -> str:
    return (name.strip()[:1] or "?").upper()


def to_out(row: Listing, db: Session | None = None) -> ListingOut:
    seller = row.seller
    year = str(seller.created_at.year) if seller.created_at else "2026"
    score, why = listing_quality(row, db)
    return ListingOut(
        id=row.slug,
        type=row.type,
        title=row.title,
        blurb=row.blurb,
        description=row.description,
        category=row.category,
        platform=row.platform,
        models=row.models or [],
        promptCount=row.prompt_count,
        seller=SellerCard(
            name=seller.name,
            avatar=_avatar(seller.name),
            trust=seller.trust_score,
            sales=seller.sales_count,
            rating=float(seller.rating or 0),
            reviews=seller.review_count,
            since=year,
        ),
        priceValue=row.price_value,
        rating=float(row.rating or 0),
        reviewCount=row.review_count,
        verified=row.verified,
        verifyType=row.verify_type,
        delivery=row.delivery,
        tags=row.tags or [],
        metrics=row.metrics or [],
        verificationLog=row.verification_log or [],
        reviews=row.reviews or [],
        license=row.license,
        status=row.status,
        hasFile=bool(row.object_key),
        qualityScore=score,
        rankReason=why,
    )


@router.get("", response_model=list[ListingOut])
def list_listings(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    type: str | None = Query(default=None, max_length=24),
    q: str | None = Query(default=None, max_length=80),
    category: str | None = Query(default=None, max_length=64),
    verified: bool | None = None,
    min_rating: float | None = Query(default=None, ge=0, le=5),
    sort: str | None = Query(default="quality", max_length=16),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    query = db.query(Listing).options(joinedload(Listing.seller)).filter(Listing.status == "live")
    if type and type != "all":
        query = query.filter(Listing.type == type)
    if category:
        query = query.filter(Listing.category == category)
    if verified:
        query = query.filter(Listing.verified.is_(True))
    if min_rating:
        query = query.filter(Listing.rating >= min_rating)
    if q:
        needle = f"%{q.strip().lower()}%"
        query = query.filter(or_(Listing.title.ilike(needle), Listing.blurb.ilike(needle)))
    rows = query.limit(100).all()
    if sort == "newest":
        rows.sort(key=lambda r: r.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return [to_out(r, db) for r in rows]
    scored = [(listing_quality(r, db)[0], r) for r in rows]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [to_out(r, db) for _, r in scored]


@router.get("/{slug}", response_model=ListingOut)
def get_listing(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(optional_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = (
        db.query(Listing)
        .options(joinedload(Listing.seller))
        .filter(Listing.slug == slug)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "Listing not found.", "code": "NOT_FOUND"})
    if row.status == "live":
        return to_out(row, db)
    if user is not None and row.seller_id == user.id:
        return to_out(row, db)
    raise HTTPException(status_code=404, detail={"error": "Listing not found.", "code": "NOT_FOUND"})


@router.post("", response_model=ListingOut, status_code=201)
def create_listing(
    body: ListingCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    if user.role not in {"seller", "both"}:
        raise HTTPException(status_code=403, detail={"error": "Seller role required.", "code": "FORBIDDEN"})
    verify_type = {
        "automation": "sandbox",
        "source": "sandbox",
        "prompt": "originality",
        "document": "originality",
        "agent": "originality",
    }[body.type]
    license_val = body.license
    if body.type == "document":
        license_val = license_val or "template"
    kinds = {"document"} if body.type == "document" else {"package"} if body.type == "automation" else {"document", "package"}
    object_key = None
    if body.type in {"document", "automation"}:
        if not (body.object_key or "").strip():
            raise HTTPException(status_code=400, detail={"error": "Upload the pack file before submitting.", "code": "FILE_REQUIRED"})
        try:
            object_key = owned_object_key(user.public_id, body.object_key, kinds=kinds)
        except ValueError:
            raise HTTPException(status_code=400, detail={"error": "That file upload is not valid.", "code": "BAD_FILE"})
        if not object_exists(settings, object_key):
            raise HTTPException(status_code=400, detail={"error": "Upload the pack file before submitting.", "code": "FILE_REQUIRED"})
    elif body.object_key:
        try:
            object_key = owned_object_key(user.public_id, body.object_key, kinds=kinds)
        except ValueError:
            raise HTTPException(status_code=400, detail={"error": "That file upload is not valid.", "code": "BAD_FILE"})
    prompt_body = None
    if body.type in {"prompt", "agent"}:
        text = (body.prompt_text or "").strip()
        if len(text) < 20:
            raise HTTPException(status_code=400, detail={"error": "Paste the prompt text before submitting.", "code": "PROMPT_REQUIRED"})
        prompt_body = text
    row = Listing(
        slug=_slugify(body.title),
        seller_id=user.id,
        type=body.type,
        title=body.title.strip(),
        blurb=body.blurb.strip(),
        description=body.description.strip(),
        category=body.category,
        platform=body.platform,
        models=body.models,
        prompt_count=body.prompt_count,
        price_value=body.price_value,
        verified=False,
        verify_type=verify_type,
        delivery="Instant download" if body.type in {"prompt", "document", "agent"} else "1-3 days setup",
        tags=body.tags,
        metrics=body.metrics,
        verification_log=[{"label": "Submitted", "status": "Queued"}],
        reviews=[],
        license=license_val,
        object_key=object_key,
        prompt_body=prompt_body,
        status="in_review",
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    row.seller = user
    return to_out(row, db)


@router.post("/{slug}/publish", response_model=ListingOut)
def publish_listing(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = (
        db.query(Listing)
        .options(joinedload(Listing.seller))
        .filter(Listing.slug == slug, Listing.seller_id == user.id)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "Listing not found.", "code": "NOT_FOUND"})
    if row.status == "live" and row.verified:
        return to_out(row, db)
    if row.status not in {"in_review", "draft", "rejected"}:
        raise HTTPException(status_code=400, detail={"error": "This listing cannot be verified.", "code": "BAD_REQUEST"})
    verify_listing(db, settings, row)
    db.commit()
    row = (
        db.query(Listing)
        .options(joinedload(Listing.seller))
        .filter(Listing.id == row.id)
        .one()
    )
    return to_out(row, db)


me_router = APIRouter(prefix="/v1/me", tags=["me"])


@me_router.get("/listings", response_model=list[ListingOut])
def my_listings(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    if user.role not in {"seller", "both"}:
        raise HTTPException(status_code=403, detail={"error": "Seller role required.", "code": "FORBIDDEN"})
    rows = (
        db.query(Listing)
        .options(joinedload(Listing.seller))
        .filter(Listing.seller_id == user.id)
        .order_by(Listing.created_at.desc())
        .limit(100)
        .all()
    )
    return [to_out(r, db) for r in rows]

