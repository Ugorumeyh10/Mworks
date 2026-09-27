import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

_lock = Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "unknown")[:64]


def rate_limit(request: Request, *, bucket: str, limit: int, window_s: int = 60) -> None:
    ip = client_ip(request)
    key = f"{bucket}:{ip}"
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and now - q[0] > window_s:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(
                status_code=429,
                detail={"error": "Too many requests. Try again shortly.", "code": "RATE_LIMITED"},
                headers={"Retry-After": "60"},
            )
        q.append(now)
