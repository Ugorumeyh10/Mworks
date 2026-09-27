from app.config import Settings
from app.fingerprint import bow_embed, cosine, jaccard, minhash_sig
from app.scan import EICAR, ScanFailed, scan_bytes, sniff_kind


def test_scan_rejects_executables_eicar_macros_and_secrets():
    settings = Settings(APP_ENV="test")
    mz = scan_bytes(settings, b"MZ" + b"\x00" * 20, filename="pack.bin", kind="document")
    assert any("Executable" in r for r in mz)
    eicar = scan_bytes(settings, EICAR + b"\n", filename="pack.txt", kind="document")
    assert any("Antivirus" in r for r in eicar)
    secret = scan_bytes(settings, b"api_key=sk_live_abcdefghijklmnop\n" + b"x" * 20, filename="pack.txt", kind="document")
    assert any("Credentials" in r for r in secret)
    try:
        sniff_kind("book.docm", "application/zip", "document", 12)
        raise AssertionError("macros should fail")
    except ScanFailed:
        pass
    try:
        scan_bytes(settings, b"x" * 12_000_001, filename="pack.txt", kind="document")
        raise AssertionError("oversize should fail")
    except ScanFailed as exc:
        assert exc.code == "TOO_LARGE"


def test_minhash_and_embedding_near_duplicate():
    a = minhash_sig("Power Automate reconciliation bot for bank statements and invoices in Nigeria")
    b = minhash_sig("Power Automate reconciliation bot for bank statements and invoices across Nigeria")
    c = minhash_sig("completely different prompt about customer support triage tone of voice")
    assert jaccard(a, b) >= 0.5
    assert jaccard(a, c) < 0.5
    assert cosine(bow_embed("n8n invoice bot for bank files"), bow_embed("n8n invoice bot for bank files")) > 0.99


def test_listings_include_quality_score(client):
    rows = client.get("/v1/listings").json()
    assert rows
    assert "qualityScore" in rows[0]
    scores = [r["qualityScore"] for r in rows]
    assert scores == sorted(scores, reverse=True)


def test_feed_tabs_separate_inventories(client):
    you = client.get("/v1/feed?tab=for_you")
    jobs = client.get("/v1/feed?tab=jobs")
    training = client.get("/v1/feed?tab=training")
    assert you.status_code == 200
    assert jobs.status_code == 200
    assert training.status_code == 200
    assert all(row["type"] == "job" for row in jobs.json())
    assert all(row["type"] == "training" for row in training.json())
    client.post("/v1/feed/events", json={"post_key": "listing:invoice-bot", "kind": "click"})


def test_macro_presign_blocked(client):
    login = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    token = login.json()["access_token"]
    denied = client.post(
        "/v1/uploads/presign",
        headers={"Authorization": f"Bearer {token}"},
        json={"filename": "flow.docm", "content_type": "application/zip", "kind": "package"},
    )
    assert denied.status_code == 400


def test_interview_static_scorecard_and_video_consent(client):
    login = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/v1/jobs/rpa-dev-fintech/apply", headers=headers, json={"share_history": True, "via": "manual"})
    start = client.post("/v1/jobs/rpa-dev-fintech/interview/start", headers=headers)
    assert start.status_code == 201
    scored = client.post(
        "/v1/jobs/rpa-dev-fintech/interview/submit",
        headers=headers,
        json={"prompt_text": "This automation uses n8n and includes a test for bank files."},
    )
    assert scored.status_code == 200
    assert scored.json()["score"] >= 50
    assert scored.json()["status"] == "scored"
    blocked = client.post(
        "/v1/jobs/rpa-dev-fintech/interview/start",
        headers=headers,
    )
    assert blocked.status_code == 201
    secret = client.post(
        "/v1/jobs/rpa-dev-fintech/interview/submit",
        headers=headers,
        json={"prompt_text": "api_key=sk_live_abcdefghijklmnop and automation test"},
    )
    assert secret.status_code == 200
    assert secret.json()["score"] == 0
    questions = client.get("/v1/jobs/rpa-dev-fintech/video-questions", headers=headers)
    assert questions.status_code == 200
    qid = questions.json()[0]["id"]
    no_consent = client.post(
        "/v1/jobs/rpa-dev-fintech/video-answers",
        headers=headers,
        json={"question_id": qid, "object_key": "interview_video/x/a.mp4", "consent": False},
    )
    assert no_consent.status_code == 400


def test_theft_claim_requires_auth_admin_can_list(client):
    denied = client.post(
        "/v1/listings/invoice-bot/theft-claim",
        json={"reason": "This pack copies my reconciliation zip from last year."},
    )
    assert denied.status_code == 401
    login = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    token = login.json()["access_token"]
    assert login.json()["user"]["isAdmin"] is True
    filed = client.post(
        "/v1/listings/invoice-bot/theft-claim",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "This pack copies my reconciliation zip from last year."},
    )
    assert filed.status_code == 201
    still_live = client.get("/v1/listings/invoice-bot")
    assert still_live.status_code == 200
    admin = client.get("/v1/admin/theft-claims", headers={"Authorization": f"Bearer {token}"})
    assert admin.status_code == 200
    claim_id = filed.json()["id"]
    resolved = client.post(
        f"/v1/admin/theft-claims/{claim_id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "rejected", "resolution": "Not a copy of the claimant pack."},
    )
    assert resolved.status_code == 200
