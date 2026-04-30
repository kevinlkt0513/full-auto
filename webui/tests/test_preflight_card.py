def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


def test_card_ok(client):
    _login(client)
    r = client.post("/api/preflight/card", json={
        "number": "4242424242424242", "cvc": "123",
        "exp_month": "12", "exp_year": "2030",
        "country": "US", "currency": "USD",
    })
    assert r.json()["status"] == "ok"


def test_card_bad_luhn(client):
    _login(client)
    r = client.post("/api/preflight/card", json={
        "number": "4242424242424241", "cvc": "123",
        "exp_month": "12", "exp_year": "2030",
        "country": "US", "currency": "USD",
    })
    assert r.json()["status"] == "fail"


def test_card_expired(client):
    _login(client)
    r = client.post("/api/preflight/card", json={
        "number": "4242424242424242", "cvc": "123",
        "exp_month": "01", "exp_year": "2020",
        "country": "US", "currency": "USD",
    })
    assert r.json()["status"] == "fail"


def test_card_currency_warn(client):
    _login(client)
    r = client.post("/api/preflight/card", json={
        "number": "4242424242424242", "cvc": "123",
        "exp_month": "12", "exp_year": "2030",
        "country": "US", "currency": "EUR",
    })
    assert r.json()["status"] == "warn"
