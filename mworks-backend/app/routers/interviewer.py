from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.db import get_db
from app.deps import require_user
from app.interviewer import (
    access_license,
    active_license,
    consume_turn,
    cv_excerpt,
    grant_license,
    ingest_doc,
    listing_for_agent,
    next_agent_turn,
    opening_message,
    write_application_score,
)
from app.models import (
    InterviewerDoc,
    InterviewerLicense,
    InterviewerSession,
    InterviewerTurn,
    Job,
    JobApplication,
    Listing,
    User,
)
from app.rate_limit import rate_limit
from app.scan import ScanFailed
from app.schemas import (
    InterviewerConsentIn,
    InterviewerDocIn,
    InterviewerDocOut,
    InterviewerLicenseOut,
    InterviewerSessionIn,
    InterviewerSessionOut,
    InterviewerTurnIn,
    InterviewerTurnOut,
)
from app.storage import object_exists, owned_object_key, read_bytes

router = APIRouter(prefix="/v1", tags=["interviewer"])


def _load_agent(db: Session, slug: str) -> Listing:
    listing = listing_for_agent(db, slug) or db.query(Listing).filter(Listing.slug == slug, Listing.type == "agent", Listing.status == "live").one_or_none()
    if listing is None:
        raise HTTPException(status_code=404, detail={"error": "Interviewer listing not found.", "code": "NOT_FOUND"})
    return listing


def _license_out(row: InterviewerLicense, listing: Listing) -> InterviewerLicenseOut:
    exp = row.expires_at
    if exp and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return InterviewerLicenseOut(
        listingId=listing.slug,
        plan=row.plan,
        status=row.status,
        turnsUsed=row.turns_used,
        turnsCap=row.turns_cap,
        expiresAt=exp.date().isoformat() if exp else "",
        hosted=True,
    )


def _turns(db: Session, session_id: str) -> list[InterviewerTurn]:
    return (
        db.query(InterviewerTurn)
        .filter(InterviewerTurn.session_id == session_id)
        .order_by(InterviewerTurn.created_at.asc())
        .all()
    )


def _session_out(
    db: Session,
    row: InterviewerSession,
    *,
    license_row: InterviewerLicense | None,
    include_turns: bool,
    user: User | None = None,
) -> InterviewerSessionOut:
    job = db.query(Job).filter(Job.id == row.job_id).one_or_none() if row.job_id else None
    candidate = db.query(User).filter(User.id == row.candidate_id).one_or_none()
    company = db.query(User).filter(User.id == row.company_id).one_or_none()
    left = 0
    if license_row is not None:
        left = max(0, int(license_row.turns_cap or 0) - int(license_row.turns_used or 0))
    turns = _turns(db, row.id) if include_turns else []
    docs_n = 0
    if license_row is not None:
        docs_n = (
            db.query(InterviewerDoc)
            .filter(InterviewerDoc.owner_id == row.company_id, InterviewerDoc.listing_id == license_row.listing_id)
            .count()
        )
    return InterviewerSessionOut(
        id=row.public_id,
        status=row.status,
        plan=license_row.plan if license_row else None,
        jobTitle=job.title if job else None,
        companyName=company.name if company else None,
        candidateName=candidate.name if candidate else None,
        consentRequired=row.consent_at is None,
        disclosedAi=True,
        questionCount=row.question_count,
        score=row.score if row.status == "scored" else None,
        scorecard=row.scorecard or [],
        summary=row.summary,
        turns=[InterviewerTurnOut(role=t.role, text=t.body) for t in turns],
        turnsLeft=left,
        youAreCandidate=bool(user and user.id == row.candidate_id),
        youAreCompany=bool(user and user.id == row.company_id),
        docsIndexed=docs_n,
        docsHint="Grounded on company docs." if docs_n else "No company docs indexed yet.",
    )


def _can_view(user: User, row: InterviewerSession) -> bool:
    return user.id in {row.company_id, row.candidate_id} or user.is_admin


@router.get("/interviewer/license", response_model=InterviewerLicenseOut)
def get_license(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
    listing_slug: str = "ai-interviewer",
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    listing = _load_agent(db, listing_slug)
    row = (
        db.query(InterviewerLicense)
        .filter(InterviewerLicense.user_id == user.id, InterviewerLicense.listing_id == listing.id)
        .one_or_none()
    )
    if row is None:
        if listing.seller_id == user.id:
            row = grant_license(db, settings, user.id, listing, plan="seller")
            db.commit()
            db.refresh(row)
        else:
            raise HTTPException(status_code=404, detail={"error": "No interviewer license on this account.", "code": "NOT_FOUND"})
    return _license_out(row, listing)


@router.get("/interviewer/licenses", response_model=list[InterviewerLicenseOut])
def list_licenses(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    rows = db.query(InterviewerLicense).filter(InterviewerLicense.user_id == user.id).all()
    listing_ids = {r.listing_id for r in rows}
    owned = db.query(Listing).filter(Listing.seller_id == user.id, Listing.type == "agent", Listing.status == "live").all()
    listings = {row.id: row for row in db.query(Listing).filter(Listing.id.in_(listing_ids)).all()} if listing_ids else {}
    out = []
    seen = set()
    for row in rows:
        listing = listings.get(row.listing_id)
        if listing is None or listing.type != "agent":
            continue
        seen.add(listing.id)
        out.append(_license_out(row, listing))
    for listing in owned:
        if listing.id in seen:
            continue
        row = grant_license(db, settings, user.id, listing, plan="seller")
        out.append(_license_out(row, listing))
    if owned:
        db.commit()
    return out


@router.post("/listings/{slug}/trial", response_model=InterviewerLicenseOut, status_code=201)
def start_trial(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    listing = _load_agent(db, slug)
    if listing.seller_id == user.id:
        raise HTTPException(status_code=400, detail={"error": "You cannot trial your own listing.", "code": "BAD_REQUEST"})
    existing = (
        db.query(InterviewerLicense)
        .filter(InterviewerLicense.user_id == user.id, InterviewerLicense.listing_id == listing.id)
        .one_or_none()
    )
    if existing is not None and existing.plan in {"purchased", "hired"} and existing.status == "active":
        return _license_out(existing, listing)
    if existing is not None and existing.plan == "trial":
        live = active_license(db, user.id, listing)
        if live is not None:
            return _license_out(live, listing)
        raise HTTPException(status_code=400, detail={"error": "This trial is used up. Buy or hire a license.", "code": "TRIAL_USED"})
    row = grant_license(db, settings, user.id, listing, plan="trial")
    db.commit()
    db.refresh(row)
    return _license_out(row, listing)


@router.post("/interviewer/docs", response_model=InterviewerDocOut, status_code=201)
def add_doc(
    body: InterviewerDocIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
    listing_slug: str = "ai-interviewer",
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    listing = _load_agent(db, listing_slug)
    license_row = access_license(db, settings, user, listing)
    if license_row is None:
        raise HTTPException(status_code=403, detail={"error": "Start a trial or buy the interviewer first.", "code": "FORBIDDEN"})
    db.commit()
    try:
        key = owned_object_key(user.public_id, body.object_key, kinds={"rag_doc"})
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "That file upload is not valid.", "code": "BAD_FILE"})
    if not object_exists(settings, key):
        raise HTTPException(status_code=400, detail={"error": "Upload the file before indexing.", "code": "FILE_REQUIRED"})
    blob = read_bytes(settings, key, limit=min(settings.UPLOAD_MAX_BYTES, 4_000_000))
    filename = key.rsplit("/", 1)[-1]
    try:
        chunks = ingest_doc(settings, blob, filename)
    except ScanFailed as exc:
        raise HTTPException(status_code=400, detail={"error": str(exc), "code": getattr(exc, "code", "SCAN_FAILED")})
    if not chunks:
        raise HTTPException(status_code=400, detail={"error": "That document had no readable text.", "code": "BAD_FILE"})
    row = InterviewerDoc(owner_id=user.id, listing_id=listing.id, object_key=key, filename=filename[-180:], chunks=chunks)
    db.add(row)
    db.commit()
    db.refresh(row)
    return InterviewerDocOut(id=row.id, filename=row.filename, chunks=len(chunks))


@router.get("/interviewer/docs", response_model=list[InterviewerDocOut])
def list_docs(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
    listing_slug: str = "ai-interviewer",
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    listing = _load_agent(db, listing_slug)
    rows = db.query(InterviewerDoc).filter(InterviewerDoc.owner_id == user.id, InterviewerDoc.listing_id == listing.id).all()
    return [InterviewerDocOut(id=r.id, filename=r.filename, chunks=len(r.chunks or [])) for r in rows]


@router.post("/interviewer/sessions", response_model=InterviewerSessionOut, status_code=201)
def create_session(
    body: InterviewerSessionIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    listing = _load_agent(db, body.listing_slug)
    license_row = access_license(db, settings, user, listing)
    if license_row is None:
        raise HTTPException(status_code=403, detail={"error": "Start a trial or buy the interviewer first.", "code": "FORBIDDEN"})
    db.commit()
    job = None
    candidate = user
    if body.job_slug:
        job = db.query(Job).filter(Job.slug == body.job_slug, Job.status == "live").one_or_none()
        if job is None:
            raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
        if job.poster_id != user.id and not user.is_admin:
            raise HTTPException(status_code=403, detail={"error": "Only the hiring company can invite a candidate.", "code": "FORBIDDEN"})
    if body.application_id:
        app_row = (
            db.query(JobApplication)
            .options(joinedload(JobApplication.applicant), joinedload(JobApplication.job))
            .filter(JobApplication.public_id == body.application_id)
            .one_or_none()
        )
        if app_row is None or app_row.job is None:
            raise HTTPException(status_code=404, detail={"error": "Application not found.", "code": "NOT_FOUND"})
        if app_row.job.poster_id != user.id and not user.is_admin:
            raise HTTPException(status_code=403, detail={"error": "Only the hiring company can invite a candidate.", "code": "FORBIDDEN"})
        job = app_row.job
        candidate = app_row.applicant
        if candidate is None:
            raise HTTPException(status_code=404, detail={"error": "Applicant not found.", "code": "NOT_FOUND"})
        if app_row.status in {"applied", "in_review"}:
            app_row.status = "interview"
        open_row = (
            db.query(InterviewerSession)
            .filter(
                InterviewerSession.license_id == license_row.id,
                InterviewerSession.candidate_id == candidate.id,
                InterviewerSession.job_id == job.id,
                InterviewerSession.status.in_(("awaiting_consent", "in_progress")),
            )
            .order_by(InterviewerSession.created_at.desc())
            .first()
        )
        if open_row is not None:
            db.commit()
            return _session_out(db, open_row, license_row=license_row, include_turns=True, user=user)
    row = InterviewerSession(
        license_id=license_row.id,
        company_id=user.id,
        candidate_id=candidate.id,
        job_id=job.id if job else None,
        status="awaiting_consent",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _session_out(db, row, license_row=license_row, include_turns=True, user=user)


@router.get("/interviewer/sessions", response_model=list[InterviewerSessionOut])
def list_sessions(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    rows = (
        db.query(InterviewerSession)
        .filter((InterviewerSession.company_id == user.id) | (InterviewerSession.candidate_id == user.id))
        .order_by(InterviewerSession.created_at.desc())
        .limit(40)
        .all()
    )
    out = []
    for row in rows:
        lic = db.query(InterviewerLicense).filter(InterviewerLicense.id == row.license_id).one_or_none()
        out.append(_session_out(db, row, license_row=lic, include_turns=False, user=user))
    return out


def _load_session(db: Session, public_id: str, user: User) -> InterviewerSession:
    row = db.query(InterviewerSession).filter(InterviewerSession.public_id == public_id).one_or_none()
    if row is None or not _can_view(user, row):
        raise HTTPException(status_code=404, detail={"error": "Interview not found.", "code": "NOT_FOUND"})
    return row


@router.get("/interviewer/sessions/{public_id}", response_model=InterviewerSessionOut)
def get_session(
    public_id: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    row = _load_session(db, public_id, user)
    lic = db.query(InterviewerLicense).filter(InterviewerLicense.id == row.license_id).one_or_none()
    return _session_out(db, row, license_row=lic, include_turns=True, user=user)


@router.post("/interviewer/sessions/{public_id}/consent", response_model=InterviewerSessionOut)
def consent_session(
    public_id: str,
    body: InterviewerConsentIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    if not body.consent:
        raise HTTPException(status_code=400, detail={"error": "Consent is required. This interviewer is an AI, not a human.", "code": "CONSENT_REQUIRED"})
    row = _load_session(db, public_id, user)
    if user.id != row.candidate_id:
        raise HTTPException(status_code=403, detail={"error": "Only the candidate can consent.", "code": "FORBIDDEN"})
    if row.consent_at is None:
        row.consent_at = datetime.now(timezone.utc)
        row.status = "in_progress"
        db.add(InterviewerTurn(session_id=row.id, role="agent", body=opening_message()))
        row.question_count = 1
    db.commit()
    lic = db.query(InterviewerLicense).filter(InterviewerLicense.id == row.license_id).one_or_none()
    return _session_out(db, row, license_row=lic, include_turns=True, user=user)


@router.post("/interviewer/sessions/{public_id}/turns", response_model=InterviewerSessionOut)
def post_turn(
    public_id: str,
    body: InterviewerTurnIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="interviewer_turns", limit=min(40, settings.RATE_LIMIT_API_PER_MIN))
    row = _load_session(db, public_id, user)
    if user.id != row.candidate_id:
        raise HTTPException(status_code=403, detail={"error": "Only the candidate can answer.", "code": "FORBIDDEN"})
    if row.consent_at is None:
        raise HTTPException(status_code=400, detail={"error": "Consent is required before answering.", "code": "CONSENT_REQUIRED"})
    if row.status == "scored":
        raise HTTPException(status_code=400, detail={"error": "This interview is already scored.", "code": "BAD_REQUEST"})
    listing = db.query(Listing).join(InterviewerLicense, InterviewerLicense.listing_id == Listing.id).filter(InterviewerLicense.id == row.license_id).one_or_none()
    if listing is None:
        raise HTTPException(status_code=404, detail={"error": "Interviewer listing not found.", "code": "NOT_FOUND"})
    license_row = db.query(InterviewerLicense).filter(InterviewerLicense.id == row.license_id).one_or_none()
    if license_row is None or active_license(db, license_row.user_id, listing) is None:
        raise HTTPException(status_code=403, detail={"error": "This interviewer license is no longer active.", "code": "FORBIDDEN"})
    db.add(InterviewerTurn(session_id=row.id, role="candidate", body=body.text.strip()))
    db.flush()
    job = db.query(Job).filter(Job.id == row.job_id).one_or_none() if row.job_id else None
    candidate = db.query(User).filter(User.id == row.candidate_id).one()
    app_row = None
    if job is not None:
        app_row = (
            db.query(JobApplication)
            .filter(JobApplication.job_id == job.id, JobApplication.applicant_id == candidate.id)
            .one_or_none()
        )
    docs = db.query(InterviewerDoc).filter(InterviewerDoc.owner_id == row.company_id, InterviewerDoc.listing_id == listing.id).all()
    turns = _turns(db, row.id)
    max_q = int(settings.INTERVIEWER_MAX_QUESTIONS or 6)
    wrap = int(row.question_count or 0) >= max_q
    question, done, score, card, summary = next_agent_turn(
        db,
        settings,
        row,
        candidate=candidate,
        job=job,
        cv_text=cv_excerpt(settings, app_row),
        docs=docs,
        turns=turns,
        max_questions=max_q if not wrap else 0,
        playbook=listing.prompt_body or "",
    )
    consume_turn(license_row)
    if done or wrap:
        row.status = "scored"
        row.score = score
        row.scorecard = card
        row.summary = summary
        db.add(InterviewerTurn(session_id=row.id, role="agent", body=summary or "Interview complete. A human reviewer will read this scorecard."))
        write_application_score(app_row, row, score=score, summary=summary)
    else:
        db.add(InterviewerTurn(session_id=row.id, role="agent", body=question))
        row.question_count = int(row.question_count or 0) + 1
        row.status = "in_progress"
    db.commit()
    db.refresh(row)
    return _session_out(db, row, license_row=license_row, include_turns=True, user=user)
