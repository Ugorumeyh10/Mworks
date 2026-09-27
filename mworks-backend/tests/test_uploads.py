import uuid

from app.storage import owned_object_key


def test_owned_object_key_rejects_traversal():
    try:
        owned_object_key("abc", "document/abc/../secret.pdf", kinds={"document"})
        assert False
    except ValueError:
        pass
    try:
        owned_object_key("abc", "document/other/pack.pdf", kinds={"document"})
        assert False
    except ValueError:
        pass
    assert owned_object_key("abc", "document/abc/12ab-pack.pdf", kinds={"document"}).endswith("pack.pdf")


def test_document_listing_requires_file(client):
    login = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    token = login.json()["access_token"]
    missing = client.post(
        "/v1/listings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "document",
            "title": "No file UAT pack",
            "blurb": "Should fail without an uploaded object key.",
            "description": "A listing that must be rejected because the pack file was never uploaded.",
            "category": "UAT",
            "price_value": 5000,
            "license": "template",
        },
    )
    assert missing.status_code == 400
    stolen = client.post(
        "/v1/listings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "document",
            "title": "Stolen key UAT pack",
            "blurb": "Should fail if the object key belongs to someone else.",
            "description": "A listing that must be rejected because the object key is not owned by the seller.",
            "category": "UAT",
            "price_value": 5000,
            "license": "template",
            "object_key": "document/not-henry/pack.pdf",
        },
    )
    assert stolen.status_code == 400


def test_presign_requires_seller(client):
    email = f"buy-{uuid.uuid4().hex[:8]}@mworks.ng"
    r = client.post("/v1/auth/signup", json={
        "name": "Buyer Only",
        "email": email,
        "password": "StrongPass9",
        "role": "buyer",
    })
    denied = client.post(
        "/v1/uploads/presign",
        headers={"Authorization": f"Bearer {r.json()['access_token']}"},
        json={"filename": "pack.pdf", "content_type": "application/pdf", "kind": "document"},
    )
    assert denied.status_code == 403
    cv = client.post(
        "/v1/uploads/presign",
        headers={"Authorization": f"Bearer {r.json()['access_token']}"},
        json={"filename": "cv.pdf", "content_type": "application/pdf", "kind": "cv", "size_bytes": 12000},
    )
    assert cv.status_code == 200


def test_download_gated_to_paid_buyer(client):
    seller = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    s_tok = seller.json()["access_token"]
    public_id = seller.json()["user"]["id"]
    created = client.post(
        "/v1/listings",
        headers={"Authorization": f"Bearer {s_tok}"},
        json={
            "type": "document",
            "title": "Downloadable UAT pack",
            "blurb": "Used to prove gated download after escrow for a document pack.",
            "description": "A UAT pack with an attached file used only in download authorization tests.",
            "category": "UAT",
            "price_value": 6000,
            "license": "template",
            "object_key": f"document/{public_id}/pack.pdf",
        },
    )
    slug = created.json()["id"]
    client.post(f"/v1/listings/{slug}/publish", headers={"Authorization": f"Bearer {s_tok}"})
    buyer = client.post("/v1/auth/signup", json={
        "name": "File Buyer",
        "email": f"file-{uuid.uuid4().hex[:8]}@mworks.ng",
        "password": "StrongPass9",
        "role": "buyer",
    })
    b_headers = {"Authorization": f"Bearer {buyer.json()['access_token']}"}
    order = client.post(f"/v1/listings/{slug}/checkout", headers=b_headers, json={"kind": "purchase"})
    ref = order.json()["id"]
    early = client.get(f"/v1/orders/{ref}/download", headers=b_headers)
    assert early.status_code == 400
    paid = client.post("/v1/payments/local/confirm", headers=b_headers, json={"reference": ref})
    assert paid.json()["hasDownload"] is True
    got = client.get(f"/v1/orders/{ref}/download", headers=b_headers)
    assert got.status_code == 200
    assert got.json()["filename"] == "pack.pdf"
    assert "url" in got.json()
    other = client.post("/v1/auth/signup", json={
        "name": "Nosy",
        "email": f"nosy-dl-{uuid.uuid4().hex[:8]}@mworks.ng",
        "password": "StrongPass9",
        "role": "buyer",
    })
    peek = client.get(
        f"/v1/orders/{ref}/download",
        headers={"Authorization": f"Bearer {other.json()['access_token']}"},
    )
    assert peek.status_code == 404
    unauth = client.get(f"/v1/orders/{ref}/download")
    assert unauth.status_code == 401
