from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.db import get_db
from app.deps import require_user
from app.fmt import ago, placed, slugify
from app.ingest_jobs import job_copy, looks_like_markup
from app.rank import applicant_rank
from app.models import AgentPref, Job, JobApplication, Listing, User
from app.rate_limit import rate_limit
from app.schemas import (
    AgentActivityOut,
    AgentPrefIn,
    AgentPrefOut,
    ApplicationOut,
    ApplyIn,
    JobCreateIn,
    JobOut,
)

router = APIRouter(prefix="/v1", tags=["jobs"])


def _job_out(row: Job) -> JobOut:
    description = row.description or ""
    bullets = list(row.responsibilities or [])
    if looks_like_markup(description):
        description, extracted = job_copy(description)
        if extracted and not bullets:
            bullets = extracted
    return JobOut(
        id=row.slug,
        title=row.title,
        company=row.company,
        companyAvatar=row.company_avatar,
        verifiedEmployer=row.verified_employer,
        track=row.track,
        type=row.type,
        location=row.location,
        salary=row.salary,
        salaryMin=row.salary_min,
        posted=ago(row.created_at),
        applicants=row.applicant_count,
        minTrust=row.min_trust,
        skills=row.skills or [],
        about=row.about or "",
        description=description,
        responsibilities=bullets,
        status=row.status,
        source=row.source,
        sourceUrl=row.apply_url,
    )


def _profile_tags(db: Session, user: User) -> set[str]:
    tags: set[str] = set()
    rows = db.query(Listing).filter(Listing.seller_id == user.id).all()
    for listing in rows:
        tags.update((t or "").strip() for t in (listing.tags or []) if t)
        if listing.category:
            tags.add(listing.category)
        if listing.platform:
            tags.add(listing.platform)
    return {t.lower() for t in tags if t}


def fit_score(user: User, job: Job, tags: set[str], note: str = "", cv_text: str = "") -> int:
    score, _reason = applicant_rank(user, job, tags, note=note, cv_text=cv_text)
    return score


def _reason(user: User, job: Job, fit: int, tags: set[str]) -> str:
    skills = job.skills or []
    overlap = [s for s in skills if s.lower() in tags]
    if fit >= 90:
        extra = f" Strong match on {', '.join(overlap[:3])}." if overlap else ""
        return f"Trust score {user.trust_score} is above the {job.min_trust}+ bar.{extra}"
    if overlap:
        return f"Matched {', '.join(overlap[:3])} against this role. Trust score {user.trust_score}."
    if user.trust_score < job.min_trust:
        return f"Trust score {user.trust_score} is below the employer {job.min_trust}+ bar; core marketplace history is still attached."
    return f"Partial profile fit at {fit}%. Trust score {user.trust_score} travels with the application."


def _app_out(row: JobApplication) -> ApplicationOut:
    job = row.job
    return ApplicationOut(
        id=row.public_id,
        jobId=job.slug if job else "",
        title=job.title if job else "Role",
        company=job.company if job else "",
        appliedAt=placed(row.created_at),
        via=row.via,
        fit=row.fit,
        status=row.status,
        reason=row.rank_reason or "",
        hasCv=bool(row.cv_key),
        interviewScore=row.interview_score if row.interview_session_id else None,
        interviewSessionId=row.interview_session_id,
        interviewSummary=row.interview_summary,
    )


def _prefs(db: Session, user: User) -> AgentPref:
    row = db.query(AgentPref).filter(AgentPref.user_id == user.id).one_or_none()
    if row is None:
        row = AgentPref(user_id=user.id, enabled=True, threshold=85, dismissed=[])
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _load_live_job(db: Session, slug: str) -> Job | None:
    return db.query(Job).filter(Job.slug == slug, Job.status == "live").one_or_none()


def _apply(db: Session, user: User, job: Job, *, via: str, note: str | None, share_history: bool, cv_key: str | None = None, cv_text: str = "") -> JobApplication:
    existing = (
        db.query(JobApplication)
        .filter(JobApplication.job_id == job.id, JobApplication.applicant_id == user.id)
        .one_or_none()
    )
    if existing is not None:
        return existing
    tags = _profile_tags(db, user)
    fit, why = applicant_rank(user, job, tags, note=note or "", cv_text=cv_text)
    row = JobApplication(
        job_id=job.id,
        applicant_id=user.id,
        note=(note or "").strip() or None,
        share_history=share_history,
        via=via,
        fit=fit,
        rank_reason=why[:280],
        cv_key=cv_key,
        status="applied",
    )
    db.add(row)
    job.applicant_count = int(job.applicant_count or 0) + 1
    db.commit()
    db.refresh(row)
    row.job = job
    return row


@router.get("/jobs", response_model=list[JobOut])
def list_jobs(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    track: str | None = Query(default=None, max_length=48),
    type: str | None = Query(default=None, max_length=24),
    q: str | None = Query(default=None, max_length=80),
    min_trust: int | None = Query(default=None, ge=0, le=95),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    query = db.query(Job).filter(Job.status == "live")
    if track:
        query = query.filter(Job.track == track)
    if type:
        query = query.filter(Job.type == type)
    if min_trust:
        query = query.filter(Job.min_trust >= min_trust)
    if q:
        needle = f"%{q.strip()}%"
        query = query.filter(
            or_(Job.title.ilike(needle), Job.company.ilike(needle), Job.description.ilike(needle))
        )
    rows = query.order_by(Job.created_at.desc()).limit(100).all()
    return [_job_out(r) for r in rows]


@router.get("/jobs/{slug}", response_model=JobOut)
def get_job(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = _load_live_job(db, slug)
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
    return _job_out(row)


@router.post("/jobs", response_model=JobOut, status_code=201)
def create_job(
    body: JobCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    skills = [s.strip() for s in body.skills if s and s.strip()][:16]
    duties = [s.strip() for s in body.responsibilities if s and s.strip()][:20]
    if body.competitive or not body.salary_min:
        salary = "Competitive"
    elif body.salary_max and body.salary_max > body.salary_min:
        salary = f"₦{body.salary_min:,} – ₦{body.salary_max:,} / month"
    else:
        salary = f"₦{body.salary_min:,} / month"
    row = Job(
        slug=slugify(body.title),
        poster_id=user.id,
        title=body.title.strip(),
        company=(body.company or user.name).strip()[:120],
        company_avatar=(body.company or user.name).strip()[:1].upper() or "?",
        verified_employer=user.trust_score >= 80,
        track=body.track,
        type=body.type,
        location=body.location.strip(),
        salary=salary,
        salary_min=0 if body.competitive else int(body.salary_min or 0),
        min_trust=body.min_trust,
        skills=skills,
        about=(body.about or "").strip(),
        description=body.description.strip(),
        responsibilities=duties,
        success_fee=body.success_fee,
        applicant_count=0,
        status="live" if user.trust_score >= 70 else "in_review",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _job_out(row)


@router.post("/jobs/{slug}/apply", response_model=ApplicationOut, status_code=201)
def apply_job(
    slug: str,
    body: ApplyIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    job = _load_live_job(db, slug)
    if job is None:
        raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
    existing = (
        db.query(JobApplication)
        .options(joinedload(JobApplication.job))
        .filter(JobApplication.job_id == job.id, JobApplication.applicant_id == user.id)
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(status_code=400, detail={"error": "You already applied to this role.", "code": "ALREADY_APPLIED"})
    cv_key = None
    cv_text = ""
    if body.cv_object_key:
        from app.storage import object_exists, owned_object_key, read_bytes

        try:
            cv_key = owned_object_key(user.public_id, body.cv_object_key, kinds={"cv"})
        except ValueError:
            raise HTTPException(status_code=400, detail={"error": "That CV upload is not valid.", "code": "BAD_FILE"})
        if not object_exists(settings, cv_key):
            raise HTTPException(status_code=400, detail={"error": "Upload the CV before applying.", "code": "FILE_REQUIRED"})
        from app.scan import ScanFailed, scan_bytes

        blob = read_bytes(settings, cv_key, limit=min(settings.UPLOAD_MAX_BYTES, 5_000_000))
        try:
            reasons = scan_bytes(settings, blob, filename=cv_key.rsplit("/", 1)[-1], kind="cv")
        except ScanFailed as exc:
            raise HTTPException(status_code=400, detail={"error": str(exc), "code": getattr(exc, "code", "SCAN_FAILED")})
        if reasons:
            raise HTTPException(status_code=400, detail={"error": reasons[0], "code": "SCAN_FAILED"})
        cv_text = blob.decode("utf-8", errors="ignore")
    row = _apply(db, user, job, via=body.via, note=body.note, share_history=body.share_history, cv_key=cv_key, cv_text=cv_text)
    return _app_out(row)


@router.get("/me/applications", response_model=list[ApplicationOut])
def my_applications(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    rows = (
        db.query(JobApplication)
        .options(joinedload(JobApplication.job))
        .filter(JobApplication.applicant_id == user.id)
        .order_by(JobApplication.created_at.desc())
        .limit(100)
        .all()
    )
    return [_app_out(r) for r in rows]


@router.get("/me/job-agent", response_model=AgentPrefOut)
def get_agent(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = _prefs(db, user)
    return AgentPrefOut(enabled=row.enabled, threshold=row.threshold)


@router.patch("/me/job-agent", response_model=AgentPrefOut)
def patch_agent(
    body: AgentPrefIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = _prefs(db, user)
    if body.enabled is not None:
        row.enabled = body.enabled
    if body.threshold is not None:
        row.threshold = body.threshold
    db.commit()
    db.refresh(row)
    return AgentPrefOut(enabled=row.enabled, threshold=row.threshold)


@router.get("/me/job-agent/activity", response_model=list[AgentActivityOut])
def agent_activity(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    tags = _profile_tags(db, user)
    jobs = db.query(Job).filter(Job.status == "live").order_by(Job.created_at.desc()).limit(50).all()
    out = []
    for job in jobs:
        fit = fit_score(user, job, tags)
        out.append(
            AgentActivityOut(
                id=job.slug,
                jobId=job.slug,
                title=job.title,
                company=job.company,
                track=job.track,
                fit=fit,
                at=ago(job.created_at),
                reason=_reason(user, job, fit, tags),
            )
        )
    return out


@router.post("/me/job-agent/activity/{slug}/apply", response_model=ApplicationOut, status_code=201)
def agent_apply(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    job = _load_live_job(db, slug)
    if job is None:
        raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
    row = _apply(db, user, job, via="agent", note=None, share_history=True)
    return _app_out(row)


@router.post("/me/job-agent/activity/{slug}/dismiss")
def agent_dismiss(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = _prefs(db, user)
    dismissed = list(row.dismissed or [])
    if slug not in dismissed:
        dismissed.append(slug)
        row.dismissed = dismissed
        db.commit()
    return {"status": "ok"}
