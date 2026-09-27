from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.blog_media import cover_from, is_object_key, normalize_media
from app.config import Settings, get_settings
from app.db import get_db
from app.deps import optional_user, require_admin
from app.fmt import slugify
from app.models import BlogPost, User
from app.news_agent import run_news_agent
from app.rate_limit import rate_limit
from app.schemas import BlogAgentRunOut, BlogCreateIn, BlogMediaOut, BlogPostOut
from app.storage import presign_get_inline

router = APIRouter(prefix="/v1/blog", tags=["blog"])


def _public_url(settings: Settings, url: str, kind: str) -> str:
    if not is_object_key(url):
        return url
    ctype = "video/mp4" if kind == "video" else "image/jpeg"
    if url.lower().endswith(".webm"):
        ctype = "video/webm"
    elif url.lower().endswith(".png"):
        ctype = "image/png"
    elif url.lower().endswith(".webp"):
        ctype = "image/webp"
    elif url.lower().endswith(".gif"):
        ctype = "image/gif"
    return presign_get_inline(settings, key=url, content_type=ctype)


def _out(row: BlogPost, settings: Settings, *, with_body: bool = False) -> BlogPostOut:
    pub = row.published_at
    if pub is not None and pub.tzinfo is None:
        pub = pub.replace(tzinfo=timezone.utc)
    made = row.created_at
    if made is not None and made.tzinfo is None:
        made = made.replace(tzinfo=timezone.utc)
    media = []
    for item in normalize_media(row.media or []):
        media.append(
            BlogMediaOut(kind=item["kind"], url=_public_url(settings, item["url"], item["kind"]))
        )
    cover = row.cover_url
    if cover:
        cover = _public_url(settings, cover, "image")
    elif media:
        cover = cover_from([{"kind": m.kind, "url": m.url} for m in media])
    return BlogPostOut(
        id=row.slug,
        title=row.title,
        excerpt=row.excerpt,
        body=row.body if with_body else None,
        category=row.category,
        tags=row.tags or [],
        source=row.source,
        sourceName=row.source_name,
        sourceUrl=row.source_url,
        authorName=row.author.name if row.author else ("Mworks Newsroom" if row.source == "agent" else None),
        status=row.status,
        readMinutes=row.read_minutes,
        publishedAt=pub.strftime("%b %d, %Y") if pub else None,
        createdAt=made.strftime("%b %d, %Y") if made else None,
        aiAssisted=row.source == "agent",
        coverUrl=cover,
        media=media,
    )


@router.get("", response_model=list[BlogPostOut])
def list_posts(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    category: str | None = Query(default=None, max_length=48),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    query = (
        db.query(BlogPost)
        .options(joinedload(BlogPost.author))
        .filter(BlogPost.status == "published")
    )
    if category:
        query = query.filter(BlogPost.category == category)
    rows = query.order_by(BlogPost.published_at.desc()).limit(30).all()
    return [_out(r, settings) for r in rows]


@router.get("/admin/posts", response_model=list[BlogPostOut])
def list_all_posts(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_admin),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    rows = (
        db.query(BlogPost)
        .options(joinedload(BlogPost.author))
        .order_by(BlogPost.created_at.desc())
        .limit(60)
        .all()
    )
    return [_out(r, settings) for r in rows]


@router.get("/{slug}", response_model=BlogPostOut)
def get_post(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User | None = Depends(optional_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = (
        db.query(BlogPost)
        .options(joinedload(BlogPost.author))
        .filter(BlogPost.slug == slug)
        .one_or_none()
    )
    if row is None or (row.status != "published" and not (user and user.is_admin)):
        raise HTTPException(status_code=404, detail={"error": "Post not found.", "code": "NOT_FOUND"})
    return _out(row, settings, with_body=True)


@router.post("", response_model=BlogPostOut, status_code=201)
def create_post(
    body: BlogCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_admin),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    media = normalize_media(body.media)
    if body.media and not media:
        raise HTTPException(status_code=400, detail={"error": "That media URL is not allowed.", "code": "BAD_REQUEST"})
    words = len(body.body.split())
    row = BlogPost(
        slug=slugify(body.title),
        title=body.title.strip(),
        excerpt=body.excerpt.strip(),
        body=body.body.strip(),
        category=body.category.strip() or "Tech news",
        tags=body.tags,
        source="manual",
        author_id=user.id,
        status="published" if body.publish else "draft",
        cover_url=cover_from(media),
        media=media,
        read_minutes=max(1, min(20, round(words / 180) or 1)),
        published_at=datetime.now(timezone.utc) if body.publish else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _out(row, settings, with_body=True)


def _load_admin_post(db: Session, slug: str) -> BlogPost:
    row = db.query(BlogPost).filter(BlogPost.slug == slug).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "Post not found.", "code": "NOT_FOUND"})
    return row


@router.post("/{slug}/publish", response_model=BlogPostOut)
def publish_post(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_admin),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = _load_admin_post(db, slug)
    if row.status != "published":
        row.status = "published"
        row.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _out(row, settings, with_body=True)


@router.post("/{slug}/unpublish", response_model=BlogPostOut)
def unpublish_post(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_admin),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = _load_admin_post(db, slug)
    row.status = "draft"
    db.commit()
    db.refresh(row)
    return _out(row, settings, with_body=True)


@router.post("/agent/run", response_model=BlogAgentRunOut)
def run_agent(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_admin),
):
    """Fetch public tech feeds and publish attributed summaries with media."""
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    created, skipped = run_news_agent(db, settings)
    posts = (
        db.query(BlogPost)
        .filter(BlogPost.source == "agent")
        .order_by(BlogPost.created_at.desc())
        .limit(20)
        .all()
    )
    out = [_out(r, settings) for r in posts]
    return BlogAgentRunOut(created=created, skipped=skipped, posts=out, drafts=out)
