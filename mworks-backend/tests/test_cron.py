def test_cron_ingest_requires_secret(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "cron-test-secret")
    from app.config import get_settings

    get_settings.cache_clear()
    denied = client.get("/v1/internal/cron/ingest")
    assert denied.status_code == 401
    ok = client.get("/v1/internal/cron/ingest", headers={"Authorization": "Bearer cron-test-secret"})
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] in {"ok", "skipped"}
    get_settings.cache_clear()
