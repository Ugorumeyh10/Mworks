from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.db import get_db
from app.deps import require_admin, require_user
from app.fingerprint import sha256_hex
from app.models import Listing, ScanVerdict, TheftClaim, User
from app.rate_limit import rate_limit
from app.scan import AUTH_KINDS, SELLER_KINDS, ScanFailed, scan_bytes
from app.schemas import ScanCommitIn, ScanCommitOut, TheftClaimIn, TheftClaimOut, TheftResolveIn
from app.storage import object_exists, owned_object_key, read_bytes

router = APIRouter(prefix="/v1", tags=["trust"])


def _claim_out(row: TheftClaim) -> TheftClaimOut:
    listing = row.listing
    return TheftClaimOut(
        id=row.public_id,
        listingId=listing.slug if listing else "",
        listingTitle=listing.title if listing else "Listing",
        status=row.status,
        reason=row.reason,
        resolution=row.resolution,
    )


@router.post("/uploads/commit", response_model=ScanCommitOut)
def commit_upload(
    body: ScanCommitIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    try:
        key = owned_object_key(user.public_id, body.object_key, kinds=SELLER_KINDS | AUTH_KINDS)
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "That file upload is not valid.", "code": "BAD_FILE"})
    if not object_exists(settings, key):
        raise HTTPException(status_code=400, detail={"error": "Upload the file before scanning.", "code": "FILE_REQUIRED"})
    existing = db.query(ScanVerdict).filter(ScanVerdict.object_key == key).one_or_none()
    if existing and existing.status == "clean":
        return ScanCommitOut(object_key=key, sha256=existing.sha256, status="clean", reasons=[])
    blob = read_bytes(settings, key, limit=settings.UPLOAD_MAX_BYTES)
    kind = key.split("/", 1)[0]
    try:
        reasons = scan_bytes(settings, blob, filename=key.rsplit("/", 1)[-1], kind=kind)
    except ScanFailed as exc:
        raise HTTPException(status_code=400, detail={"error": str(exc) or "Scan failed.", "code": getattr(exc, "code", "SCAN_FAILED")})
    digest = sha256_hex(blob)
    status = "clean" if not reasons else "blocked"
    row = existing or ScanVerdict(object_key=key, user_id=user.id, sha256=digest)
    row.sha256 = digest
    row.status = status
    row.reasons = reasons
    if existing is None:
        db.add(row)
    db.commit()
    if status != "clean":
        raise HTTPException(status_code=400, detail={"error": reasons[0], "code": "SCAN_FAILED"})
    return ScanCommitOut(object_key=key, sha256=digest, status="clean", reasons=[])


@router.post("/listings/{slug}/theft-claim", response_model=TheftClaimOut, status_code=201)
def file_claim(
    slug: str,
    body: TheftClaimIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    listing = db.query(Listing).filter(Listing.slug == slug).one_or_none()
    if listing is None or listing.status not in {"live", "pending_review", "rejected"}:
        raise HTTPException(status_code=404, detail={"error": "Listing not found.", "code": "NOT_FOUND"})
    if listing.seller_id == user.id and listing.status != "rejected" and listing.status != "pending_review":
        raise HTTPException(status_code=400, detail={"error": "You cannot claim theft on your own live listing.", "code": "BAD_REQUEST"})
    row = TheftClaim(listing_id=listing.id, claimant_id=user.id, reason=body.reason.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    row.listing = listing
    return _claim_out(row)


@router.get("/admin/theft-claims", response_model=list[TheftClaimOut])
def list_claims(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_admin),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    rows = (
        db.query(TheftClaim)
        .options(joinedload(TheftClaim.listing))
        .order_by(TheftClaim.created_at.desc())
        .limit(100)
        .all()
    )
    return [_claim_out(r) for r in rows]


@router.post("/admin/theft-claims/{public_id}/resolve", response_model=TheftClaimOut)
def resolve_claim(
    public_id: str,
    body: TheftResolveIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_admin),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = (
        db.query(TheftClaim)
        .options(joinedload(TheftClaim.listing))
        .filter(TheftClaim.public_id == public_id)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "Claim not found.", "code": "NOT_FOUND"})
    row.status = body.status
    row.resolution = body.resolution.strip()
    listing = row.listing
    if listing is not None:
        if body.status == "upheld":
            listing.status = "rejected"
            listing.verified = False
        elif listing.status == "pending_review":
            listing.status = "live"
            listing.verified = True
    db.commit()
    return _claim_out(row)
