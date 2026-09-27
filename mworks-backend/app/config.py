from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "db"}


class Settings(BaseSettings):
    """Declared settings only. Unknown env keys are ignored so OpenShift extras cannot crash the pod."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    APP_ENV: str = "local"
    APP_NAME: str = "mworks-api"
    CORS_ORIGINS: str = "http://localhost:5173"

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "mworks"
    DB_USER: str = "mworks"
    DB_PASSWORD: str = ""
    DB_SSLMODE: str = ""

    JWT_ISS: str = "mworks"
    JWT_AUD: str = "mworks-web"
    JWT_PRIVATE_KEY_PATH: str = "./secrets/jwt_private.pem"
    JWT_PUBLIC_KEY_PATH: str = "./secrets/jwt_public.pem"
    JWT_ACCESS_MINUTES: int = 15
    JWT_REFRESH_DAYS: int = 7

    REDIS_URL: str = "redis://localhost:6379/0"

    S3_ENDPOINT: str = "http://localhost:9000"
    S3_PUBLIC_ENDPOINT: str = ""
    S3_BUCKET: str = "mworks"
    S3_ACCESS_KEY: str = "mworks"
    S3_SECRET_KEY: str = ""
    S3_REGION: str = "us-east-1"

    APP_PUBLIC_URL: str = "http://localhost:5173"
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_PUBLIC_KEY: str = ""

    RATE_LIMIT_AUTH_PER_MIN: int = 5
    RATE_LIMIT_API_PER_MIN: int = 120
    JSON_BODY_MAX_BYTES: int = 1_000_000

    DEMO_USER_EMAIL: str = "henry@mworks.ng"
    DEMO_USER_PASSWORD: str = "ChangeMe1a!"

    JOB_INGEST_ENABLED: bool = True
    JOB_INGEST_INTERVAL_SEC: int = 30
    JOB_INGEST_MAX_NEW: int = 40
    # Greenhouse values are public career-page slugs (boards.greenhouse.io/{slug}),
    # not secret API keys. Only include boards that return HTTP 200.
    JOB_INGEST_SOURCES: str = (
        "greenhouse:anthropic,greenhouse:databricks,greenhouse:xai,"
        "greenhouse:scaleai,greenhouse:togetherai,greenhouse:dataiku,"
        "greenhouse:stripe,greenhouse:gitlab,greenhouse:cloudflare,"
        "greenhouse:mongodb,greenhouse:elastic,greenhouse:datadog,"
        "greenhouse:figma,greenhouse:vercel,greenhouse:okta,arbeitnow"
    )

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/anthropic"
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"
    DEEPSEEK_MODEL_FAST: str = "deepseek-v4-flash"

    CLAMD_HOST: str = ""
    CLAMD_PORT: int = 3310
    SCAN_REQUIRE_CLAMAV: bool = False
    UPLOAD_MAX_BYTES: int = 20_000_000
    VIDEO_RETAIN_DAYS: int = 90
    NEAR_DUPE_JACCARD: float = 0.85
    INTERVIEWER_TRIAL_TURNS: int = 8
    INTERVIEWER_PAID_TURNS: int = 500
    INTERVIEWER_TRIAL_DAYS: int = 14
    INTERVIEWER_MAX_QUESTIONS: int = 6

    def resolved_sslmode(self) -> str:
        raw = (self.DB_SSLMODE or "").strip().lower()
        if raw:
            return raw
        host = (self.DB_HOST or "").strip().lower()
        if host in _LOCAL_HOSTS:
            return "disable"
        return "require"

    def sqlalchemy_url(self) -> str:
        if self.APP_ENV == "test":
            return "sqlite+pysqlite:///:memory:"
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        sslmode = self.resolved_sslmode()
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?sslmode={sslmode}"
        )

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def docs_enabled(self) -> bool:
        return self.APP_ENV in {"local", "test"}

    def s3_presign_endpoint(self) -> str:
        public = (self.S3_PUBLIC_ENDPOINT or "").strip()
        return public or self.S3_ENDPOINT

    def paystack_enabled(self) -> bool:
        return bool((self.PAYSTACK_SECRET_KEY or "").strip())

    def local_payments_allowed(self) -> bool:
        return self.APP_ENV in {"local", "test"}

    def job_ingest_interval(self) -> int:
        # Career-board APIs ban 1Hz crawls. 15s is the floor; 30s is the default.
        try:
            raw = int(self.JOB_INGEST_INTERVAL_SEC)
        except (TypeError, ValueError):
            raw = 30
        return max(15, min(3600, raw))

    def job_ingest_sources(self) -> list[str]:
        return [p.strip().lower() for p in (self.JOB_INGEST_SOURCES or "").split(",") if p.strip()]

    def deepseek_enabled(self) -> bool:
        return bool((self.DEEPSEEK_API_KEY or "").strip()) and self.APP_ENV != "test"

    def clamav_required(self) -> bool:
        if self.APP_ENV == "test":
            return False
        return bool(self.SCAN_REQUIRE_CLAMAV)


@lru_cache
def get_settings() -> Settings:
    return Settings()
