import platform
import shutil
import sys
from pathlib import Path
from ._common import CheckResult, PreflightResult, aggregate


def _which(binary: str) -> str | None:
    path = shutil.which(binary)
    if path:
        return path
    sibling = Path(sys.executable).with_name(binary)
    if sibling.exists():
        return str(sibling)
    return None


def check() -> PreflightResult:
    checks: list[CheckResult] = []

    # Python
    if sys.version_info >= (3, 10):
        checks.append(CheckResult(name="python", status="ok",
                                  message=f"Python {sys.version.split()[0]}"))
    else:
        checks.append(CheckResult(name="python", status="fail",
                                  message=f"Python {sys.version.split()[0]} < 3.10"))

    # Binaries
    camoufox_path = _which("camoufox")
    checks.append(CheckResult(
        name="camoufox",
        status="ok" if camoufox_path else "fail",
        message=camoufox_path or "camoufox not found in PATH",
    ))

    xvfb_path = _which("xvfb-run")
    if xvfb_path:
        checks.append(CheckResult(name="xvfb-run", status="ok", message=xvfb_path))
    elif platform.system() == "Darwin":
        checks.append(CheckResult(
            name="xvfb-run",
            status="warn",
            message="xvfb-run is Linux-only; not required on macOS",
        ))
    else:
        checks.append(CheckResult(
            name="xvfb-run",
            status="fail",
            message="xvfb-run not found in PATH",
        ))

    # Playwright import
    try:
        import playwright  # noqa: F401
        checks.append(CheckResult(name="playwright", status="ok",
                                  message="playwright importable"))
    except ImportError as e:
        checks.append(CheckResult(name="playwright", status="fail",
                                  message=str(e)))

    return aggregate(checks)
