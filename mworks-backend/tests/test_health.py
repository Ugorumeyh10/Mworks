def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "mworks-api"
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"


def test_ready(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"


def test_trace_method_rejected(client):
    r = client.request("TRACE", "/health")
    assert r.status_code == 405
