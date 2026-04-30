import respx
from httpx import Response


def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


@respx.mock
def test_webshare_ok(client):
    _login(client)
    respx.get("https://proxy.webshare.io/api/v2/proxy/list/").mock(
        return_value=Response(200, json={"count": 100, "results": [{"proxy_address": "1.2.3.4", "ports": {"socks5": 1080}}]})
    )
    r = client.post("/api/preflight/webshare", json={"api_key": "k"})
    body = r.json()
    assert body["status"] == "ok"


@respx.mock
def test_webshare_unauth(client):
    _login(client)
    respx.get("https://proxy.webshare.io/api/v2/proxy/list/").mock(
        return_value=Response(401, json={"detail": "Invalid token."})
    )
    r = client.post("/api/preflight/webshare", json={"api_key": "bad"})
    assert r.json()["status"] == "fail"
