import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base

JsonType = JSON().with_variant(SQLITE_JSON(), "sqlite")


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, default=lambda: uuid.uuid4().hex[:16])
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(64), default="Nigeria")
    role: Mapped[str] = mapped_column(String(16), default="buyer")
    password_hash: Mapped[str] = mapped_column(String(120))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    trust_score: Mapped[int] = mapped_column(Integer, default=50)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listings: Mapped[list["Listing"]] = relationship(back_populates="seller")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("slug", name="uq_listings_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(80), index=True)
    seller_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(24), index=True)
    title: Mapped[str] = mapped_column(String(160))
    blurb: Mapped[str] = mapped_column(String(280))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    models: Mapped[list] = mapped_column(JsonType, default=list)
    prompt_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_value: Mapped[int] = mapped_column(Integer)
    rating: Mapped[float] = mapped_column(default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verify_type: Mapped[str] = mapped_column(String(24), default="originality")
    delivery: Mapped[str] = mapped_column(String(64), default="Instant download")
    tags: Mapped[list] = mapped_column(JsonType, default=list)
    metrics: Mapped[list] = mapped_column(JsonType, default=list)
    verification_log: Mapped[list] = mapped_column(JsonType, default=list)
    reviews: Mapped[list] = mapped_column(JsonType, default=list)
    license: Mapped[str | None] = mapped_column(String(32), nullable=True)
    object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    prompt_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="live")
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    minhash_sig: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    seller: Mapped[User] = relationship(back_populates="listings")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    public_ref: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    listing_id: Mapped[str] = mapped_column(ForeignKey("listings.id"), index=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    seller_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    amount: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(24), default="pending_payment")
    brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeline: Mapped[list] = mapped_column(JsonType, default=list)
    payment_ref: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    payment_provider: Mapped[str | None] = mapped_column(String(24), nullable=True)
    delivery_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("slug", name="uq_jobs_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(80), index=True)
    poster_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    company: Mapped[str] = mapped_column(String(120))
    company_avatar: Mapped[str] = mapped_column(String(8), default="?")
    verified_employer: Mapped[bool] = mapped_column(Boolean, default=True)
    track: Mapped[str] = mapped_column(String(48), index=True)
    type: Mapped[str] = mapped_column(String(24), index=True)
    location: Mapped[str] = mapped_column(String(120))
    salary: Mapped[str] = mapped_column(String(120))
    salary_min: Mapped[int] = mapped_column(Integer, default=0)
    min_trust: Mapped[int] = mapped_column(Integer, default=0)
    skills: Mapped[list] = mapped_column(JsonType, default=list)
    about: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text)
    responsibilities: Mapped[list] = mapped_column(JsonType, default=list)
    success_fee: Mapped[bool] = mapped_column(Boolean, default=False)
    applicant_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(24), default="live")
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    external_key: Mapped[str | None] = mapped_column(String(180), unique=True, nullable=True, index=True)
    apply_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    poster: Mapped[User] = relationship()


class JobApplication(Base):
    __tablename__ = "job_applications"
    __table_args__ = (UniqueConstraint("job_id", "applicant_id", name="uq_job_applicant"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    public_id: Mapped[str] = mapped_column(String(24), unique=True, index=True, default=lambda: "JA-" + uuid.uuid4().hex[:8])
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    applicant_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    share_history: Mapped[bool] = mapped_column(Boolean, default=True)
    via: Mapped[str] = mapped_column(String(16), default="manual")
    fit: Mapped[int] = mapped_column(Integer, default=0)
    rank_reason: Mapped[str] = mapped_column(String(280), default="")
    cv_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    interview_score: Mapped[int] = mapped_column(Integer, default=0)
    interview_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_session_id: Mapped[str | None] = mapped_column(String(24), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="applied")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[Job] = relationship()
    applicant: Mapped[User] = relationship()


class AgentPref(Base):
    __tablename__ = "agent_prefs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    threshold: Mapped[int] = mapped_column(Integer, default=85)
    dismissed: Mapped[list] = mapped_column(JsonType, default=list)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    public_id: Mapped[str] = mapped_column(String(24), unique=True, index=True, default=lambda: "C-" + uuid.uuid4().hex[:10])
    user_a_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    user_b_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScanVerdict(Base):
    __tablename__ = "scan_verdicts"
    __table_args__ = (UniqueConstraint("object_key", name="uq_scan_object_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    object_key: Mapped[str] = mapped_column(String(512), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), default="clean")
    reasons: Mapped[list] = mapped_column(JsonType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TheftClaim(Base):
    __tablename__ = "theft_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    public_id: Mapped[str] = mapped_column(String(24), unique=True, index=True, default=lambda: "TC-" + uuid.uuid4().hex[:8].upper())
    listing_id: Mapped[str] = mapped_column(ForeignKey("listings.id"), index=True)
    claimant_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), default="open")
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listing: Mapped["Listing"] = relationship()
    claimant: Mapped["User"] = relationship()


class FeedEvent(Base):
    __tablename__ = "feed_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    post_key: Mapped[str] = mapped_column(String(160), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewTask(Base):
    __tablename__ = "interview_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), unique=True, index=True)
    prompt: Mapped[str] = mapped_column(Text)
    time_limit_sec: Mapped[int] = mapped_column(Integer, default=1800)
    tests: Mapped[list] = mapped_column(JsonType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["Job"] = relationship()


class InterviewAttempt(Base):
    __tablename__ = "interview_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    public_id: Mapped[str] = mapped_column(String(24), unique=True, index=True, default=lambda: "IA-" + uuid.uuid4().hex[:8].upper())
    task_id: Mapped[str] = mapped_column(ForeignKey("interview_tasks.id"), index=True)
    applicant_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    artifact_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    scorecard: Mapped[list] = mapped_column(JsonType, default=list)
    status: Mapped[str] = mapped_column(String(24), default="in_progress")

    task: Mapped["InterviewTask"] = relationship()
    applicant: Mapped["User"] = relationship()


class VideoQuestion(Base):
    __tablename__ = "video_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class VideoAnswer(Base):
    __tablename__ = "video_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    application_id: Mapped[str] = mapped_column(ForeignKey("job_applications.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("video_questions.id"), index=True)
    object_key: Mapped[str] = mapped_column(String(512))
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    retain_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(24), default="stored")


class InterviewerLicense(Base):
    __tablename__ = "interviewer_licenses"
    __table_args__ = (UniqueConstraint("user_id", "listing_id", name="uq_interviewer_user_listing"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    listing_id: Mapped[str] = mapped_column(ForeignKey("listings.id"), index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    plan: Mapped[str] = mapped_column(String(16), default="trial")
    status: Mapped[str] = mapped_column(String(16), default="active")
    turns_used: Mapped[int] = mapped_column(Integer, default=0)
    turns_cap: Mapped[int] = mapped_column(Integer, default=8)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewerDoc(Base):
    __tablename__ = "interviewer_docs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    listing_id: Mapped[str] = mapped_column(ForeignKey("listings.id"), index=True)
    object_key: Mapped[str] = mapped_column(String(512))
    filename: Mapped[str] = mapped_column(String(180), default="brief.txt")
    chunks: Mapped[list] = mapped_column(JsonType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewerSession(Base):
    __tablename__ = "interviewer_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    public_id: Mapped[str] = mapped_column(String(24), unique=True, index=True, default=lambda: "AI-" + uuid.uuid4().hex[:8].upper())
    license_id: Mapped[str] = mapped_column(ForeignKey("interviewer_licenses.id"), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("jobs.id"), nullable=True, index=True)
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="awaiting_consent")
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    scorecard: Mapped[list] = mapped_column(JsonType, default=list)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewerTurn(Base):
    __tablename__ = "interviewer_turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("interviewer_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BlogPost(Base):
    __tablename__ = "blog_posts"
    __table_args__ = (UniqueConstraint("slug", name="uq_blog_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(200))
    excerpt: Mapped[str] = mapped_column(String(480), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(48), default="Tech news", index=True)
    tags: Mapped[list] = mapped_column(JsonType, default=list)
    source: Mapped[str] = mapped_column(String(16), default="manual")  # manual | agent
    source_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    author_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    media: Mapped[list] = mapped_column(JsonType, default=list)
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)  # draft | published
    read_minutes: Mapped[int] = mapped_column(Integer, default=3)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author: Mapped[User | None] = relationship()
