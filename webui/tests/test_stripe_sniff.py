import json


def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


def _parse_sse(text: str):
    events = []
    # Handle both \r\n\r\n and \n\n delimiters
    blocks = text.strip().replace("\r\n", "\n").split("\n\n")
    for block in blocks:
        ev = {}
        for line in block.splitlines():
            if line.startswith("event:"):
                ev["event"] = line[len("event:"):].strip()
            elif line.startswith("data:"):
                ev["data"] = json.loads(line[len("data:"):].strip())
        if ev:
            events.append(ev)
    return events


def test_stripe_sniff_streams_progress(client, monkeypatch):
    _login(client)
    import webui.backend.preflight.stripe_sniff as mod

    def fake_run():
        yield {"event": "status", "data": {"phase": "launching_browser"}}
        yield {"event": "status", "data": {"phase": "navigating_pricing"}}
        yield {"event": "result", "data": {"version": "abc", "js_checksum": "JS", "rv_timestamp": "RV"}}
        yield {"event": "done", "data": {}}

    monkeypatch.setattr(mod, "run_sniff", lambda: fake_run())
    r = client.get("/api/sniff/stripe")
    assert r.status_code == 200
    events = _parse_sse(r.text)
    phases = [e["data"].get("phase") for e in events if e.get("event") == "status"]
    assert phases == ["launching_browser", "navigating_pricing"]
    result = next(e["data"] for e in events if e.get("event") == "result")
    assert result == {"version": "abc", "js_checksum": "JS", "rv_timestamp": "RV"}


def test_stripe_sniff_requires_auth(client):
    r = client.get("/api/sniff/stripe")
    assert r.status_code == 401
