import respx
from httpx import Response


def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


@respx.mock
def test_captcha_ok(client):
    _login(client)
    respx.post("https://api.example.com/createTask").mock(
        return_value=Response(200, json={"errorId": 0, "taskId": "t-1"})
    )
    r = client.post("/api/preflight/captcha", json={
        "api_url": "https://api.example.com",
        "client_key": "k",
    })
    assert r.json()["status"] == "ok"


@respx.mock
def test_captcha_bad_key(client):
    _login(client)
    respx.post("https://api.example.com/createTask").mock(
        return_value=Response(200, json={"errorId": 1, "errorDescription": "ERROR_KEY_DENIED_ACCESS"})
    )
    r = client.post("/api/preflight/captcha", json={
        "api_url": "https://api.example.com",
        "client_key": "bad",
    })
    assert r.json()["status"] == "fail"
