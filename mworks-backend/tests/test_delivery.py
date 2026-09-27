def _auth(client, email="henry@mworks.ng", password="ChangeMe1a!"):
    login = client.post("/v1/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"], login.json()["user"]["id"]


def test_hire_deliver_requires_upload_and_gates_download(client):
    buyer_tok, _ = _auth(client)
    b_headers = {"Authorization": f"Bearer {buyer_tok}"}
    checkout = client.post(
        "/v1/listings/invoice-bot/checkout",
        headers=b_headers,
        json={"kind": "hire", "brief": "Map three entity bank statements into the close pack.", "budget": 180000},
    )
    assert checkout.status_code == 201
    ref = checkout.json()["id"]
    paid = client.post("/v1/payments/local/confirm", headers=b_headers, json={"reference": ref})
    assert paid.json()["state"] == "funds_held"
    assert paid.json()["hasDownload"] is False
    missing = client.post(f"/v1/orders/{ref}/deliver", headers=b_headers)
    assert missing.status_code in {403, 404, 422}
    seller_tok, seller_id = _auth(client, email="abdul@mworks.ng")
    s_headers = {"Authorization": f"Bearer {seller_tok}"}
    empty = client.post(f"/v1/orders/{ref}/deliver", headers=s_headers)
    assert empty.status_code == 422
    stolen = client.post(
        f"/v1/orders/{ref}/deliver",
        headers=s_headers,
        json={"object_key": "delivery/not-abdul/pack.zip"},
    )
    assert stolen.status_code == 400
    key = f"delivery/{seller_id}/aa11bb22-custom-work.zip"
    delivered = client.post(
        f"/v1/orders/{ref}/deliver",
        headers=s_headers,
        json={"object_key": key},
    )
    assert delivered.status_code == 200
    assert delivered.json()["state"] == "delivered"
    buyer_view = client.get(f"/v1/orders/{ref}", headers=b_headers)
    assert buyer_view.json()["hasDownload"] is True
    got = client.get(f"/v1/orders/{ref}/download", headers=b_headers)
    assert got.status_code == 200
    assert got.json()["filename"] == "custom-work.zip"
    listing_pack = client.get("/v1/listings/invoice-bot")
    assert listing_pack.status_code == 200


def test_publish_runs_verification_and_rejects_secrets(client):
    token, public_id = _auth(client)
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/v1/listings",
        headers=headers,
        json={
            "type": "prompt",
            "title": "Secret leak UAT prompt",
            "blurb": "Used to prove verification rejects credential leaks.",
            "description": "A prompt pack that must stay rejected because it embeds a live secret.",
            "category": "Customer Support",
            "price_value": 4000,
            "models": ["GPT-4o"],
            "prompt_text": "Use sk_live_forbiddensecretvalue and never share it with the buyer.",
        },
    )
    slug = created.json()["id"]
    published = client.post(f"/v1/listings/{slug}/publish", headers=headers)
    assert published.status_code == 200
    assert published.json()["status"] == "rejected"
    assert published.json()["verified"] is False
    public = client.get(f"/v1/listings/{slug}")
    assert public.status_code == 404
    ok = client.post(
        "/v1/listings",
        headers=headers,
        json={
            "type": "document",
            "title": "Verified UAT pack unique",
            "blurb": "Used to prove originality verification can pass a unique pack.",
            "description": "A unique UAT document used only to confirm verification can promote a listing live.",
            "category": "UAT",
            "price_value": 5000,
            "license": "template",
            "object_key": f"document/{public_id}/aa99-verify.md",
        },
    )
    live_slug = ok.json()["id"]
    verified = client.post(f"/v1/listings/{live_slug}/publish", headers=headers)
    assert verified.status_code == 200
    assert verified.json()["status"] == "live"
    assert verified.json()["verified"] is True
    assert any(item["label"] == "Originality check" for item in verified.json()["verificationLog"])
