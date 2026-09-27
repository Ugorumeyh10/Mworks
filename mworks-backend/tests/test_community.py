import uuid


def _auth(client):
    login = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_jobs_board_and_apply(client):
    public = client.get("/v1/jobs")
    assert public.status_code == 200
    slugs = {row["id"] for row in public.json()}
    assert "rpa-dev-fintech" in slugs
    one = client.get("/v1/jobs/rpa-dev-fintech")
    assert one.status_code == 200
    assert one.json()["minTrust"] == 80
    denied = client.post("/v1/jobs/rpa-dev-fintech/apply", json={"share_history": True})
    assert denied.status_code == 401
    headers = _auth(client)
    again = client.post(
        "/v1/jobs/ba-automation/apply",
        headers=headers,
        json={"note": "I mapped similar close processes.", "share_history": True, "via": "manual"},
    )
    assert again.status_code == 201
    body = again.json()
    assert body["jobId"] == "ba-automation"
    assert body["status"] == "applied"
    assert 40 <= body["fit"] <= 99
    dup = client.post(
        "/v1/jobs/ba-automation/apply",
        headers=headers,
        json={"share_history": True, "via": "manual"},
    )
    assert dup.status_code == 400
    mine = client.get("/v1/me/applications", headers=headers)
    assert mine.status_code == 200
    assert any(row["jobId"] == "ba-automation" for row in mine.json())
    extra = client.post(
        "/v1/jobs",
        json={"title": "x", "track": "RPA Developer", "location": "Lagos", "description": "too short"},
    )
    assert extra.status_code == 401
    created = client.post(
        "/v1/jobs",
        headers=headers,
        json={
            "title": "RPA Developer - Internal tools",
            "track": "RPA Developer",
            "type": "Full-time",
            "location": "Remote (Nigeria)",
            "salary_min": 500000,
            "skills": ["Python", "Power Automate"],
            "min_trust": 70,
            "description": "Build and maintain internal finance automations for a Nigeria-first marketplace.",
            "responsibilities": ["Own production flows", "Write runbooks"],
            "success_fee": True,
            "company": "Mworks Hiring",
        },
    )
    assert created.status_code == 201
    assert created.json()["status"] == "live"
    assert created.json()["id"] in {row["id"] for row in client.get("/v1/jobs").json()}


def test_job_agent_activity_and_dismiss(client):
    headers = _auth(client)
    prefs = client.get("/v1/me/job-agent", headers=headers)
    assert prefs.status_code == 200
    assert prefs.json()["threshold"] == 85
    patched = client.patch("/v1/me/job-agent", headers=headers, json={"enabled": True, "threshold": 80})
    assert patched.json()["threshold"] == 80
    activity = client.get("/v1/me/job-agent/activity", headers=headers)
    assert activity.status_code == 200
    assert len(activity.json()) >= 4
    slug = activity.json()[0]["jobId"]
    dismissed = client.post(f"/v1/me/job-agent/activity/{slug}/dismiss", headers=headers)
    assert dismissed.status_code == 200


def test_messages_and_assistant_require_auth_and_persist(client):
    assert client.get("/v1/conversations").status_code == 401
    assert client.get("/v1/assistant/messages").status_code == 401
    headers = _auth(client)
    convos = client.get("/v1/conversations", headers=headers)
    assert convos.status_code == 200
    assert len(convos.json()) >= 1
    cid = convos.json()[0]["id"]
    thread = client.get(f"/v1/conversations/{cid}/messages", headers=headers)
    assert thread.status_code == 200
    sent = client.post(
        f"/v1/conversations/{cid}/messages",
        headers=headers,
        json={"text": "Can we review the delivery pack tomorrow?"},
    )
    assert sent.status_code == 201
    assert sent.json()["fromMe"] is True
    stranger = client.post(
        "/v1/auth/signup",
        json={
            "name": "Nosy Chat",
            "email": f"chat-{uuid.uuid4().hex[:8]}@mworks.ng",
            "password": "StrongPass9",
            "role": "buyer",
        },
    )
    peek = client.get(
        f"/v1/conversations/{cid}/messages",
        headers={"Authorization": f"Bearer {stranger.json()['access_token']}"},
    )
    assert peek.status_code == 404
    boot = client.get("/v1/assistant/messages", headers=headers)
    assert boot.status_code == 200
    assert boot.json()[0]["from"] == "bot"
    ask = client.post("/v1/assistant/messages", headers=headers, json={"text": "How are my listings doing?"})
    assert ask.status_code == 201
    assert ask.json()[0]["from"] == "me"
    assert ask.json()[1]["from"] == "bot"
    assert "listing" in ask.json()[1]["text"].lower()
