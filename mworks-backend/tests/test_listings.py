def test_public_catalog_includes_documents(client):
    r = client.get("/v1/listings")
    assert r.status_code == 200
    rows = r.json()
    types = {row["type"] for row in rows}
    assert "automation" in types
    assert "document" in types
    slugs = {row["id"] for row in rows}
    assert "invoice-bot" in slugs
    assert "rpa-opportunity-canvas" in slugs
    assert "ai-interviewer" in slugs
    assert "agent" in types


def test_get_listing_by_slug(client):
    r = client.get("/v1/listings/c4-architecture-pack")
    assert r.status_code == 200
    assert r.json()["category"] == "Architecture"
    assert r.json()["license"] == "template"


def test_missing_listing(client):
    r = client.get("/v1/listings/does-not-exist")
    assert r.status_code == 404


def test_revise_requires_auth(client):
    r = client.post("/v1/listings/rpa-opportunity-canvas/checkout", json={"kind": "revise", "brief": "Adapt to payroll."})
    assert r.status_code == 401


def test_revise_checkout_and_cap(client):
    c = client
    login = c.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    over = c.post(
        "/v1/listings/rpa-opportunity-canvas/checkout",
        headers=headers,
        json={"kind": "revise", "brief": "Adapt to payroll.", "budget": 80000},
    )
    assert over.status_code == 400
    ok = c.post(
        "/v1/listings/rpa-opportunity-canvas/checkout",
        headers=headers,
        json={"kind": "revise", "brief": "Adapt the canvas to a payroll close process.", "budget": 15000},
    )
    assert ok.status_code == 201
    body = ok.json()
    assert body["kind"] == "revise"
    assert body["amount"] == 15000
    assert body["state"] == "pending_payment"
    assert body["paymentUrl"]
    held = c.post(
        "/v1/payments/local/confirm",
        headers=headers,
        json={"reference": body["id"]},
    )
    assert held.status_code == 200
    assert held.json()["state"] == "funds_held"
    mine = c.get("/v1/orders", headers=headers)
    assert mine.status_code == 200
    assert any(o["id"] == body["id"] for o in mine.json())
