def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


def test_wizard_state_requires_auth(client):
    r = client.get("/api/wizard/state")
    assert r.status_code == 401


def test_wizard_state_initially_empty(client):
    _login(client)
    r = client.get("/api/wizard/state")
    assert r.status_code == 200
    assert r.json() == {"current_step": 1, "answers": {}}


def test_wizard_state_persists(client):
    _login(client)
    payload = {"current_step": 3, "answers": {"cloudflare": {"cf_token": "x"}}}
    r = client.post("/api/wizard/state", json=payload)
    assert r.status_code == 200

    r = client.get("/api/wizard/state")
    assert r.json() == payload


def test_wizard_state_partial_update(client):
    _login(client)
    client.post("/api/wizard/state", json={"current_step": 3, "answers": {"a": 1}})
    client.post("/api/wizard/state", json={"current_step": 4, "answers": {"b": 2}})
    r = client.get("/api/wizard/state")
    body = r.json()
    assert body["current_step"] == 4
    assert body["answers"] == {"b": 2}  # full replace, not merge
