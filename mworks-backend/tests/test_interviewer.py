import uuid

from app.interviewer import chunk_text, opening_message, retrieve_docs
from app.models import InterviewerDoc


def test_opening_discloses_ai():
    text = opening_message()
    assert "not a human" in text.lower() or "AI Interviewer" in text


def test_chunk_and_retrieve_without_model():
    chunks = chunk_text("Keep secrets in a vault. Do not paste production credentials into a flow. Test automations in a sandbox.")
    assert chunks
    doc = InterviewerDoc(chunks=chunks)
    hit = retrieve_docs([doc], "vault secrets in flows")
    assert "vault" in hit.lower() or hit != "(none)"


def test_trial_consent_and_fallback_interview(client):
    login = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = client.get("/v1/listings/ai-interviewer")
    assert listing.status_code == 200
    assert listing.json()["type"] == "agent"
    trial = client.post("/v1/listings/ai-interviewer/trial", headers=headers)
    assert trial.status_code == 201
    assert trial.json()["plan"] == "trial"
    again = client.post("/v1/listings/ai-interviewer/trial", headers=headers)
    assert again.status_code == 201
    session = client.post("/v1/interviewer/sessions", headers=headers, json={})
    assert session.status_code == 201
    sid = session.json()["id"]
    denied = client.post(f"/v1/interviewer/sessions/{sid}/turns", headers=headers, json={"text": "I ship n8n automations and write tests."})
    assert denied.status_code == 400
    no = client.post(f"/v1/interviewer/sessions/{sid}/consent", headers=headers, json={"consent": False})
    assert no.status_code == 400
    yes = client.post(f"/v1/interviewer/sessions/{sid}/consent", headers=headers, json={"consent": True})
    assert yes.status_code == 200
    assert any("AI Interviewer" in t["text"] for t in yes.json()["turns"] if t["role"] == "agent")
    answered = client.post(
        f"/v1/interviewer/sessions/{sid}/turns",
        headers=headers,
        json={"text": "I shipped a Power Automate reconciliation flow with a sandbox test for bank files and no secrets in the XML."},
    )
    assert answered.status_code == 200
    assert answered.json()["status"] in {"in_progress", "scored"}
    assert answered.json()["turns"][-1]["role"] == "agent"


def test_trial_unauth(client):
    denied = client.post("/v1/listings/ai-interviewer/trial")
    assert denied.status_code == 401


def test_purchase_grants_hosted_license(client):
    login = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    checkout = client.post("/v1/listings/ai-interviewer/checkout", headers=headers, json={"kind": "purchase"})
    assert checkout.status_code == 201
    paid = client.post("/v1/payments/local/confirm", headers=headers, json={"reference": checkout.json()["id"]})
    assert paid.status_code == 200
    assert paid.json()["state"] == "delivered"
    assert paid.json()["hasPrompt"] is True
    license_row = client.get("/v1/interviewer/license", headers=headers)
    assert license_row.status_code == 200
    assert license_row.json()["plan"] == "purchased"
    assert license_row.json()["status"] == "active"


def test_company_invite_writes_scorecard(client):
    kudi = client.post("/v1/auth/login", json={"email": "kudi@mworks.ng", "password": "ChangeMe1a!"})
    assert kudi.status_code == 200
    kh = {"Authorization": f"Bearer {kudi.json()['access_token']}"}
    trial = client.post("/v1/listings/ai-interviewer/trial", headers=kh)
    assert trial.status_code == 201
    apps = client.get("/v1/jobs/rpa-dev-fintech/applicants", headers=kh)
    assert apps.status_code == 200
    henry_app = next(row for row in apps.json() if row["name"] == "Henry Okafor")
    invited = client.post("/v1/interviewer/sessions", headers=kh, json={"application_id": henry_app["id"]})
    assert invited.status_code == 201
    assert invited.json()["youAreCandidate"] is False
    assert invited.json()["consentRequired"] is True
    sid = invited.json()["id"]
    again = client.post("/v1/interviewer/sessions", headers=kh, json={"application_id": henry_app["id"]})
    assert again.status_code == 201
    assert again.json()["id"] == sid
    henry = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    hh = {"Authorization": f"Bearer {henry.json()['access_token']}"}
    inbox = client.get("/v1/interviewer/sessions", headers=hh)
    assert any(row["id"] == sid and row["youAreCandidate"] for row in inbox.json())
    yes = client.post(f"/v1/interviewer/sessions/{sid}/consent", headers=hh, json={"consent": True})
    assert yes.status_code == 200
    payload = {
        "text": "I shipped a Power Automate reconciliation flow with a sandbox test and secrets in a vault, never in XML."
    }
    last = None
    for _ in range(8):
        last = client.post(f"/v1/interviewer/sessions/{sid}/turns", headers=hh, json=payload)
        assert last.status_code == 200
        if last.json()["status"] == "scored":
            break
    assert last is not None and last.json()["status"] == "scored"
    ranked = client.get("/v1/jobs/rpa-dev-fintech/applicants", headers=kh)
    row = next(item for item in ranked.json() if item["id"] == henry_app["id"])
    assert row["interviewSessionId"] == sid
    assert row["interviewScore"]
    mine = client.get("/v1/me/applications", headers=hh)
    mine_app = next(item for item in mine.json() if item["id"] == henry_app["id"])
    assert mine_app["interviewScore"] == row["interviewScore"]
    assert mine_app["status"] == "interview"


def test_seller_lists_and_operates_own_agent(client):
    seller = client.post("/v1/auth/login", json={"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    headers = {"Authorization": f"Bearer {seller.json()['access_token']}"}
    missing = client.post(
        "/v1/listings",
        headers=headers,
        json={
            "type": "agent",
            "title": "Banking RPA Interviewer UAT",
            "blurb": "A hosted interviewer with a seller playbook for banking RPA screens.",
            "description": "Companies trial, buy, or hire this agent. It discloses it is AI and never impersonates a human.",
            "category": "HR & Recruiting",
            "price_value": 90000,
            "models": ["DeepSeek"],
        },
    )
    assert missing.status_code == 400
    created = client.post(
        "/v1/listings",
        headers=headers,
        json={
            "type": "agent",
            "title": "Banking RPA Interviewer UAT",
            "blurb": "A hosted interviewer with a seller playbook for banking RPA screens.",
            "description": "Companies trial, buy, or hire this agent. It discloses it is AI and never impersonates a human.",
            "category": "HR & Recruiting",
            "price_value": 90000,
            "models": ["DeepSeek"],
            "prompt_text": (
                "Ask about Power Automate testing, vaulted secrets, and sandbox bank files. "
                "Never claim to be a human recruiter. Do not make a hire decision."
            ),
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["type"] == "agent"
    assert "promptText" not in body
    assert "prompt_text" not in body
    slug = body["id"]
    published = client.post(f"/v1/listings/{slug}/publish", headers=headers)
    assert published.status_code == 200
    assert published.json()["status"] == "live"
    public = client.get(f"/v1/listings/{slug}")
    assert public.status_code == 200
    assert public.json()["type"] == "agent"
    assert "promptText" not in public.json()
    assert "prompt_text" not in public.json()
    catalog = client.get("/v1/listings?type=agent")
    assert any(row["id"] == slug for row in catalog.json())
    own_trial = client.post(f"/v1/listings/{slug}/trial", headers=headers)
    assert own_trial.status_code == 400
    license_row = client.get(f"/v1/interviewer/license?listing_slug={slug}", headers=headers)
    assert license_row.status_code == 200
    assert license_row.json()["plan"] == "seller"
    licenses = client.get("/v1/interviewer/licenses", headers=headers)
    assert any(row["listingId"] == slug and row["plan"] == "seller" for row in licenses.json())
    session = client.post("/v1/interviewer/sessions", headers=headers, json={"listing_slug": slug})
    assert session.status_code == 201
    buyer = client.post(
        "/v1/auth/signup",
        json={
            "name": "Agent Buyer",
            "email": f"agent-{uuid.uuid4().hex[:8]}@mworks.ng",
            "password": "StrongPass9",
            "role": "buyer",
        },
    )
    b_headers = {"Authorization": f"Bearer {buyer.json()['access_token']}"}
    trial = client.post(f"/v1/listings/{slug}/trial", headers=b_headers)
    assert trial.status_code == 201
    assert trial.json()["plan"] == "trial"
    assert trial.json()["listingId"] == slug
    other_session = client.post("/v1/interviewer/sessions", headers=b_headers, json={"listing_slug": slug})
    assert other_session.status_code == 201
