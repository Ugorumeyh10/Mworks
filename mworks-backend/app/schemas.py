from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_LISTING_TYPES = {"automation", "prompt", "document", "source", "agent"}
_ORDER_KINDS = {"purchase", "hire", "revise"}
_ROLES = {"buyer", "seller", "both"}
_CATEGORIES = {
    "Finance",
    "Customer Support",
    "Data & Scraping",
    "HR & Recruiting",
    "Marketing",
    "Operations",
    "Developer Tools",
    "Process mapping",
    "Requirements",
    "Architecture",
    "UAT",
    "Governance",
    "SOP",
}
_DOC_LICENSES = {"template", "exclusive", "revise_rights"}
REVISE_MAX_NAIRA = 25_000


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SignupIn(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    country: str = Field(default="Nigeria", max_length=64)
    role: str = "buyer"

    @field_validator("role")
    @classmethod
    def role_ok(cls, v: str) -> str:
        if v not in _ROLES:
            raise ValueError("invalid role")
        return v

    @field_validator("password")
    @classmethod
    def pw_ok(cls, v: str) -> str:
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("password must include letters and numbers")
        return v


class LoginIn(StrictModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenOut(StrictModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "PublicUser"


class RefreshIn(StrictModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class PublicUser(StrictModel):
    id: str
    email: EmailStr
    name: str
    role: str
    country: str
    trust: int
    isAdmin: bool = False


class SellerCard(StrictModel):
    name: str
    avatar: str
    trust: int
    sales: int
    rating: float
    reviews: int
    since: str


class ListingOut(StrictModel):
    id: str
    type: str
    title: str
    blurb: str
    description: str
    category: str
    platform: str | None = None
    models: list[str] = []
    promptCount: int | None = None
    seller: SellerCard
    priceValue: int
    rating: float
    reviewCount: int
    verified: bool
    verifyType: str
    delivery: str
    tags: list[str] = []
    metrics: list[dict] = []
    verificationLog: list[dict] = []
    reviews: list[dict] = []
    license: str | None = None
    status: str | None = None
    hasFile: bool = False
    qualityScore: int = 0
    rankReason: str = ""


class ListingCreateIn(StrictModel):
    type: str
    title: str = Field(min_length=4, max_length=160)
    blurb: str = Field(min_length=10, max_length=280)
    description: str = Field(min_length=30, max_length=8000)
    category: str
    price_value: int = Field(gt=0, le=50_000_000)
    tags: list[str] = Field(default_factory=list, max_length=12)
    platform: str | None = None
    models: list[str] = Field(default_factory=list, max_length=8)
    prompt_count: int | None = Field(default=None, ge=1, le=500)
    metrics: list[dict] = Field(default_factory=list, max_length=6)
    license: str | None = None
    object_key: str | None = Field(default=None, max_length=512)
    prompt_text: str | None = Field(default=None, max_length=20000)

    @field_validator("type")
    @classmethod
    def type_ok(cls, v: str) -> str:
        if v not in _LISTING_TYPES:
            raise ValueError("invalid listing type")
        return v

    @field_validator("category")
    @classmethod
    def cat_ok(cls, v: str) -> str:
        if v not in _CATEGORIES:
            raise ValueError("invalid category")
        return v

    @field_validator("tags")
    @classmethod
    def tags_ok(cls, v: list[str]) -> list[str]:
        out = [t.strip()[:32] for t in v if t and t.strip()]
        return out[:12]


class CheckoutIn(StrictModel):
    kind: str = "purchase"
    brief: str | None = Field(default=None, max_length=4000)
    budget: int | None = Field(default=None, gt=0, le=50_000_000)

    @field_validator("kind")
    @classmethod
    def kind_ok(cls, v: str) -> str:
        if v not in _ORDER_KINDS:
            raise ValueError("invalid order kind")
        return v


class PartyCard(StrictModel):
    name: str
    avatar: str


class OrderOut(StrictModel):
    id: str
    listingId: str
    title: str
    type: str
    kind: str
    amount: int
    state: str
    brief: str | None = None
    timeline: list[dict] = []
    counterparty: PartyCard | None = None
    placedAt: str | None = None
    paymentUrl: str | None = None
    paymentProvider: str | None = None
    role: str | None = None
    hasDownload: bool = False
    hasPrompt: bool = False


class DeliverIn(StrictModel):
    object_key: str = Field(min_length=8, max_length=512)


class LocalPayIn(StrictModel):
    reference: str = Field(min_length=8, max_length=32)


class PresignIn(StrictModel):
    filename: str = Field(min_length=3, max_length=180)
    content_type: str = Field(max_length=80)
    kind: str = "document"
    size_bytes: int | None = Field(default=None, ge=1, le=50_000_000)


class PresignOut(StrictModel):
    object_key: str
    put_url: str
    headers: dict[str, str] = {}


class DownloadOut(StrictModel):
    url: str
    filename: str
    expiresIn: int = 120


class PromptOut(StrictModel):
    promptText: str
    filename: str = "prompt.txt"


_TRACKS = {"RPA Developer", "Business Analyst", "Project Manager", "Solution Architect"}
_JOB_TYPES = {"Full-time", "Contract", "Project gig"}


class JobOut(StrictModel):
    id: str
    title: str
    company: str
    companyAvatar: str
    verifiedEmployer: bool = True
    track: str
    type: str
    location: str
    salary: str
    salaryMin: int = 0
    posted: str = ""
    applicants: int = 0
    minTrust: int = 0
    skills: list[str] = []
    about: str = ""
    description: str = ""
    responsibilities: list[str] = []
    status: str | None = None
    source: str | None = None
    sourceUrl: str | None = None


class JobCreateIn(StrictModel):
    title: str = Field(min_length=6, max_length=160)
    track: str
    type: str = "Full-time"
    location: str = Field(min_length=2, max_length=120)
    salary_min: int | None = Field(default=None, ge=0, le=50_000_000)
    salary_max: int | None = Field(default=None, ge=0, le=50_000_000)
    competitive: bool = False
    skills: list[str] = Field(default_factory=list, max_length=16)
    min_trust: int = Field(default=70, ge=0, le=95)
    description: str = Field(min_length=40, max_length=8000)
    responsibilities: list[str] = Field(default_factory=list, max_length=20)
    about: str | None = Field(default=None, max_length=2000)
    success_fee: bool = False
    company: str | None = Field(default=None, max_length=120)

    @field_validator("track")
    @classmethod
    def track_ok(cls, v: str) -> str:
        if v not in _TRACKS:
            raise ValueError("invalid track")
        return v

    @field_validator("type")
    @classmethod
    def type_job_ok(cls, v: str) -> str:
        if v not in _JOB_TYPES:
            raise ValueError("invalid type")
        return v


class ApplyIn(StrictModel):
    note: str | None = Field(default=None, max_length=2000)
    share_history: bool = True
    via: str = "manual"
    cv_object_key: str | None = Field(default=None, max_length=512)

    @field_validator("via")
    @classmethod
    def via_ok(cls, v: str) -> str:
        if v not in {"manual", "agent"}:
            raise ValueError("invalid via")
        return v


class ApplicationOut(StrictModel):
    id: str
    jobId: str
    title: str
    company: str
    appliedAt: str
    via: str
    fit: int
    status: str
    reason: str = ""
    hasCv: bool = False
    interviewScore: int | None = None
    interviewSessionId: str | None = None
    interviewSummary: str | None = None


class AgentPrefIn(StrictModel):
    enabled: bool | None = None
    threshold: int | None = Field(default=None, ge=60, le=95)


class AgentPrefOut(StrictModel):
    enabled: bool
    threshold: int


class AgentActivityOut(StrictModel):
    id: str
    jobId: str
    title: str
    company: str
    track: str
    fit: int
    at: str
    reason: str


class ConversationOut(StrictModel):
    id: str
    name: str
    avatar: str
    preview: str
    time: str
    unread: bool = False
    org: bool = False
    steel: bool = False


class ChatMessageOut(StrictModel):
    id: str
    fromMe: bool
    text: str
    time: str


class ChatSendIn(StrictModel):
    text: str = Field(min_length=1, max_length=4000)


class AssistantTurnOut(StrictModel):
    from_: str = Field(alias="from")
    text: str

    model_config = ConfigDict(extra="forbid", populate_by_name=True, ser_json_by_alias=True)


class AssistantSendIn(StrictModel):
    text: str = Field(min_length=1, max_length=4000)


class ScanCommitIn(StrictModel):
    object_key: str = Field(min_length=8, max_length=512)


class ScanCommitOut(StrictModel):
    object_key: str
    sha256: str
    status: str
    reasons: list[str] = []


class TheftClaimIn(StrictModel):
    reason: str = Field(min_length=20, max_length=2000)


class TheftResolveIn(StrictModel):
    status: str
    resolution: str = Field(min_length=8, max_length=2000)

    @field_validator("status")
    @classmethod
    def claim_status_ok(cls, v: str) -> str:
        if v not in {"upheld", "rejected"}:
            raise ValueError("invalid status")
        return v


class TheftClaimOut(StrictModel):
    id: str
    listingId: str
    listingTitle: str
    status: str
    reason: str
    resolution: str | None = None


class FeedSeller(StrictModel):
    name: str
    avatar: str
    trust: int = 0


class FeedPostOut(StrictModel):
    id: str
    type: str
    title: str
    caption: str = ""
    href: str
    priceValue: int | None = None
    verified: bool = False
    qualityScore: int = 0
    rankReason: str = ""
    score: float = 0
    seller: FeedSeller | None = None
    likes: int = 0
    comments: int = 0
    meta: str = ""


class FeedEventIn(StrictModel):
    post_key: str = Field(min_length=3, max_length=160)
    kind: str = "click"

    @field_validator("kind")
    @classmethod
    def event_ok(cls, v: str) -> str:
        if v not in {"click", "hide"}:
            raise ValueError("invalid event")
        return v


class InterviewTaskOut(StrictModel):
    prompt: str
    timeLimitSec: int
    attemptId: str | None = None
    status: str = "ready"


class InterviewSubmitIn(StrictModel):
    object_key: str | None = Field(default=None, max_length=512)
    prompt_text: str | None = Field(default=None, max_length=8000)


class InterviewScoreOut(StrictModel):
    attemptId: str
    score: int
    status: str
    scorecard: list[dict] = []
    timeLimitSec: int


class VideoQuestionOut(StrictModel):
    id: str
    prompt: str


class VideoAnswerIn(StrictModel):
    question_id: str = Field(min_length=8, max_length=36)
    object_key: str = Field(min_length=8, max_length=512)
    consent: bool
    transcript: str | None = Field(default=None, max_length=8000)


class VideoAnswerOut(StrictModel):
    questionId: str
    status: str
    retainUntil: str
    transcript: str | None = None


class ApplicantRankOut(StrictModel):
    id: str
    name: str
    trust: int
    sales: int
    fit: int
    reason: str
    status: str
    hasCv: bool = False
    interviewScore: int | None = None
    interviewSessionId: str | None = None
    interviewSummary: str | None = None


class InterviewerLicenseOut(StrictModel):
    listingId: str
    plan: str
    status: str
    turnsUsed: int
    turnsCap: int
    expiresAt: str
    hosted: bool = True


class InterviewerDocOut(StrictModel):
    id: str
    filename: str
    chunks: int


class InterviewerDocIn(StrictModel):
    object_key: str = Field(min_length=8, max_length=512)


class InterviewerSessionIn(StrictModel):
    listing_slug: str = Field(default="ai-interviewer", max_length=80)
    job_slug: str | None = Field(default=None, max_length=80)
    application_id: str | None = Field(default=None, max_length=24)


class InterviewerConsentIn(StrictModel):
    consent: bool


class InterviewerTurnIn(StrictModel):
    text: str = Field(min_length=2, max_length=4000)


class InterviewerTurnOut(StrictModel):
    role: str
    text: str


class InterviewerSessionOut(StrictModel):
    id: str
    status: str
    plan: str | None = None
    jobTitle: str | None = None
    companyName: str | None = None
    candidateName: str | None = None
    consentRequired: bool = True
    disclosedAi: bool = True
    questionCount: int = 0
    score: int | None = None
    scorecard: list[dict] = []
    summary: str | None = None
    turns: list[InterviewerTurnOut] = []
    turnsLeft: int = 0
    youAreCandidate: bool = False
    youAreCompany: bool = False
    docsIndexed: int = 0
    docsHint: str = ""


class BlogMediaOut(StrictModel):
    kind: str
    url: str


class BlogCreateIn(StrictModel):
    title: str = Field(min_length=4, max_length=200)
    excerpt: str = Field(min_length=10, max_length=480)
    body: str = Field(min_length=40, max_length=40000)
    category: str = Field(default="Tech news", max_length=48)
    tags: list[str] = Field(default_factory=list, max_length=8)
    media: list[dict] = Field(default_factory=list, max_length=6)
    publish: bool = True

    @field_validator("tags")
    @classmethod
    def blog_tags_ok(cls, v: list[str]) -> list[str]:
        return [t.strip()[:32] for t in v if t and t.strip()][:8]


class BlogPostOut(StrictModel):
    id: str
    title: str
    excerpt: str
    body: str | None = None
    category: str
    tags: list[str] = []
    source: str
    sourceName: str | None = None
    sourceUrl: str | None = None
    authorName: str | None = None
    status: str
    readMinutes: int = 3
    publishedAt: str | None = None
    createdAt: str | None = None
    aiAssisted: bool = False
    coverUrl: str | None = None
    media: list[BlogMediaOut] = []


class BlogAgentRunOut(StrictModel):
    created: int
    skipped: int
    posts: list[BlogPostOut] = []
    drafts: list[BlogPostOut] = []


TokenOut.model_rebuild()
