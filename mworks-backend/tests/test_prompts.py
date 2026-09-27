import uuid


def test_prompt_listing_requires_text_and_stays_private(client):
    seller = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    headers = {"Authorization": f"Bearer {seller.json()['access_token']}"}
    missing = client.post(
        "/v1/listings",
        headers=headers,
        json={
            "type": "prompt",
            "title": "Triage prompt UAT",
            "blurb": "A prompt pack used only to prove gated prompt delivery.",
            "description": "This listing must be rejected until the seller pastes the actual prompt text.",
            "category": "Customer Support",
            "price_value": 4000,
            "models": ["GPT-4o"],
        },
    )
    assert missing.status_code == 400
    created = client.post(
        "/v1/listings",
        headers=headers,
        json={
            "type": "prompt",
            "title": "Triage prompt UAT",
            "blurb": "A prompt pack used only to prove gated prompt delivery.",
            "description": "This listing stores prompt text that buyers see only after payment.",
            "category": "Customer Support",
            "price_value": 4000,
            "models": ["GPT-4o"],
            "prompt_text": "Classify each ticket as billing, access, or fraud. Never invent a balance.",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert "promptText" not in body
    assert "prompt_text" not in body
    slug = body["id"]
    client.post(f"/v1/listings/{slug}/publish", headers=headers)
    public = client.get(f"/v1/listings/{slug}")
    assert public.status_code == 200
    assert "promptText" not in public.json()
    buyer = client.post(
        "/v1/auth/signup",
        json={
            "name": "Prompt Buyer",
            "email": f"prompt-{uuid.uuid4().hex[:8]}@mworks.ng",
            "password": "StrongPass9",
            "role": "buyer",
        },
    )
    b_headers = {"Authorization": f"Bearer {buyer.json()['access_token']}"}
    order = client.post(f"/v1/listings/{slug}/checkout", headers=b_headers, json={"kind": "purchase"})
    ref = order.json()["id"]
    early = client.get(f"/v1/orders/{ref}/content", headers=b_headers)
    assert early.status_code == 400
    paid = client.post("/v1/payments/local/confirm", headers=b_headers, json={"reference": ref})
    assert paid.json()["hasPrompt"] is True
    got = client.get(f"/v1/orders/{ref}/content", headers=b_headers)
    assert got.status_code == 200
    assert "Never invent a balance" in got.json()["promptText"]
    peek = client.get(f"/v1/orders/{ref}/content", headers=headers)
    assert peek.status_code == 404
    unauth = client.get(f"/v1/orders/{ref}/content")
    assert unauth.status_code == 401


def test_seed_document_download_after_pay(client):
    buyer = client.post(
        "/v1/auth/signup",
        json={
            "name": "Canvas Buyer",
            "email": f"canvas-{uuid.uuid4().hex[:8]}@mworks.ng",
            "password": "StrongPass9",
            "role": "buyer",
        },
    )
    headers = {"Authorization": f"Bearer {buyer.json()['access_token']}"}
    listing = client.get("/v1/listings/rpa-opportunity-canvas")
    assert listing.status_code == 200
    assert listing.json()["hasFile"] is True
    order = client.post("/v1/listings/rpa-opportunity-canvas/checkout", headers=headers, json={"kind": "purchase"})
    ref = order.json()["id"]
    paid = client.post("/v1/payments/local/confirm", headers=headers, json={"reference": ref})
    assert paid.json()["hasDownload"] is True
    got = client.get(f"/v1/orders/{ref}/download", headers=headers)
    assert got.status_code == 200
    assert got.json()["filename"].endswith(".md")
