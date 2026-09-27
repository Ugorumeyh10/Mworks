import hashlib
import hmac
import json
import uuid

from app.config import Settings
from app.payments import verify_paystack_signature


def _token(client, role="buyer"):
    email = f"pay-{uuid.uuid4().hex[:10]}@mworks.ng"
    r = client.post("/v1/auth/signup", json={
        "name": "Pay Buyer",
        "email": email,
        "password": "StrongPass9",
        "role": role,
    })
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def test_checkout_pending_then_local_pay(client):
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/v1/listings/rpa-opportunity-canvas/checkout",
        headers=headers,
        json={"kind": "purchase"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["state"] == "pending_payment"
    assert body["paymentProvider"] == "local_test"
    assert "/checkout/pay/" in body["paymentUrl"]
    paid = client.post("/v1/payments/local/confirm", headers=headers, json={"reference": body["id"]})
    assert paid.status_code == 200
    assert paid.json()["state"] == "delivered"
    detail = client.get(f"/v1/orders/{body['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["counterparty"]["name"]


def test_local_pay_rejected_for_other_user(client):
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/v1/listings/support-prompts/checkout",
        headers=headers,
        json={"kind": "purchase"},
    )
    ref = created.json()["id"]
    other = client.post("/v1/auth/signup", json={
        "name": "Other",
        "email": f"other-{uuid.uuid4().hex[:8]}@mworks.ng",
        "password": "StrongPass9",
        "role": "buyer",
    })
    stolen = client.post(
        "/v1/payments/local/confirm",
        headers={"Authorization": f"Bearer {other.json()['access_token']}"},
        json={"reference": ref},
    )
    assert stolen.status_code == 404


def test_order_idor(client):
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/v1/listings/web-scraper/checkout",
        headers=headers,
        json={"kind": "purchase"},
    )
    ref = created.json()["id"]
    other = client.post("/v1/auth/signup", json={
        "name": "Nosy",
        "email": f"nosy-{uuid.uuid4().hex[:8]}@mworks.ng",
        "password": "StrongPass9",
        "role": "buyer",
    })
    peek = client.get(
        f"/v1/orders/{ref}",
        headers={"Authorization": f"Bearer {other.json()['access_token']}"},
    )
    assert peek.status_code == 404


def test_paystack_webhook_signature(client):
    settings = Settings(PAYSTACK_SECRET_KEY="sk_test_qa")
    raw = json.dumps({"event": "charge.success", "data": {"reference": "MW-NOPE"}}).encode()
    sig = hmac.new(b"sk_test_qa", raw, hashlib.sha512).hexdigest()
    assert verify_paystack_signature(settings, raw, sig)
    assert not verify_paystack_signature(settings, raw, "deadbeef")
    denied = client.post("/v1/payments/paystack/webhook", content=raw, headers={"x-paystack-signature": "nope"})
    assert denied.status_code == 401


def test_publish_own_listing(client):
    login = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    token = login.json()["access_token"]
    public_id = login.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/v1/listings",
        headers=headers,
        json={
            "type": "document",
            "title": "Publish me UAT pack",
            "blurb": "Seller publish path for QA coverage of in-review listings.",
            "description": "A pack used only to verify that a seller can publish their own in-review listing.",
            "category": "UAT",
            "price_value": 7000,
            "license": "template",
            "object_key": f"document/{public_id}/pack.pdf",
        },
    )
    slug = created.json()["id"]
    hidden = client.get(f"/v1/listings/{slug}")
    assert hidden.status_code == 404
    preview = client.get(f"/v1/listings/{slug}", headers=headers)
    assert preview.status_code == 200
    assert preview.json()["status"] == "in_review"
    stranger = client.post(
        "/v1/auth/signup",
        json={
            "name": "Other Buyer",
            "email": f"peek-{uuid.uuid4().hex[:8]}@mworks.ng",
            "password": "StrongPass9",
            "role": "buyer",
        },
    )
    peek = client.get(
        f"/v1/listings/{slug}",
        headers={"Authorization": f"Bearer {stranger.json()['access_token']}"},
    )
    assert peek.status_code == 404
    published = client.post(f"/v1/listings/{slug}/publish", headers=headers)
    assert published.status_code == 200
    assert published.json()["status"] == "live"
    live = client.get(f"/v1/listings/{slug}")
    assert live.status_code == 200
    catalog = client.get("/v1/listings")
    assert slug in {row["id"] for row in catalog.json()}


def test_s3_presign_prefers_public_endpoint():
    s = Settings(S3_ENDPOINT="http://minio:9000", S3_PUBLIC_ENDPOINT="http://localhost:9000")
    assert s.s3_presign_endpoint() == "http://localhost:9000"
