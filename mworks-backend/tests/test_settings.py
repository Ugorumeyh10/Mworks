from app.config import Settings


def test_sslmode_local_hosts():
    for host in ("localhost", "127.0.0.1", "::1", "db"):
        s = Settings(DB_HOST=host, DB_SSLMODE="", APP_ENV="local")
        assert s.resolved_sslmode() == "disable"


def test_sslmode_remote_requires_tls():
    s = Settings(DB_HOST="pg.internal.bank.example", DB_SSLMODE="", APP_ENV="prod")
    assert s.resolved_sslmode() == "require"


def test_sslmode_explicit_wins():
    s = Settings(DB_HOST="localhost", DB_SSLMODE="require", APP_ENV="local")
    assert s.resolved_sslmode() == "require"


def test_url_includes_sslmode():
    s = Settings(
        DB_HOST="pg.example",
        DB_USER="u",
        DB_PASSWORD="p@ss",
        DB_NAME="mworks",
        DB_SSLMODE="require",
        APP_ENV="prod",
    )
    url = s.sqlalchemy_url()
    assert "sslmode=require" in url
    assert "statement_timeout" not in url
    assert "p%40ss" in url


def test_unknown_env_does_not_crash(monkeypatch):
    monkeypatch.setenv("OPENSHIFT_BOGUS", "1")
    s = Settings()
    assert s.APP_NAME
