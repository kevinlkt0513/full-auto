def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


def test_system_preflight_returns_status(client):
    _login(client)
    r = client.post("/api/preflight/system", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "warn", "fail")
    assert "checks" in body
    names = {c["name"] for c in body["checks"]}
    assert {"python", "camoufox", "xvfb-run", "playwright"}.issubset(names)


def test_system_preflight_each_check_has_status(client):
    _login(client)
    body = client.post("/api/preflight/system", json={}).json()
    for c in body["checks"]:
        assert c["status"] in ("ok", "warn", "fail")
        assert "message" in c


def test_system_preflight_requires_auth(client):
    r = client.post("/api/preflight/system", json={})
    assert r.status_code == 401
