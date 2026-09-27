from app.config import Settings
from app.llm import LlmError, complete, redact


def test_redact_strips_live_keys():
    assert "[redacted]" in redact("token sk_live_abc123def")
    assert "sk_live_" not in redact("token sk_live_abc123def")


def test_complete_rejects_non_allowlisted_host():
    settings = Settings(
        APP_ENV="local",
        DEEPSEEK_API_KEY="sk-test",
        DEEPSEEK_BASE_URL="https://evil.example/anthropic",
    )
    try:
        complete(settings, system="sys", user="hi")
        raise AssertionError("expected LlmError")
    except LlmError:
        return


def test_complete_parses_text_blocks(monkeypatch):
    class Resp:
        status_code = 200

        def json(self):
            return {"content": [{"type": "text", "text": "Invoice recon is live."}]}

    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json=None, headers=None):
            assert url.startswith("https://api.deepseek.com/")
            assert headers["x-api-key"] == "sk-test"
            return Resp()

    monkeypatch.setattr("app.llm.httpx.Client", Client)
    settings = Settings(APP_ENV="local", DEEPSEEK_API_KEY="sk-test")
    assert complete(settings, system="sys", user="hi") == "Invoice recon is live."


def test_assistant_uses_llm_when_answer_returns(client, monkeypatch):
    from app.routers import assistant as ar

    monkeypatch.setattr(
        ar,
        "answer_account",
        lambda db, settings, user, text: "Grounded: your live listings are in good shape.",
    )
    signup = client.post(
        "/v1/auth/signup",
        json={
            "name": "Llm User",
            "email": "llm-user@mworks.ng",
            "password": "StrongPass9",
            "role": "both",
        },
    )
    headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}
    client.get("/v1/assistant/messages", headers=headers)
    ask = client.post("/v1/assistant/messages", headers=headers, json={"text": "Summarise my catalog."})
    assert ask.status_code == 201
    assert ask.json()[1]["text"].startswith("Grounded")
