import json
import time
from pathlib import Path
from urllib.parse import urlparse
from . import settings as s


CODEX_OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
DEFAULT_EMAIL_POOL_FILE = str(s.ROOT / "output" / "email_pool.txt")
DEFAULT_EMAIL_POOL_STATE_PATH = str(s.ROOT / "output" / "email_pool_state.json")


def _deep_merge(dst: dict, src: dict) -> dict:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def _backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    bak = path.with_suffix(path.suffix + f".bak.{int(time.time())}")
    bak.write_bytes(path.read_bytes())
    return bak


def _payment_method(answers: dict) -> str:
    return (answers.get("payment") or {}).get("method", "both")


def _normalize_cpa_base_url(base_url: str) -> str:
    base = (base_url or "").strip().rstrip("/")
    if base.endswith("/api"):
        base = base[:-4].rstrip("/")
    return base


def _normalize_proxy_url(proxy_url: str) -> str:
    raw = (proxy_url or "").strip()
    try:
        pp = urlparse(raw)
    except ValueError:
        return raw
    if not pp.netloc or not pp.username or pp.password is not None or "@" not in pp.username:
        return raw
    userinfo, hostinfo = pp.netloc.rsplit("@", 1)
    username, password = userinfo.split("@", 1)
    return pp._replace(netloc=f"{username}:{password}@{hostinfo}").geturl()


def _email_pool_path(value: str, default: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return default
    path = Path(raw).expanduser()
    if path.is_absolute():
        return str(path)
    return str((s.REG_CONFIG_PATH.parent / raw).resolve())


def _project_pay(answers: dict) -> dict:
    """Map flat wizard answers onto CTF-pay config schema."""
    out: dict = {}
    pm = _payment_method(answers)
    if "paypal" in answers and pm in ("paypal", "both"):
        out["paypal"] = answers["paypal"]
    if "captcha" in answers:
        out["captcha"] = {
            "api_url": answers["captcha"].get("api_url", ""),
            "api_key": answers["captcha"].get("api_key") or answers["captcha"].get("client_key", ""),
        }
    if "team_system" in answers:
        out["team_system"] = answers["team_system"]
    if "cpa" in answers:
        cpa = dict(answers["cpa"] or {})
        if cpa.get("enabled"):
            cpa["base_url"] = _normalize_cpa_base_url(cpa.get("base_url", ""))
            cpa["oauth_client_id"] = (cpa.get("oauth_client_id") or CODEX_OAUTH_CLIENT_ID).strip()
            cpa.setdefault("plan_tag", "team")
            cpa.setdefault("timeout_s", 20)
            out["cpa"] = cpa
    if pm == "gopay" and "gopay" in answers:
        gp = answers["gopay"] or {}
        if all(gp.get(k) for k in ("country_code", "phone_number", "pin")):
            out["gopay"] = {
                "country_code": str(gp["country_code"]).lstrip("+"),
                "phone_number": str(gp["phone_number"]),
                "pin": str(gp["pin"]),
            }
            if gp.get("midtrans_client_id"):
                out["gopay"]["midtrans_client_id"] = gp["midtrans_client_id"]
    if "team_plan" in answers:
        tp = answers["team_plan"] or {}
        plan: dict = {}
        for k in (
            "plan_name",
            "entry_point",
            "promo_campaign_id",
            "price_interval",
            "workspace_name",
            "seat_quantity",
            "billing_country",
            "billing_currency",
        ):
            if k in tp and tp[k] not in (None, ""):
                plan[k] = tp[k]
        if plan:
            out["fresh_checkout"] = {"plan": plan}
    if "daemon" in answers:
        out["daemon"] = answers["daemon"]
    if "stripe_runtime" in answers and pm in ("card", "both"):
        out["runtime"] = answers["stripe_runtime"]
    if "card" in answers and pm in ("card", "both"):
        out["cards"] = [answers["card"]]
    if "proxy" in answers:
        proxy = answers["proxy"]
        if proxy.get("url"):
            out["proxy"] = _normalize_proxy_url(proxy["url"])
        # webshare 段：仅 mode=webshare 且填了 api_key 才写
        if proxy.get("mode") == "webshare" and proxy.get("api_key"):
            out["webshare"] = {
                "enabled": True,
                "api_key": proxy["api_key"],
                "lock_country": proxy.get("lock_country", "US"),
                "refresh_threshold": proxy.get("refresh_threshold", 2),
                "zone_rotate_after_ip_rotations": proxy.get("zone_rotate_after_ip_rotations", 2),
                "zone_rotate_on_reg_fails": proxy.get("zone_rotate_on_reg_fails", 3),
                "no_rotation_cooldown_s": proxy.get("no_rotation_cooldown_s", 10800),
                "gost_listen_port": proxy.get("gost_listen_port", 18898),
                "sync_team_proxy": proxy.get("sync_team_proxy", True),
            }
    return out


def _project_reg(answers: dict) -> dict:
    """Map flat wizard answers onto CTF-reg config schema."""
    out: dict = {}
    pm = _payment_method(answers)
    if "imap" in answers:
        mail = dict(answers["imap"])
        mailbox = dict(answers.get("mailbox") or {})
        mailbox_mode = mailbox.get("mode", "catch_all")
        zones = (answers.get("cloudflare") or {}).get("zone_names") or []
        if mailbox_mode == "fixed_pool":
            mail["catch_all_domain"] = ""
            mail["catch_all_domains"] = []
            mail["email_pool"] = mailbox.get("email_pool") or []
            mail["email_pool_file"] = _email_pool_path(
                mailbox.get("email_pool_file"),
                DEFAULT_EMAIL_POOL_FILE,
            )
            mail["email_pool_state_path"] = _email_pool_path(
                mailbox.get("email_pool_state_path"),
                DEFAULT_EMAIL_POOL_STATE_PATH,
            )
            mail["email_pool_reuse"] = bool(mailbox.get("email_pool_reuse", False))
        else:
            catch_all_domain = (mailbox.get("catch_all_domain") or "").strip()
            if catch_all_domain:
                mail["catch_all_domain"] = catch_all_domain
            elif zones:
                # 用 cloudflare zone 作为 catch-all 域；email routing 需在 CF 那边配好转发到 mail.email
                mail["catch_all_domain"] = zones[0]
            if zones:
                mail["catch_all_domains"] = list(zones)
            mail["email_pool"] = []
            mail["email_pool_file"] = ""
            mail["email_pool_state_path"] = ""
            mail["email_pool_reuse"] = False
        out["mail"] = mail
    if "card" in answers and pm in ("card", "both"):
        out["card"] = {k: answers["card"].get(k, "") for k in ("number", "cvc", "exp_month", "exp_year")}
    if "billing" in answers:
        out["billing"] = answers["billing"]
    if "team_plan" in answers:
        out["team_plan"] = answers["team_plan"]
    if "captcha" in answers:
        out["captcha"] = {"client_key": answers["captcha"].get("client_key") or answers["captcha"].get("api_key", "")}
    if "proxy" in answers and answers["proxy"].get("url"):
        out["proxy"] = _normalize_proxy_url(answers["proxy"]["url"])
    return out


def write_configs(answers: dict) -> dict:
    """Returns {pay_path, reg_path, backups: [path, ...]}."""
    pay_skeleton = json.loads(s.PAY_EXAMPLE_PATH.read_text(encoding="utf-8"))
    reg_skeleton = json.loads(s.REG_EXAMPLE_PATH.read_text(encoding="utf-8"))

    # Skeleton 里 auto_register.config_path 默认指向 .example.json 模板（imap_server=imap.example.com 之类的占位），
    # 直接 merge 后 pipeline 子进程会读到模板 → DNS 解析占位 hostname 失败。
    # 用 wizard 实际写的真实 reg 路径覆盖它。
    auth = pay_skeleton.setdefault("fresh_checkout", {}).setdefault("auth", {})
    auto = auth.setdefault("auto_register", {})
    auto["config_path"] = str(s.REG_CONFIG_PATH)

    pay = _deep_merge(pay_skeleton, _project_pay(answers))
    reg = _deep_merge(reg_skeleton, _project_reg(answers))

    backups = []
    for p in (s.PAY_CONFIG_PATH, s.REG_CONFIG_PATH):
        b = _backup(p)
        if b:
            backups.append(str(b))

    s.PAY_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    s.REG_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    s.PAY_CONFIG_PATH.write_text(json.dumps(pay, ensure_ascii=False, indent=2), encoding="utf-8")
    s.REG_CONFIG_PATH.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "pay_path": str(s.PAY_CONFIG_PATH),
        "reg_path": str(s.REG_CONFIG_PATH),
        "backups": backups,
    }
