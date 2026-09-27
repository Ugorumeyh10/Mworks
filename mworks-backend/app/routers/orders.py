from datetime import datetime, timezone
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.db import get_db
from app.deps import require_user
from app.models import Listing, Order, User
from app.payments import (
    PaymentError,
    initialize_payment,
    verify_paystack_reference,
    verify_paystack_signature,
)
from app.rate_limit import rate_limit
from app.schemas import CheckoutIn, DeliverIn, DownloadOut, LocalPayIn, OrderOut, PartyCard, PresignIn, PresignOut, PromptOut
from app.interviewer import grant_license
from app.scan import AUTH_KINDS, SELLER_KINDS, ScanFailed
from app.storage import filename_from_key, object_exists, owned_object_key, presign_get, presign_put, safe_key, validate_upload

router = APIRouter(prefix="/v1", tags=["commerce"])

COMMISSION = {"automation": 0.15, "prompt": 0.10, "document": 0.10, "source": 0.15, "agent": 0.15}


def _ref() -> str:
    return "MW-" + uuid.uuid4().hex[:8].upper()


def _now_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _placed(row: Order) -> str:
    if not row.created_at:
        return ""
    stamp = row.created_at
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.strftime("%b %d, %Y").replace(" 0", " ")


def _avatar(name: str) -> str:
    return (name.strip()[:1] or "?").upper()


def _append(row: Order, label: str) -> None:
    trail = list(row.timeline or [])
    trail.append({"t": _now_label(), "label": label})
    row.timeline = trail


def _pack_key(row: Order, listing: Listing | None) -> str | None:
    if row.delivery_key:
        return row.delivery_key
    if listing is not None and listing.object_key:
        return listing.object_key
    return None


def _to_out(row: Order, listing: Listing, user: User, *, payment_url: str | None = None) -> OrderOut:
    if user.id == row.buyer_id:
        other = listing.seller if listing is not None else None
        role = "buyer"
    else:
        other = None
        role = "seller"
    if role == "seller":
        # buyer name is loaded by caller when needed via listing only; seller view uses buyer from row
        other_name = getattr(row, "_buyer_name", None)
        other_avatar = _avatar(other_name or "B")
        party = PartyCard(name=other_name or "Buyer", avatar=other_avatar) if other_name else None
    else:
        party = PartyCard(name=other.name, avatar=_avatar(other.name)) if other is not None else None
    return OrderOut(
        id=row.public_ref,
        listingId=listing.slug if listing else "",
        title=listing.title if listing else "Listing",
        type=listing.type if listing else "automation",
        kind=row.kind,
        amount=row.amount,
        state=row.state,
        brief=row.brief,
        timeline=row.timeline or [],
        counterparty=party,
        placedAt=_placed(row),
        paymentUrl=payment_url,
        paymentProvider=row.payment_provider,
        role=role,
        hasDownload=bool(
            role == "buyer"
            and _pack_key(row, listing)
            and row.state in {"delivered", "completed"}
        ),
        hasPrompt=bool(
            role == "buyer"
            and listing is not None
            and (listing.prompt_body or "").strip()
            and row.state in {"delivered", "completed"}
        ),
    )


def _mark_paid(db: Session, settings: Settings, order: Order, listing: Listing) -> None:
    if listing.type in {"prompt", "document", "agent"} and order.kind == "purchase":
        order.state = "delivered"
        _append(order, "Payment captured and held in escrow")
        _append(order, "Instant download unlocked" if listing.type != "agent" else "Hosted interviewer and playbook unlocked")
    else:
        order.state = "funds_held"
        _append(order, "Payment captured and held in escrow")
    if listing.type == "agent":
        plan = "hired" if order.kind == "hire" else "purchased"
        grant_license(db, settings, order.buyer_id, listing, plan=plan, order_id=order.id)


@router.post("/uploads/presign", response_model=PresignOut)
def presign(
    body: PresignIn,
    request: Request,
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    if body.kind in SELLER_KINDS and user.role not in {"seller", "both"}:
        raise HTTPException(status_code=403, detail={"error": "Seller role required.", "code": "FORBIDDEN"})
    if body.kind in {"blog_image", "blog_video"} and not user.is_admin:
        raise HTTPException(status_code=403, detail={"error": "Admin role required.", "code": "FORBIDDEN"})
    if body.kind not in SELLER_KINDS | AUTH_KINDS:
        raise HTTPException(status_code=400, detail={"error": "That file type is not allowed.", "code": "BAD_FILE"})
    try:
        validate_upload(body.filename, body.content_type, body.kind, body.size_bytes)
    except (ValueError, ScanFailed):
        raise HTTPException(status_code=400, detail={"error": "That file type is not allowed.", "code": "BAD_FILE"})
    key = safe_key(f"{body.kind}/{user.public_id}", f"{uuid.uuid4().hex[:8]}-{body.filename}")
    try:
        url = presign_put(settings, key=key, content_type=body.content_type)
    except Exception:
        raise HTTPException(status_code=503, detail={"error": "Uploads are temporarily unavailable.", "code": "STORAGE_DOWN"})
    return PresignOut(object_key=key, put_url=url, headers={"Content-Type": body.content_type})


@router.post("/listings/{slug}/checkout", response_model=OrderOut, status_code=201)
def checkout(
    slug: str,
    body: CheckoutIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    listing = (
        db.query(Listing)
        .options(joinedload(Listing.seller))
        .filter(Listing.slug == slug, Listing.status == "live")
        .one_or_none()
    )
    if listing is None:
        raise HTTPException(status_code=404, detail={"error": "Listing not found.", "code": "NOT_FOUND"})
    if listing.seller_id == user.id:
        raise HTTPException(status_code=400, detail={"error": "You cannot buy your own listing.", "code": "BAD_REQUEST"})

    amount = listing.price_value
    if body.kind == "hire":
        amount = body.budget or listing.price_value
        if not (body.brief or "").strip():
            raise HTTPException(status_code=400, detail={"error": "A brief is required for hire.", "code": "VALIDATION_ERROR"})
    if body.kind == "revise":
        from app.schemas import REVISE_MAX_NAIRA

        if listing.type != "document":
            raise HTTPException(status_code=400, detail={"error": "Revise is only available for document packs.", "code": "BAD_REQUEST"})
        amount = body.budget or min(listing.price_value, REVISE_MAX_NAIRA)
        if amount > REVISE_MAX_NAIRA:
            raise HTTPException(
                status_code=400,
                detail={"error": "Revise orders are capped at 25000 naira.", "code": "REVISE_CAP"},
            )
        if not (body.brief or "").strip():
            raise HTTPException(status_code=400, detail={"error": "A brief is required for a revise order.", "code": "VALIDATION_ERROR"})

    public_ref = _ref()
    order = Order(
        public_ref=public_ref,
        listing_id=listing.id,
        buyer_id=user.id,
        seller_id=listing.seller_id,
        kind=body.kind,
        amount=amount,
        state="pending_payment",
        brief=(body.brief or "").strip() or None,
        timeline=[{"t": _now_label(), "label": "Order created. Awaiting payment."}],
        payment_ref=public_ref,
        payment_provider=None,
    )
    db.add(order)
    db.flush()
    try:
        pay = initialize_payment(settings, email=user.email, amount_naira=amount, reference=public_ref)
    except PaymentError:
        db.rollback()
        raise HTTPException(status_code=503, detail={"error": "Payments are temporarily unavailable.", "code": "PAYMENTS_DOWN"})
    order.payment_provider = pay["provider"]
    db.commit()
    db.refresh(order)
    return _to_out(order, listing, user, payment_url=pay["authorization_url"])


def _load_order(db: Session, ref: str) -> tuple[Order | None, Listing | None]:
    row = db.query(Order).filter(Order.public_ref == ref).one_or_none()
    if row is None:
        return None, None
    listing = (
        db.query(Listing)
        .options(joinedload(Listing.seller))
        .filter(Listing.id == row.listing_id)
        .one_or_none()
    )
    return row, listing


@router.get("/orders", response_model=list[OrderOut])
def my_orders(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
    role: str = Query(default="buying", max_length=16),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    if role not in {"buying", "selling"}:
        raise HTTPException(status_code=422, detail={"error": "The request payload is invalid.", "code": "VALIDATION_ERROR"})
    if role == "selling":
        q = db.query(Order).filter(Order.seller_id == user.id)
    else:
        q = db.query(Order).filter(Order.buyer_id == user.id)
    rows = q.order_by(Order.created_at.desc()).limit(50).all()
    listing_ids = {r.listing_id for r in rows}
    listings = {l.id: l for l in db.query(Listing).options(joinedload(Listing.seller)).filter(Listing.id.in_(listing_ids)).all()} if listing_ids else {}
    buyer_ids = {r.buyer_id for r in rows} if role == "selling" else set()
    buyers = {u.id: u for u in db.query(User).filter(User.id.in_(buyer_ids)).all()} if buyer_ids else {}
    out = []
    for r in rows:
        listing = listings.get(r.listing_id)
        if role == "selling":
            buyer = buyers.get(r.buyer_id)
            r._buyer_name = buyer.name if buyer else "Buyer"
        out.append(_to_out(r, listing, user))
    return out


@router.get("/orders/{ref}", response_model=OrderOut)
def get_order(
    ref: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row, listing = _load_order(db, ref)
    if row is None or (row.buyer_id != user.id and row.seller_id != user.id):
        raise HTTPException(status_code=404, detail={"error": "Order not found.", "code": "NOT_FOUND"})
    if row.seller_id == user.id:
        buyer = db.query(User).filter(User.id == row.buyer_id).one_or_none()
        row._buyer_name = buyer.name if buyer else "Buyer"
    pay_url = None
    if row.state == "pending_payment" and row.payment_provider == "local_test":
        pay_url = f"{settings.APP_PUBLIC_URL.rstrip('/')}/checkout/pay/{row.public_ref}"
    return _to_out(row, listing, user, payment_url=pay_url)


@router.post("/payments/local/confirm", response_model=OrderOut)
def local_confirm(
    body: LocalPayIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    if not settings.local_payments_allowed() or settings.paystack_enabled():
        raise HTTPException(status_code=404, detail={"error": "Order not found.", "code": "NOT_FOUND"})
    row, listing = _load_order(db, body.reference)
    if row is None or row.buyer_id != user.id:
        raise HTTPException(status_code=404, detail={"error": "Order not found.", "code": "NOT_FOUND"})
    if row.payment_provider != "local_test":
        raise HTTPException(status_code=400, detail={"error": "This order cannot be paid that way.", "code": "BAD_REQUEST"})
    if row.state != "pending_payment":
        return _to_out(row, listing, user)
    _mark_paid(db, settings, row, listing)
    db.commit()
    db.refresh(row)
    return _to_out(row, listing, user)


@router.post("/payments/verify/{ref}", response_model=OrderOut)
def verify_payment(
    ref: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row, listing = _load_order(db, ref)
    if row is None or (row.buyer_id != user.id and row.seller_id != user.id):
        raise HTTPException(status_code=404, detail={"error": "Order not found.", "code": "NOT_FOUND"})
    if row.state != "pending_payment":
        if row.seller_id == user.id:
            buyer = db.query(User).filter(User.id == row.buyer_id).one_or_none()
            row._buyer_name = buyer.name if buyer else "Buyer"
        return _to_out(row, listing, user)
    if row.buyer_id != user.id:
        raise HTTPException(status_code=403, detail={"error": "Forbidden.", "code": "FORBIDDEN"})
    if row.payment_provider == "paystack":
        if not verify_paystack_reference(settings, row.payment_ref or row.public_ref):
            raise HTTPException(status_code=400, detail={"error": "Payment is not complete.", "code": "PAYMENT_PENDING"})
        _mark_paid(db, settings, row, listing)
        db.commit()
        db.refresh(row)
        return _to_out(row, listing, user)
    raise HTTPException(status_code=400, detail={"error": "Payment is not complete.", "code": "PAYMENT_PENDING"})


@router.post("/payments/paystack/webhook")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    raw = await request.body()
    sig = request.headers.get("x-paystack-signature", "")
    if not settings.paystack_enabled() or not verify_paystack_signature(settings, raw, sig):
        raise HTTPException(status_code=401, detail={"error": "Authentication required.", "code": "UNAUTHENTICATED"})
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail={"error": "Invalid request.", "code": "BAD_REQUEST"})
    event = payload.get("event")
    data = payload.get("data") or {}
    ref = data.get("reference")
    if event != "charge.success" or not ref:
        return {"status": "ok"}
    row = db.query(Order).filter(Order.payment_ref == ref).one_or_none()
    if row is None or row.state != "pending_payment":
        return {"status": "ok"}
    listing = db.query(Listing).filter(Listing.id == row.listing_id).one_or_none()
    if listing is None:
        return {"status": "ok"}
    _mark_paid(db, settings, row, listing)
    db.commit()
    return {"status": "ok"}


@router.post("/orders/{ref}/deliver", response_model=OrderOut)
def mark_delivered(
    ref: str,
    body: DeliverIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row, listing = _load_order(db, ref)
    if row is None or row.seller_id != user.id:
        raise HTTPException(status_code=404, detail={"error": "Order not found.", "code": "NOT_FOUND"})
    if row.state != "funds_held":
        raise HTTPException(status_code=400, detail={"error": "This order cannot be marked delivered.", "code": "BAD_REQUEST"})
    try:
        key = owned_object_key(user.public_id, body.object_key, kinds={"delivery", "document", "package"})
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "Upload the delivery pack first.", "code": "BAD_FILE"})
    if not object_exists(settings, key):
        raise HTTPException(status_code=400, detail={"error": "Upload the delivery pack first.", "code": "FILE_REQUIRED"})
    row.delivery_key = key
    row.state = "delivered"
    _append(row, "Seller uploaded the delivered pack")
    db.commit()
    db.refresh(row)
    buyer = db.query(User).filter(User.id == row.buyer_id).one_or_none()
    row._buyer_name = buyer.name if buyer else "Buyer"
    return _to_out(row, listing, user)


@router.post("/orders/{ref}/confirm", response_model=OrderOut)
def confirm_delivery(
    ref: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row, listing = _load_order(db, ref)
    if row is None or row.buyer_id != user.id:
        raise HTTPException(status_code=404, detail={"error": "Order not found.", "code": "NOT_FOUND"})
    if row.state != "delivered":
        raise HTTPException(status_code=400, detail={"error": "Confirm is only available after delivery.", "code": "BAD_REQUEST"})
    row.state = "completed"
    _append(row, "You confirmed delivery. Funds released to the seller.")
    db.commit()
    db.refresh(row)
    return _to_out(row, listing, user)


@router.get("/orders/{ref}/download", response_model=DownloadOut)
def download_order(
    ref: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row, listing = _load_order(db, ref)
    if row is None or row.buyer_id != user.id:
        raise HTTPException(status_code=404, detail={"error": "Order not found.", "code": "NOT_FOUND"})
    if row.state not in {"delivered", "completed"}:
        raise HTTPException(status_code=400, detail={"error": "Download is not available yet.", "code": "NOT_READY"})
    key = _pack_key(row, listing)
    if not key:
        raise HTTPException(status_code=404, detail={"error": "Delivery is not available yet.", "code": "NOT_FOUND"})
    filename = filename_from_key(key)
    try:
        url = presign_get(settings, key=key, filename=filename)
    except Exception:
        raise HTTPException(status_code=503, detail={"error": "Downloads are temporarily unavailable.", "code": "STORAGE_DOWN"})
    return DownloadOut(url=url, filename=filename, expiresIn=120)


@router.get("/orders/{ref}/content", response_model=PromptOut)
def order_prompt(
    ref: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row, listing = _load_order(db, ref)
    if row is None or row.buyer_id != user.id:
        raise HTTPException(status_code=404, detail={"error": "Order not found.", "code": "NOT_FOUND"})
    if row.state not in {"delivered", "completed"}:
        raise HTTPException(status_code=400, detail={"error": "Delivery is not available yet.", "code": "NOT_READY"})
    text = (listing.prompt_body or "").strip() if listing is not None else ""
    if not text:
        raise HTTPException(status_code=404, detail={"error": "Delivery is not available yet.", "code": "NOT_FOUND"})
    return PromptOut(promptText=text)
