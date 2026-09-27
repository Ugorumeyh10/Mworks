from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import InterviewAttempt, InterviewTask, Job, VideoAnswer, VideoQuestion
from app.scan import ScanFailed, scan_bytes

DEFAULT_TESTS = [
    {"kind": "contains", "needle": "automat", "weight": 25, "label": "Mentions automation"},
    {"kind": "contains", "needle": "test", "weight": 15, "label": "Includes a test or validation step"},
]


def default_task(job: Job) -> dict:
    return {
        "prompt": (
            f"Timed work sample for {job.title}. Submit a prompt, flow XML, or short script that "
            "solves the role's core automation. Do not include secrets. The API does not execute "
            "your file; a static scorecard is shown to the employer."
        ),
        "time_limit_sec": 1800,
        "tests": DEFAULT_TESTS,
    }


def ensure_task(db: Session, job: Job) -> InterviewTask:
    row = db.query(InterviewTask).filter(InterviewTask.job_id == job.id).one_or_none()
    if row:
        return row
    spec = default_task(job)
    row = InterviewTask(
        job_id=job.id,
        prompt=spec["prompt"],
        time_limit_sec=spec["time_limit_sec"],
        tests=spec["tests"],
    )
    db.add(row)
    db.flush()
    return row


def ensure_questions(db: Session, job: Job) -> list[VideoQuestion]:
    rows = (
        db.query(VideoQuestion).filter(VideoQuestion.job_id == job.id).order_by(VideoQuestion.sort_order.asc()).all()
    )
    if rows:
        return rows
    prompts = [
        "Walk through an automation you shipped and how you tested it.",
        "How do you keep secrets out of a flow that talks to a bank or ATS?",
        "Describe a failure in production and what you changed afterward.",
    ]
    for i, prompt in enumerate(prompts):
        db.add(VideoQuestion(job_id=job.id, prompt=prompt, sort_order=i))
    db.flush()
    return (
        db.query(VideoQuestion).filter(VideoQuestion.job_id == job.id).order_by(VideoQuestion.sort_order.asc()).all()
    )


def score_attempt(settings: Settings, attempt: InterviewAttempt, task: InterviewTask, blob: bytes, filename: str) -> None:
    reasons: list[dict] = []
    score = 100
    started = attempt.started_at
    now = datetime.now(timezone.utc)
    if started and started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    elapsed = int((now - started).total_seconds()) if started else 0
    if elapsed > int(task.time_limit_sec or 1800):
        score -= 35
        reasons.append({"label": "Time box", "status": "Exceeded"})
    else:
        reasons.append({"label": "Time box", "status": "Passed"})
    try:
        hits = scan_bytes(settings, blob, filename=filename, kind="interview_artifact")
    except ScanFailed as exc:
        attempt.score = 0
        attempt.status = "rejected"
        attempt.scorecard = [{"label": "Security scan", "status": "Failed", "detail": str(exc)}]
        attempt.submitted_at = now
        return
    if hits:
        attempt.score = 0
        attempt.status = "rejected"
        attempt.scorecard = [{"label": "Security scan", "status": "Failed", "detail": hits[0]}]
        attempt.submitted_at = now
        return
    reasons.append({"label": "Security scan", "status": "Clean"})
    text = blob.decode("utf-8", errors="ignore").lower()
    for spec in task.tests or DEFAULT_TESTS:
        needle = (spec.get("needle") or "").lower()
        if spec.get("kind") == "contains" and needle:
            if needle not in text:
                score -= int(spec.get("weight") or 15)
                reasons.append({"label": spec.get("label") or needle, "status": "Missed"})
            else:
                reasons.append({"label": spec.get("label") or needle, "status": "Passed"})
    attempt.score = max(0, min(100, score))
    attempt.scorecard = reasons
    attempt.status = "scored"
    attempt.submitted_at = now


def expire_videos(db: Session, settings: Settings) -> int:
    now = datetime.now(timezone.utc)
    rows = db.query(VideoAnswer).filter(VideoAnswer.status == "stored", VideoAnswer.retain_until <= now).all()
    for row in rows:
        row.status = "expired"
        row.object_key = ""
        row.transcript = None
    return len(rows)
