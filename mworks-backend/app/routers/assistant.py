from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.deps import require_user
from app.llm import answer_account
from app.models import AssistantMessage, JobApplication, Listing, Order, User
from app.rate_limit import rate_limit
from app.schemas import AssistantSendIn, AssistantTurnOut

router = APIRouter(prefix="/v1/assistant", tags=["assistant"])

_WELCOME = (
    "Hi - I only see your Mworks account: listings, orders, and job applications. "
    "Ask about a pack that is in review, an order in escrow, or an application."
)


def _turn(role: str, text: str) -> AssistantTurnOut:
    return AssistantTurnOut.model_validate({"from": "bot" if role == "bot" else "me", "text": text})


def _reply(db: Session, user: User, text: str) -> str:
    needle = (text or "").lower()
    listings = (
        db.query(Listing).filter(Listing.seller_id == user.id).order_by(Listing.created_at.desc()).limit(8).all()
    )
    orders = (
        db.query(Order)
        .filter((Order.buyer_id == user.id) | (Order.seller_id == user.id))
        .order_by(Order.created_at.desc())
        .limit(8)
        .all()
    )
    apps = (
        db.query(JobApplication)
        .filter(JobApplication.applicant_id == user.id)
        .order_by(JobApplication.created_at.desc())
        .limit(8)
        .all()
    )

    if any(w in needle for w in ("listing", "pack", "prompt", "verify", "sandbox", "publish")):
        if not listings:
            return "You do not have any listings yet. Create one from the seller workspace, then I can track verification."
        live = [r for r in listings if r.status == "live"]
        held = [r for r in listings if r.status in {"in_review", "draft"}]
        rejected = [r for r in listings if r.status == "rejected"]
        bits = [f"{len(live)} live", f"{len(held)} in review"]
        if rejected:
            bits.append(f"{len(rejected)} need changes")
        newest = listings[0]
        return (
            f"Your listings: {', '.join(bits)}. Newest is '{newest.title}' ({newest.status}"
            f"{', verified' if newest.verified else ''})."
        )
    if any(w in needle for w in ("order", "escrow", "deliver", "download", "hire", "payout")):
        if not orders:
            return "You have no orders yet. After checkout I can tell you whether a pack is unlocked or still in escrow."
        held = sum(1 for o in orders if o.state == "funds_held")
        delivered = sum(1 for o in orders if o.state == "delivered")
        newest = orders[0]
        return (
            f"You have {len(orders)} recent orders. {held} still in escrow, {delivered} waiting on buyer confirm. "
            f"Latest is {newest.public_ref} ({newest.state})."
        )
    if any(w in needle for w in ("job", "application", "apply", "agent", "role")):
        if not apps:
            return "You have not applied to any roles yet. Open the job board or let the Job Agent score matches."
        newest = apps[0]
        return (
            f"You have {len(apps)} applications on file. Latest is {newest.status} "
            f"({newest.via}, {newest.fit}% fit)."
        )
    return (
        f"I can check {len(listings)} listings, {len(orders)} orders, and {len(apps)} applications. "
        "Ask about a listing, an order, or a job application."
    )


@router.get("/messages", response_model=list[AssistantTurnOut])
def list_messages(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    rows = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.user_id == user.id)
        .order_by(AssistantMessage.created_at.asc())
        .limit(80)
        .all()
    )
    if not rows:
        welcome = AssistantMessage(user_id=user.id, role="bot", body=_WELCOME)
        db.add(welcome)
        db.commit()
        db.refresh(welcome)
        rows = [welcome]
    return [_turn(r.role, r.body) for r in rows]


@router.post("/messages", response_model=list[AssistantTurnOut], status_code=201)
def send_message(
    body: AssistantSendIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    text = body.text.strip()
    mine = AssistantMessage(user_id=user.id, role="me", body=text[:4000])
    db.add(mine)
    db.flush()
    reply = answer_account(db, settings, user, text) or _reply(db, user, text)
    bot = AssistantMessage(user_id=user.id, role="bot", body=reply[:4000])
    db.add(bot)
    db.commit()
    return [_turn("me", mine.body), _turn("bot", bot.body)]
