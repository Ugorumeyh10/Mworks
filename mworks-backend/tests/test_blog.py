import uuid


def _admin_headers(client):
    res = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _buyer_headers(client):
    res = client.post(
        "/v1/auth/signup",
        json={
            "name": "Blog Reader",
            "email": f"reader-{uuid.uuid4().hex[:8]}@mworks.ng",
            "password": "StrongPass9",
            "role": "buyer",
        },
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_public_blog_list_and_detail(client):
    res = client.get("/v1/blog")
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) >= 3
    assert all(row["status"] == "published" for row in rows)
    assert all(row.get("body") is None for row in rows)
    welcome = next(row for row in rows if row["id"] == "welcome-to-the-mworks-blog")
    assert welcome["coverUrl"] == "/keyboard-hero.jpg"
    slug = rows[0]["id"]
    detail = client.get(f"/v1/blog/{slug}")
    assert detail.status_code == 200
    assert detail.json()["body"]
    assert client.get("/v1/blog/does-not-exist").status_code == 404


def test_manual_post_requires_admin(client):
    payload = {
        "title": "Non-admin post",
        "excerpt": "This should never be created by a regular user.",
        "body": "A body long enough to pass validation for the blog create endpoint checks.",
    }
    assert client.post("/v1/blog", json=payload).status_code == 401
    assert client.post("/v1/blog", headers=_buyer_headers(client), json=payload).status_code == 403


def test_manual_create_with_media_and_unpublish(client):
    headers = _admin_headers(client)
    created = client.post(
        "/v1/blog",
        headers=headers,
        json={
            "title": "Escrow payouts explained",
            "excerpt": "How escrow releases work on Mworks, from checkout to seller payout.",
            "body": (
                "Escrow protects both sides of a marketplace order.\n\n"
                "## When funds release\n\nFunds release when the buyer confirms delivery or the "
                "auto-release window closes without a dispute."
            ),
            "category": "Product",
            "tags": ["Escrow", "Payments"],
            "media": [
                {"kind": "image", "url": "https://techcabal.com/wp-content/uploads/escrow.jpg"},
                {"kind": "youtube", "url": "https://youtu.be/dQw4w9WgXcQ"},
            ],
        },
    )
    assert created.status_code == 201
    body = created.json()
    slug = body["id"]
    assert body["status"] == "published"
    assert body["coverUrl"]
    assert any(m["kind"] == "youtube" for m in body["media"])
    assert any(row["id"] == slug for row in client.get("/v1/blog").json())

    unpublished = client.post(f"/v1/blog/{slug}/unpublish", headers=headers)
    assert unpublished.status_code == 200
    assert unpublished.json()["status"] == "draft"
    assert client.get(f"/v1/blog/{slug}").status_code == 404


def test_manual_rejects_unsafe_media(client):
    headers = _admin_headers(client)
    bad = client.post(
        "/v1/blog",
        headers=headers,
        json={
            "title": "Unsafe media",
            "excerpt": "This post should never store a javascript URL as an image.",
            "body": "A body long enough to pass validation for the blog create endpoint checks.",
            "media": [{"kind": "image", "url": "javascript:alert(1)"}],
        },
    )
    assert bad.status_code == 400


def test_news_agent_auto_publishes_with_media(client):
    headers = _admin_headers(client)
    run = client.post("/v1/blog/agent/run", headers=headers)
    assert run.status_code == 200
    data = run.json()
    assert data["created"] >= 1
    posts = data["posts"]
    assert all(row["status"] == "published" for row in posts)
    assert all(row["aiAssisted"] for row in posts)
    assert all(row["sourceUrl"] for row in posts)
    with_media = [row for row in posts if row.get("media")]
    assert with_media
    assert any(m["kind"] in {"image", "youtube", "video"} for row in with_media for m in row["media"])

    public = client.get("/v1/blog").json()
    public_ids = {row["id"] for row in public}
    assert any(row["id"] in public_ids for row in posts)

    live = client.get(f"/v1/blog/{posts[0]['id']}")
    assert live.status_code == 200
    assert live.json()["aiAssisted"] is True

    rerun = client.post("/v1/blog/agent/run", headers=headers)
    assert rerun.status_code == 200
    assert rerun.json()["created"] == 0
    assert rerun.json()["skipped"] >= 1
    assert client.post("/v1/blog/agent/run", headers=_buyer_headers(client)).status_code == 403


def test_admin_posts_listing(client):
    headers = _admin_headers(client)
    res = client.get("/v1/blog/admin/posts", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 3
    assert client.get("/v1/blog/admin/posts", headers=_buyer_headers(client)).status_code == 403
