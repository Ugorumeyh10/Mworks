from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.db import get_db
from app.deps import require_user
from app.hire import ensure_questions, ensure_task, expire_videos, score_attempt
from app.models import InterviewAttempt, InterviewTask, Job, JobApplication, User, VideoAnswer, VideoQuestion
from app.rate_limit import rate_limit
from app.rank import applicant_rank
from app.scan import ScanFailed, scan_bytes
from app.schemas import (
    ApplicantRankOut,
    InterviewScoreOut,
    InterviewSubmitIn,
    InterviewTaskOut,
    VideoAnswerIn,
    VideoAnswerOut,
    VideoQuestionOut,
)
from app.storage import object_exists, owned_object_key, read_bytes

router = APIRouter(prefix="/v1", tags=["hire"])


def _load_job(db: Session, slug: str) -> Job | None:
    return db.query(Job).filter(Job.slug == slug, Job.status == "live").one_or_none()


@router.get("/jobs/{slug}/interview", response_model=InterviewTaskOut)
def get_interview(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    job = _load_job(db, slug)
    if job is None:
        raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
    task = ensure_task(db, job)
    db.commit()
    open_row = (
        db.query(InterviewAttempt)
        .filter(InterviewAttempt.task_id == task.id, InterviewAttempt.applicant_id == user.id)
        .order_by(InterviewAttempt.started_at.desc())
        .first()
    )
    return InterviewTaskOut(
        prompt=task.prompt,
        timeLimitSec=task.time_limit_sec,
        attemptId=open_row.public_id if open_row else None,
        status=open_row.status if open_row else "ready",
    )


@router.post("/jobs/{slug}/interview/start", response_model=InterviewTaskOut, status_code=201)
def start_interview(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    job = _load_job(db, slug)
    if job is None:
        raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
    task = ensure_task(db, job)
    row = InterviewAttempt(task_id=task.id, applicant_id=user.id, status="in_progress")
    db.add(row)
    db.commit()
    db.refresh(row)
    return InterviewTaskOut(prompt=task.prompt, timeLimitSec=task.time_limit_sec, attemptId=row.public_id, status=row.status)


@router.post("/jobs/{slug}/interview/submit", response_model=InterviewScoreOut)
def submit_interview(
    slug: str,
    body: InterviewSubmitIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    job = _load_job(db, slug)
    if job is None:
        raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
    task = ensure_task(db, job)
    attempt = (
        db.query(InterviewAttempt)
        .filter(
            InterviewAttempt.task_id == task.id,
            InterviewAttempt.applicant_id == user.id,
            InterviewAttempt.status == "in_progress",
        )
        .order_by(InterviewAttempt.started_at.desc())
        .first()
    )
    if attempt is None:
        raise HTTPException(status_code=400, detail={"error": "Start the interview before submitting.", "code": "BAD_REQUEST"})
    blob = b""
    filename = "work.txt"
    if body.object_key:
        try:
            key = owned_object_key(user.public_id, body.object_key, kinds={"interview_artifact"})
        except ValueError:
            raise HTTPException(status_code=400, detail={"error": "That file upload is not valid.", "code": "BAD_FILE"})
        if not object_exists(settings, key):
            raise HTTPException(status_code=400, detail={"error": "Upload the work sample first.", "code": "FILE_REQUIRED"})
        blob = read_bytes(settings, key)
        attempt.artifact_key = key
        filename = key.rsplit("/", 1)[-1]
    elif (body.prompt_text or "").strip():
        blob = body.prompt_text.strip().encode("utf-8")
        attempt.prompt_text = body.prompt_text.strip()
    else:
        raise HTTPException(status_code=400, detail={"error": "Submit a file or prompt text.", "code": "VALIDATION_ERROR"})
    score_attempt(settings, attempt, task, blob, filename)
    db.commit()
    return InterviewScoreOut(
        attemptId=attempt.public_id,
        score=attempt.score,
        status=attempt.status,
        scorecard=attempt.scorecard or [],
        timeLimitSec=task.time_limit_sec,
    )


@router.get("/jobs/{slug}/interview/scorecard", response_model=InterviewScoreOut)
def interview_scorecard(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    job = _load_job(db, slug)
    if job is None:
        raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
    task = db.query(InterviewTask).filter(InterviewTask.job_id == job.id).one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail={"error": "No scorecard yet.", "code": "NOT_FOUND"})
    query = db.query(InterviewAttempt).filter(InterviewAttempt.task_id == task.id)
    if user.id != job.poster_id and not user.is_admin:
        query = query.filter(InterviewAttempt.applicant_id == user.id)
    attempt = query.order_by(InterviewAttempt.started_at.desc()).first()
    if attempt is None:
        raise HTTPException(status_code=404, detail={"error": "No scorecard yet.", "code": "NOT_FOUND"})
    return InterviewScoreOut(
        attemptId=attempt.public_id,
        score=attempt.score,
        status=attempt.status,
        scorecard=attempt.scorecard or [],
        timeLimitSec=task.time_limit_sec,
    )


@router.get("/jobs/{slug}/video-questions", response_model=list[VideoQuestionOut])
def video_questions(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    job = _load_job(db, slug)
    if job is None:
        raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
    expire_videos(db, settings)
    rows = ensure_questions(db, job)
    db.commit()
    return [VideoQuestionOut(id=r.id, prompt=r.prompt) for r in rows]


@router.post("/jobs/{slug}/video-answers", response_model=VideoAnswerOut, status_code=201)
def submit_video(
    slug: str,
    body: VideoAnswerIn,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    if not body.consent:
        raise HTTPException(status_code=400, detail={"error": "Consent is required to store this recording.", "code": "CONSENT_REQUIRED"})
    job = _load_job(db, slug)
    if job is None:
        raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
    question = db.query(VideoQuestion).filter(VideoQuestion.id == body.question_id, VideoQuestion.job_id == job.id).one_or_none()
    if question is None:
        raise HTTPException(status_code=404, detail={"error": "Question not found.", "code": "NOT_FOUND"})
    app_row = (
        db.query(JobApplication)
        .filter(JobApplication.job_id == job.id, JobApplication.applicant_id == user.id)
        .one_or_none()
    )
    if app_row is None:
        raise HTTPException(status_code=400, detail={"error": "Apply to the role before recording.", "code": "BAD_REQUEST"})
    try:
        key = owned_object_key(user.public_id, body.object_key, kinds={"interview_video"})
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "That file upload is not valid.", "code": "BAD_FILE"})
    if not object_exists(settings, key):
        raise HTTPException(status_code=400, detail={"error": "Upload the recording first.", "code": "FILE_REQUIRED"})
    blob = read_bytes(settings, key, limit=min(settings.UPLOAD_MAX_BYTES, 2_000_000))
    try:
        reasons = scan_bytes(settings, blob, filename=key.rsplit("/", 1)[-1], kind="interview_video")
    except ScanFailed as exc:
        raise HTTPException(status_code=400, detail={"error": str(exc), "code": getattr(exc, "code", "SCAN_FAILED")})
    # Video bytes are not executed. Header/size/MIME gates already ran at presign.
    # Full malware scan of large mp4s is ClamAV's job when configured.
    if reasons:
        raise HTTPException(status_code=400, detail={"error": reasons[0], "code": "SCAN_FAILED"})
    days = max(1, min(365, int(settings.VIDEO_RETAIN_DAYS or 90)))
    now = datetime.now(timezone.utc)
    row = VideoAnswer(
        application_id=app_row.id,
        question_id=question.id,
        object_key=key,
        consent_at=now,
        transcript=(body.transcript or "").strip() or "Transcript pending. A human reviewer will watch this recording.",
        retain_until=now + timedelta(days=days),
        status="stored",
    )
    db.add(row)
    db.commit()
    return VideoAnswerOut(
        questionId=question.id,
        status="stored",
        retainUntil=row.retain_until.date().isoformat(),
        transcript=row.transcript,
    )


@router.get("/jobs/{slug}/applicants", response_model=list[ApplicantRankOut])
def ranked_applicants(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(require_user),
):
    rate_limit(request, bucket="api", limit=settings.RATE_LIMIT_API_PER_MIN)
    job = _load_job(db, slug)
    if job is None or (job.poster_id != user.id and not user.is_admin):
        raise HTTPException(status_code=404, detail={"error": "Role not found.", "code": "NOT_FOUND"})
    rows = (
        db.query(JobApplication)
        .options(joinedload(JobApplication.applicant))
        .filter(JobApplication.job_id == job.id)
        .all()
    )
    out = []
    for row in rows:
        person = row.applicant
        out.append(
            ApplicantRankOut(
                id=row.public_id,
                name=person.name if person else "Applicant",
                trust=person.trust_score if person else 0,
                sales=person.sales_count if person else 0,
                fit=row.fit,
                reason=row.rank_reason or "",
                status=row.status,
                hasCv=bool(row.cv_key),
                interviewScore=row.interview_score if row.interview_session_id else None,
                interviewSessionId=row.interview_session_id,
                interviewSummary=row.interview_summary,
            )
        )
    out.sort(key=lambda r: r.fit, reverse=True)
    return out
