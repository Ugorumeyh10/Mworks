from app.config import Settings
from app.ingest_jobs import classify_track, ingest_once, is_automation_role, job_copy


def test_filters_out_unrelated_roles():
    assert is_automation_role("RPA Developer - Finance")
    assert is_automation_role("Senior AI Engineer")
    assert is_automation_role("Platform owner", body="Build Power Automate flows and UiPath robots.")
    assert not is_automation_role("Remote Office Assistant")
    assert not is_automation_role("Inside Sales Contractor")
    assert classify_track("Business Analyst, Automation") == "Business Analyst"
    assert classify_track("Solution Architect, AI Platform") == "Solution Architect"


def _fetch(url: str):
    if url.endswith("/jobs"):
        return {
            "jobs": [
                {
                    "id": 101,
                    "title": "RPA Developer",
                    "absolute_url": "https://boards.greenhouse.io/huggingface/jobs/101",
                    "location": {"name": "Remote"},
                },
                {
                    "id": 102,
                    "title": "Office Coordinator",
                    "absolute_url": "https://boards.greenhouse.io/huggingface/jobs/102",
                    "location": {"name": "London"},
                },
            ]
        }
    if url.endswith("/jobs/101"):
        return {
            "id": 101,
            "title": "RPA Developer",
            "content": "<p>Own Power Automate reconciliation bots for finance ops.</p>",
            "absolute_url": "https://boards.greenhouse.io/huggingface/jobs/101",
            "location": {"name": "Remote"},
        }
    if url.endswith("/jobs/102"):
        return {"id": 102, "title": "Office Coordinator", "content": "<p>Calendar and travel.</p>"}
    if "arbeitnow" in url:
        return {"data": []}
    raise AssertionError(url)


def test_ingest_posts_new_automation_jobs_only_once(client):
    from app.db import SessionLocal
    from app.models import Job

    settings = Settings(JOB_INGEST_SOURCES="greenhouse:huggingface", JOB_INGEST_MAX_NEW=10, APP_ENV="test")
    db = SessionLocal()
    try:
        first = ingest_once(db, settings, fetch=_fetch)
        assert first["posted"] == 1
        second = ingest_once(db, settings, fetch=_fetch)
        assert second["posted"] == 0
        row = db.query(Job).filter(Job.external_key == "greenhouse:huggingface:101").one()
        assert row.title == "RPA Developer"
        assert row.source == "greenhouse"
        assert row.apply_url.endswith("/101")
        assert "<" not in row.description
        assert "Power Automate" in row.description
        assert db.query(Job).filter(Job.title == "Office Coordinator").one_or_none() is None
    finally:
        db.close()
    listed = client.get("/v1/jobs")
    assert listed.status_code == 200
    sourced = [row for row in listed.json() if row.get("source") == "greenhouse"]
    assert sourced
    assert sourced[0]["sourceUrl"]
    assert sourced[0]["verifiedEmployer"] is False
    assert "<" not in sourced[0]["description"]


def test_job_copy_strips_escaped_greenhouse_html():
    raw = (
        "&lt;div class=&quot;content-intro&quot;&gt;&lt;p&gt;GitLab is the intelligent "
        "orchestration platform for DevSecOps.&lt;/p&gt;&lt;/div&gt;"
        "&lt;h3&gt;What you’ll do&lt;/h3&gt;&lt;ul&gt;"
        "&lt;li&gt;Develop secure features for GitLab Duo Chat.&lt;/li&gt;"
        "&lt;li&gt;Implement agentic flows in Python using LangGraph.&lt;/li&gt;"
        "&lt;/ul&gt;"
        "&lt;div class=&quot;pay-range&quot;&gt;&lt;span&gt;$115,200&lt;/span&gt;"
        "&lt;span&gt; — &lt;/span&gt;&lt;span&gt;$194,400 USD&lt;/span&gt;&lt;/div&gt;"
    )
    text, items = job_copy(raw)
    assert "<" not in text
    assert "GitLab is the intelligent orchestration platform" in text
    assert "content-intro" not in text
    assert "What you’ll do" not in text
    assert items[0].startswith("Develop secure features")
    from app.ingest_jobs import pay_range

    assert pay_range(raw).startswith("$115,200")
