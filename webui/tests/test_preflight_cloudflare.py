import pytest
import respx
from httpx import Response


def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


@respx.mock
def test_cloudflare_ok(client):
    _login(client)
    respx.get("https://api.cloudflare.com/client/v4/user/tokens/verify").mock(
        return_value=Response(200, json={"success": True, "result": {"status": "active"}})
    )
    respx.get("https://api.cloudflare.com/client/v4/zones?name=example.com").mock(
        return_value=Response(200, json={"success": True, "result": [{"id": "z1"}]})
    )
    r = client.post("/api/preflight/cloudflare", json={
        "cf_token": "tok",
        "zone_names": ["example.com"],
    })
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@respx.mock
def test_cloudflare_bad_token(client):
    _login(client)
    respx.get("https://api.cloudflare.com/client/v4/user/tokens/verify").mock(
        return_value=Response(401, json={"success": False, "errors": [{"code": 1000, "message": "Invalid"}]})
    )
    r = client.post("/api/preflight/cloudflare", json={
        "cf_token": "tok",
        "zone_names": ["example.com"],
    })
    assert r.json()["status"] == "fail"


@respx.mock
def test_cloudflare_zone_not_found(client):
    _login(client)
    respx.get("https://api.cloudflare.com/client/v4/user/tokens/verify").mock(
        return_value=Response(200, json={"success": True, "result": {"status": "active"}})
    )
    respx.get("https://api.cloudflare.com/client/v4/zones?name=nope.com").mock(
        return_value=Response(200, json={"success": True, "result": []})
    )
    r = client.post("/api/preflight/cloudflare", json={
        "cf_token": "tok",
        "zone_names": ["nope.com"],
    })
    assert r.json()["status"] == "fail"
