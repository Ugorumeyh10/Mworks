from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import User
from app.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def require_user(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail={"error": "Authentication required.", "code": "UNAUTHENTICATED"})
    try:
        payload = decode_access_token(settings, creds.credentials)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail={"error": "Authentication required.", "code": "UNAUTHENTICATED"})
    sub = payload.get("sub")
    user = db.query(User).filter(User.public_id == sub).one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail={"error": "Authentication required.", "code": "UNAUTHENTICATED"})
    request.state.user_id = user.public_id
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail={"error": "Admin role required.", "code": "FORBIDDEN"})
    return user


def optional_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User | None:
    if creds is None or creds.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_access_token(settings, creds.credentials)
    except InvalidTokenError:
        return None
    return db.query(User).filter(User.public_id == payload.get("sub")).one_or_none()
