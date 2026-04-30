def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


class _FakeIMAP:
    def __init__(self, server, port, **kwargs):
        if "fail" in server:
            raise ConnectionRefusedError("connection refused")

    def login(self, email, code):
        if code == "wrong":
            import imaplib
            raise imaplib.IMAP4.error("AUTHENTICATIONFAILED")
        return ("OK", [b"LOGIN completed"])

    def logout(self):
        return ("BYE", [])


def test_imap_ok(client, monkeypatch):
    _login(client)
    import webui.backend.preflight.imap as mod
    monkeypatch.setattr(mod.imaplib, "IMAP4_SSL", _FakeIMAP)
    r = client.post("/api/preflight/imap", json={
        "imap_server": "imap.qq.com",
        "imap_port": 993,
        "email": "x@example.com",
        "auth_code": "ok",
    })
    assert r.json()["status"] == "ok"


def test_imap_bad_auth(client, monkeypatch):
    _login(client)
    import webui.backend.preflight.imap as mod
    monkeypatch.setattr(mod.imaplib, "IMAP4_SSL", _FakeIMAP)
    r = client.post("/api/preflight/imap", json={
        "imap_server": "imap.qq.com",
        "imap_port": 993,
        "email": "x@example.com",
        "auth_code": "wrong",
    })
    assert r.json()["status"] == "fail"


def test_imap_connect_fail(client, monkeypatch):
    _login(client)
    import webui.backend.preflight.imap as mod
    monkeypatch.setattr(mod.imaplib, "IMAP4_SSL", _FakeIMAP)
    r = client.post("/api/preflight/imap", json={
        "imap_server": "fail.example.com",
        "imap_port": 993,
        "email": "x@example.com",
        "auth_code": "ok",
    })
    assert r.json()["status"] == "fail"
