def test_login_demo_user(client):
    r = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "henry@mworks.ng"
    assert "password" not in body["user"]


def test_login_unknown_email_same_shape(client):
    r = client.post("/v1/auth/login", json={"email": "nobody@mworks.ng", "password": "ChangeMe1a!"})
    assert r.status_code == 401
    assert r.json()["code"] == "AUTH_FAILED"


def test_login_wrong_password_same_shape(client):
    r = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "WrongPass1"})
    assert r.status_code == 401
    assert r.json()["code"] == "AUTH_FAILED"


def test_signup_and_me_listing_auth(client):
    c = client
    r = c.post(
        "/v1/auth/signup",
        json={
            "name": "Ada Obi",
            "email": "ada-new@mworks.ng",
            "password": "StrongPass9",
            "country": "Nigeria",
            "role": "both",
        },
    )
    assert r.status_code == 201
    token = r.json()["access_token"]
    public_id = r.json()["user"]["id"]
    denied = c.post(
        "/v1/listings",
        json={
            "type": "document",
            "title": "UAT script pack for close",
            "blurb": "Reusable UAT checklist for month-end automations.",
            "description": "A ten-page UAT script covering happy path, exceptions, and rollback for finance automations.",
            "category": "UAT",
            "price_value": 12000,
            "tags": ["UAT", "BA"],
            "license": "template",
        },
    )
    assert denied.status_code == 401
    created = c.post(
        "/v1/listings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "document",
            "title": "UAT script pack for close",
            "blurb": "Reusable UAT checklist for month-end automations.",
            "description": "A ten-page UAT script covering happy path, exceptions, and rollback for finance automations.",
            "category": "UAT",
            "price_value": 12000,
            "tags": ["UAT", "BA"],
            "license": "template",
            "object_key": f"document/{public_id}/pack.pdf",
        },
    )
    assert created.status_code == 201
    assert created.json()["type"] == "document"
    assert created.json()["id"]


def test_extra_fields_rejected(client):
    r = client.post(
        "/v1/auth/signup",
        json={
            "name": "Evil",
            "email": "evil@mworks.ng",
            "password": "StrongPass9",
            "is_admin": True,
        },
    )
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"
