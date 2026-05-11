import json

from webui.backend.config_writer import DEFAULT_EMAIL_POOL_FILE, DEFAULT_EMAIL_POOL_STATE_PATH


def _login(client):
    client.post("/api/setup", json={"username": "admin", "password": "hunter2hunter2"})
    client.post("/api/login", json={"username": "admin", "password": "hunter2hunter2"})


def _seed(tmp_path, monkeypatch):
    pay_ex = tmp_path / "CTF-pay" / "config.paypal.example.json"
    reg_ex = tmp_path / "CTF-reg" / "config.paypal-proxy.example.json"
    pay_ex.parent.mkdir(parents=True)
    reg_ex.parent.mkdir(parents=True)
    pay_ex.write_text(json.dumps({"paypal": {"email": ""}, "captcha": {"api_url": "", "api_key": ""}}))
    reg_ex.write_text(json.dumps({"mail": {"imap_server": ""}, "captcha": {"client_key": ""}}))

    import webui.backend.settings as s
    monkeypatch.setattr(s, "PAY_EXAMPLE_PATH", pay_ex)
    monkeypatch.setattr(s, "REG_EXAMPLE_PATH", reg_ex)
    monkeypatch.setattr(s, "PAY_CONFIG_PATH", tmp_path / "CTF-pay" / "config.paypal.json")
    monkeypatch.setattr(s, "REG_CONFIG_PATH", tmp_path / "CTF-reg" / "config.paypal-proxy.json")


def test_export_writes_two_files(client, tmp_path, monkeypatch):
    _login(client)
    _seed(tmp_path, monkeypatch)

    answers = {
        "paypal": {"email": "you@example.com"},
        "imap": {"imap_server": "imap.qq.com"},
        "captcha": {"api_url": "https://x", "api_key": "k", "client_key": "k"},
    }
    r = client.post("/api/config/export", json={"answers": answers})
    assert r.status_code == 200

    pay = json.loads((tmp_path / "CTF-pay" / "config.paypal.json").read_text())
    reg = json.loads((tmp_path / "CTF-reg" / "config.paypal-proxy.json").read_text())
    assert pay["paypal"]["email"] == "you@example.com"
    assert pay["captcha"]["api_key"] == "k"
    assert reg["mail"]["imap_server"] == "imap.qq.com"
    assert reg["captcha"]["client_key"] == "k"


def test_export_writes_fixed_email_pool_to_reg_config(client, tmp_path, monkeypatch):
    _login(client)
    _seed(tmp_path, monkeypatch)

    answers = {
        "imap": {
            "imap_server": "imap.gmail.com",
            "imap_port": 993,
            "email": "kevin.share233@gmail.com",
            "auth_code": "app-password",
        },
        "cloudflare": {"zone_names": ["example.com"]},
        "mailbox": {
            "mode": "fixed_pool",
            "email_pool": ["alias1@example.net", "alias2@example.net"],
            "email_pool_reuse": False,
        },
    }
    r = client.post("/api/config/export", json={"answers": answers})
    assert r.status_code == 200

    reg = json.loads((tmp_path / "CTF-reg" / "config.paypal-proxy.json").read_text())
    assert reg["mail"]["email"] == "kevin.share233@gmail.com"
    assert reg["mail"]["catch_all_domain"] == ""
    assert reg["mail"]["catch_all_domains"] == []
    assert reg["mail"]["email_pool"] == ["alias1@example.net", "alias2@example.net"]
    assert reg["mail"]["email_pool_file"] == DEFAULT_EMAIL_POOL_FILE
    assert reg["mail"]["email_pool_state_path"] == DEFAULT_EMAIL_POOL_STATE_PATH
    assert reg["mail"]["email_pool_reuse"] is False


def test_export_uses_mailbox_catch_all_override(client, tmp_path, monkeypatch):
    _login(client)
    _seed(tmp_path, monkeypatch)

    answers = {
        "imap": {"imap_server": "imap.gmail.com"},
        "cloudflare": {"zone_names": ["zone-a.example", "zone-b.example"]},
        "mailbox": {
            "mode": "catch_all",
            "catch_all_domain": "mailbox.example",
            "email_pool_file": "../output/email_pool.txt",
        },
    }
    r = client.post("/api/config/export", json={"answers": answers})
    assert r.status_code == 200

    reg = json.loads((tmp_path / "CTF-reg" / "config.paypal-proxy.json").read_text())
    assert reg["mail"]["catch_all_domain"] == "mailbox.example"
    assert reg["mail"]["catch_all_domains"] == ["zone-a.example", "zone-b.example"]
    assert reg["mail"]["email_pool"] == []
    assert reg["mail"]["email_pool_file"] == ""


def test_export_writes_cpa_to_pay_config(client, tmp_path, monkeypatch):
    _login(client)
    _seed(tmp_path, monkeypatch)

    answers = {
        "cpa": {
            "enabled": True,
            "base_url": "https://cpa.example.com/api/",
            "admin_key": "management-key",
            "oauth_client_id": "",
        },
    }
    r = client.post("/api/config/export", json={"answers": answers})
    assert r.status_code == 200

    pay = json.loads((tmp_path / "CTF-pay" / "config.paypal.json").read_text())
    assert pay["cpa"]["enabled"] is True
    assert pay["cpa"]["base_url"] == "https://cpa.example.com"
    assert pay["cpa"]["admin_key"] == "management-key"
    assert pay["cpa"]["oauth_client_id"] == "app_EMoamEEZ73f0CkXaXp7hrann"
    assert pay["cpa"]["plan_tag"] == "team"
    assert pay["cpa"]["timeout_s"] == 20


def test_export_normalizes_manual_proxy_url(client, tmp_path, monkeypatch):
    _login(client)
    _seed(tmp_path, monkeypatch)

    answers = {
        "proxy": {
            "mode": "manual",
            "url": "socks5://proxyuser@password@127.0.0.1:21080",
        },
    }
    r = client.post("/api/config/export", json={"answers": answers})
    assert r.status_code == 200

    pay = json.loads((tmp_path / "CTF-pay" / "config.paypal.json").read_text())
    reg = json.loads((tmp_path / "CTF-reg" / "config.paypal-proxy.json").read_text())
    assert pay["proxy"] == "socks5://proxyuser:password@127.0.0.1:21080"
    assert reg["proxy"] == "socks5://proxyuser:password@127.0.0.1:21080"


def test_export_backs_up_existing(client, tmp_path, monkeypatch):
    _login(client)
    _seed(tmp_path, monkeypatch)

    pay_path = tmp_path / "CTF-pay" / "config.paypal.json"
    pay_path.parent.mkdir(parents=True, exist_ok=True)
    pay_path.write_text(json.dumps({"old": True}))

    client.post("/api/config/export", json={"answers": {}})

    backups = list((tmp_path / "CTF-pay").glob("config.paypal.json.bak.*"))
    assert len(backups) == 1
    assert json.loads(backups[0].read_text()) == {"old": True}


def test_export_requires_auth(client):
    r = client.post("/api/config/export", json={"answers": {}})
    assert r.status_code == 401
