from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.deps import require_user
from app.fmt import ago, avatar
from app.models import ChatMessage, Conversation, User
from app.rate_limit import rate_limit
from app.schemas import ChatMessageOut, ChatSendIn, ConversationOut

router = APIRouter(prefix="/v1", tags=["messages"])


def _other(row: Conversation, user_id: str) -> str:
    return row.user_b_id if row.user_a_id == user_id else row.user_a_id


def _owned(db: Session, public_id: str, user: User) -> Conversation | None:
    row = db.query(Conversation).filter(Conversation.public_id == public_id).one_or_none()
    if row is None or user.id not in {row.user_a_id, row.user_b_id}:
        return None
    return row


def _last(db: Session, conversation_id: str) -> ChatMessage | None:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.desc())
        .first()
    )


def _conv_out(db: Session, row: Conversation, user: User) -> ConversationOut:
    other = db.query(User).filter(User.id == _other(row, user.id)).one_or_none()
    name = other.name if other else "Member"
    last = _last(db, row.id)
    preview = (last.body if last else "No messages yet.")[:140]
    org = bool(other and ("@" in other.email and other.email.split("@")[0] in {"kudi", "semicolon", "jobs"}))
    return ConversationOut(
        id=row.public_id,
        name=name,
        avatar=avatar(name),
        preview=preview,
        time=ago(last.created_at if last else row.created_at),
        unread=bool(last and last.sender_id != user.id),
        org=org or bool(other and other.role == "buyer" and "mworks.ng" in (other.email or "") and other.name.endswith("Hiring")),
        steel="employer" in (other.name or "").lower() if other else False,
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    rows = (
        db.query(Conversation)
        .filter(or_(Conversation.user_a_id == user.id, Conversation.user_b_id == user.id))
        .order_by(Conversation.created_at.desc())
        .limit(50)
        .all()
    )
    rows.sort(key=lambda r: (_last(db, r.id).created_at if _last(db, r.id) else r.created_at), reverse=True)
    return [_conv_out(db, r, user) for r in rows]


@router.get("/conversations/{cid}/messages", response_model=list[ChatMessageOut])
def list_messages(
    cid: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    conv = _owned(db, cid, user)
    if conv is None:
        raise HTTPException(status_code=404, detail={"error": "Conversation not found.", "code": "NOT_FOUND"})
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conv.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(200)
        .all()
    )
    return [
        ChatMessageOut(
            id=m.id,
            fromMe=m.sender_id == user.id,
            text=m.body,
            time=ago(m.created_at),
        )
        for m in rows
    ]


@router.post("/conversations/{cid}/messages", response_model=ChatMessageOut, status_code=201)
def send_message(
    cid: str,
    body: ChatSendIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    conv = _owned(db, cid, user)
    if conv is None:
        raise HTTPException(status_code=404, detail={"error": "Conversation not found.", "code": "NOT_FOUND"})
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail={"error": "Message cannot be empty.", "code": "VALIDATION_ERROR"})
    row = ChatMessage(conversation_id=conv.id, sender_id=user.id, body=text[:4000])
    db.add(row)
    db.commit()
    db.refresh(row)
    return ChatMessageOut(id=row.id, fromMe=True, text=row.body, time=ago(row.created_at))
