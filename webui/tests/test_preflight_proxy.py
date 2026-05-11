from webui.backend.preflight import proxy as proxy_check


def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


def test_proxy_ok_country_match(client, monkeypatch):
    _login(client)
    monkeypatch.setattr(proxy_check, "_fetch_exit_ip", lambda _url: "1.2.3.4")
    monkeypatch.setattr(proxy_check, "_fetch_geo", lambda _ip: {
        "status": "success", "countryCode": "US", "country": "United States",
    })
    r = client.post("/api/preflight/proxy", json={
        "mode": "manual",
        "url": "http://proxy.example:8080",
        "expected_country": "US",
    })
    assert r.json()["status"] == "ok"


def test_proxy_country_mismatch(client, monkeypatch):
    _login(client)
    monkeypatch.setattr(proxy_check, "_fetch_exit_ip", lambda _url: "1.2.3.4")
    monkeypatch.setattr(proxy_check, "_fetch_geo", lambda _ip: {
        "status": "success", "countryCode": "DE", "country": "Germany",
    })
    r = client.post("/api/preflight/proxy", json={
        "mode": "manual",
        "url": "http://proxy.example:8080",
        "expected_country": "US",
    })
    assert r.json()["status"] == "warn"


def test_proxy_mode_none(client):
    _login(client)
    r = client.post("/api/preflight/proxy", json={"mode": "none"})
    assert r.json()["status"] == "ok"


def test_proxy_normalizes_user_at_password_format(client, monkeypatch):
    _login(client)
    seen = {}

    def fake_fetch_exit_ip(url):
        seen["url"] = url
        return "1.2.3.4"

    monkeypatch.setattr(proxy_check, "_fetch_exit_ip", fake_fetch_exit_ip)
    monkeypatch.setattr(proxy_check, "_fetch_geo", lambda _ip: {
        "status": "success", "countryCode": "US", "country": "United States",
    })
    monkeypatch.setattr(proxy_check, "_port_listening", lambda _port: True)
    r = client.post("/api/preflight/proxy", json={
        "mode": "manual",
        "url": "socks5://proxyuser@password@127.0.0.1:21080",
        "expected_country": "US",
    })

    assert r.json()["status"] == "ok"
    assert seen["url"] == "socks5://proxyuser:password@127.0.0.1:21080"
