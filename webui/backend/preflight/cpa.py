import httpx
from pydantic import BaseModel
from ._common import CheckResult, PreflightResult, aggregate


MANAGEMENT_CONFIG_PATH = "/v0/management/config"


class CPAInput(BaseModel):
    base_url: str
    admin_key: str


def _candidate_base_urls(base_url: str) -> list[str]:
    base = base_url.strip().rstrip("/")
    if not base:
        return []
    candidates = []
    if base.endswith("/api"):
        candidates.append(base[:-4].rstrip("/"))
    candidates.append(base)
    return list(dict.fromkeys(candidates))


def check(body: dict) -> PreflightResult:
    cfg = CPAInput.model_validate(body)
    candidates = _candidate_base_urls(cfg.base_url)
    if not candidates:
        return aggregate([CheckResult(name="management_api", status="fail",
                                      message="base_url is required")])

    headers = {"Authorization": f"Bearer {cfg.admin_key.strip()}"}
    last_status = ""
    try:
        with httpx.Client(timeout=15.0) as c:
            for base_url in candidates:
                r = c.get(base_url + MANAGEMENT_CONFIG_PATH, headers=headers)
                if r.status_code == 200:
                    return aggregate([CheckResult(name="management_api", status="ok",
                                                  message="management api ok")])
                last_status = f"HTTP {r.status_code}"
    except httpx.HTTPError as e:
        return aggregate([CheckResult(name="management_api", status="fail",
                                      message=str(e))])
    return aggregate([CheckResult(name="management_api", status="fail",
                                  message=last_status or "management api unavailable")])
