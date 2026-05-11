def test_healthz_returns_ok(client):
    r = client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_webui_prefixed_api_routes_work(client):
    r = client.get("/webui/api/setup/status")
    assert r.status_code == 200
    assert r.json() == {"initialized": False}

    r = client.post("/webui/api/setup", json={
        "username": "admin",
        "password": "hunter2hunter2",
    })
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_webui_assets_are_served_with_javascript_mime(client, tmp_path, monkeypatch):
    import webui.server as server

    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(
        '<script type="module" src="/webui/assets/app.js"></script>',
        encoding="utf-8",
    )
    (assets / "app.js").write_text("export default 1;\n", encoding="utf-8")

    monkeypatch.setattr(server, "FRONTEND_DIST", dist)
    test_client = type(client)(server.create_app())

    r = test_client.get("/webui/assets/app.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]
    assert r.text == "export default 1;\n"
