import imaplib
from pydantic import BaseModel
from ._common import CheckResult, PreflightResult, aggregate


class IMAPInput(BaseModel):
    imap_server: str
    imap_port: int = 993
    email: str
    auth_code: str


def check(body: dict) -> PreflightResult:
    cfg = IMAPInput.model_validate(body)
    try:
        conn = imaplib.IMAP4_SSL(cfg.imap_server, cfg.imap_port, timeout=15)
    except Exception as e:
        return aggregate([CheckResult(name="connect", status="fail",
                                      message=f"connect failed: {e}")])
    try:
        try:
            conn.login(cfg.email, cfg.auth_code)
        except Exception as e:
            return aggregate([CheckResult(name="login", status="fail",
                                          message=str(e))])
        return aggregate([
            CheckResult(name="connect", status="ok",
                        message=f"{cfg.imap_server}:{cfg.imap_port}"),
            CheckResult(name="login", status="ok",
                        message=f"logged in as {cfg.email}"),
        ])
    finally:
        try:
            conn.logout()
        except Exception:
            pass
