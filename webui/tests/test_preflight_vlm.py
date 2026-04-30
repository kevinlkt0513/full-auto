import respx
from httpx import Response


def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


@respx.mock
def test_vlm_ok(client):
    _login(client)
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    )
    r = client.post("/api/preflight/vlm", json={
        "base_url": "https://api.openai.com/v1",
        "api_key": "sk-x",
        "model": "gpt-4o-mini",
    })
    assert r.json()["status"] == "ok"


@respx.mock
def test_vlm_unauth(client):
    _login(client)
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=Response(401, json={"error": {"message": "invalid"}})
    )
    r = client.post("/api/preflight/vlm", json={
        "base_url": "https://api.openai.com/v1",
        "api_key": "bad",
        "model": "gpt-4o-mini",
    })
    assert r.json()["status"] == "fail"
