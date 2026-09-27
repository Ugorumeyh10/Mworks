from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import RefreshToken, User
from app.rate_limit import rate_limit
from app.schemas import LoginIn, PublicUser, RefreshIn, SignupIn, TokenOut
from app.security import (
    hash_password,
    hash_refresh,
    issue_access_token,
    new_refresh_token,
    normalize_role,
    refresh_expiry,
    verify_password,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_AUTH_FAIL = {"error": "Email or password is incorrect.", "code": "AUTH_FAILED"}


def _tokens(settings: Settings, db: Session, user: User) -> TokenOut:
    access = issue_access_token(settings, sub=user.public_id, role=user.role)
    refresh = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh(refresh),
            expires_at=refresh_expiry(settings),
        )
    )
    db.commit()
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.JWT_ACCESS_MINUTES * 60,
        user=PublicUser(
            id=user.public_id,
            email=user.email,
            name=user.name,
            role=user.role,
            country=user.country,
            trust=user.trust_score,
            isAdmin=bool(user.is_admin),
        ),
    )


@router.post("/signup", response_model=TokenOut, status_code=201)
def signup(body: SignupIn, request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    rate_limit(request, bucket="auth", limit=settings.RATE_LIMIT_AUTH_PER_MIN)
    email = str(body.email).lower()
    if db.query(User).filter(User.email == email).one_or_none():
        raise HTTPException(status_code=409, detail={"error": "An account with that email already exists.", "code": "EMAIL_TAKEN"})
    user = User(
        email=email,
        name=body.name.strip(),
        country=body.country.strip()[:64],
        role=normalize_role(body.role),
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _tokens(settings, db, user)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    rate_limit(request, bucket="auth", limit=settings.RATE_LIMIT_AUTH_PER_MIN)
    email = str(body.email).lower()
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail=_AUTH_FAIL)
    return _tokens(settings, db, user)


@router.post("/refresh", response_model=TokenOut)
def refresh(body: RefreshIn, request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    rate_limit(request, bucket="auth", limit=settings.RATE_LIMIT_AUTH_PER_MIN)
    hashed = hash_refresh(body.refresh_token)
    row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hashed, RefreshToken.revoked.is_(False))
        .one_or_none()
    )
    now = datetime.now(timezone.utc)
    if row is None or row.expires_at < now:
        raise HTTPException(status_code=401, detail={"error": "Authentication required.", "code": "UNAUTHENTICATED"})
    row.revoked = True
    user = db.query(User).filter(User.id == row.user_id).one()
    return _tokens(settings, db, user)
