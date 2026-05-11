"""Correlate registration failure logs with screenshot and WebUI evidence."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CTF_REG = ROOT / "CTF-reg"
if str(CTF_REG) not in sys.path:
    sys.path.insert(0, str(CTF_REG))

import registration_evidence  # noqa: E402
import summarize_webui_access_log  # noqa: E402


AUTH_STAGE_RE = re.compile(r"auth\.openai\.com 返回错误页 \((?P<stage>[^)]+)\)")
SCREENSHOT_RE = re.compile(r"screenshot=(?P<path>/[A-Za-z0-9_./-]+\.png)")
BROWSER_REG_PNG_RE = re.compile(r"(?P<path>/[A-Za-z0-9_./-]*browser_reg[A-Za-z0-9_./-]*\.png)")
BJT = timezone(timedelta(hours=8), "BJT")
DEFAULT_VIEWER_BASE_URL = "http://100.89.13.34:18080"


@dataclass(frozen=True)
class FailureSummary:
    log_path: Path | None
    root_cause: str
    stage: str
    operation_timed_out: bool
    generic_register_timeout: bool
    screenshot_paths: tuple[str, ...]


def choose_latest_failure_log(log_dir: Path) -> Path | None:
    candidates = [path for path in log_dir.glob("failure_*.log") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def parse_failure_log(text: str, log_path: Path | None = None) -> FailureSummary:
    stage_match = AUTH_STAGE_RE.search(text)
    operation_timed_out = "Operation timed out" in text
    generic_timeout = "注册超时" in text

    if stage_match or ("Oops, an error occurred" in text and operation_timed_out):
        root_cause = "auth_error_page"
    elif generic_timeout:
        root_cause = "register_timeout"
    elif "注册失败" in text:
        root_cause = "registration_failed"
    elif text.strip():
        root_cause = "unknown_failure"
    else:
        root_cause = "no_failure_log"

    screenshot_paths = _dedupe(
        [match.group("path") for match in SCREENSHOT_RE.finditer(text)]
        + [match.group("path") for match in BROWSER_REG_PNG_RE.finditer(text)]
    )

    return FailureSummary(
        log_path=log_path,
        root_cause=root_cause,
        stage=stage_match.group("stage") if stage_match else "-",
        operation_timed_out=operation_timed_out,
        generic_register_timeout=generic_timeout,
        screenshot_paths=tuple(screenshot_paths),
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def latest_screenshot_entries(screenshot_dir: Path, limit: int) -> list[registration_evidence.Evidence]:
    entries = registration_evidence.latest_step_sequence(
        registration_evidence.collect_evidence(screenshot_dir)
    )
    if limit > 0:
        entries = entries[-limit:]
    return entries


def format_screenshot_timeline(entries: list[registration_evidence.Evidence]) -> str:
    return registration_evidence.format_table(entries)


def format_screenshot_file_status(paths: tuple[str, ...]) -> str:
    if not paths:
        return "  none"

    rows: list[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            rows.append(f"  {raw_path} exists=no")
            continue
        stat = path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, BJT).strftime("%Y%m%d_%H%M%S_BJT")
        rows.append(f"  {raw_path} exists=yes mtime_bjt={mtime} size_bytes={stat.st_size}")
    return "\n".join(rows)


def viewer_url(path: Path, base_url: str) -> str | None:
    if not path.exists():
        return None
    resolved = str(path.resolve())
    image_id = hashlib.sha256(resolved.encode()).hexdigest()[:20]
    return f"{base_url.rstrip('/')}/image/{image_id}/{quote(path.name)}"


def format_failure_viewer_urls(paths: tuple[str, ...], base_url: str) -> str:
    if not paths:
        return "  none"

    rows: list[str] = []
    for raw_path in paths:
        url = viewer_url(Path(raw_path), base_url)
        if url is None:
            rows.append(f"  {raw_path} -> missing")
        else:
            rows.append(f"  {raw_path} -> {url}")
    return "\n".join(rows)


def format_timeline_viewer_urls(
    entries: list[registration_evidence.Evidence],
    base_url: str,
) -> str:
    if not entries:
        return "  none"

    rows: list[str] = []
    for entry in entries:
        url = viewer_url(entry.path, base_url)
        label = f"{entry.sequence:03d}" if entry.sequence is not None else "-"
        if url is None:
            rows.append(f"  {label} {entry.stage} -> missing")
        else:
            rows.append(f"  {label} {entry.stage} -> {url}")
    return "\n".join(rows)


def timeline_correlation(
    summary: FailureSummary,
    entries: list[registration_evidence.Evidence],
) -> str:
    if summary.stage == "-":
        return "not_applicable"
    if not entries:
        return "no_latest_timeline"
    for entry in entries:
        if summary.stage == entry.stage or summary.stage in entry.stage:
            return "matches_failure_stage"
    return f"stage_not_in_latest_timeline latest_last_stage={entries[-1].stage}"


def format_webui_summary(webui_log: Path, tail: int, top: int) -> str:
    if not webui_log.exists():
        return f"webui_log=missing path:{webui_log}"

    text = webui_log.read_text(encoding="utf-8", errors="replace")
    if tail > 0:
        text = "\n".join(text.splitlines()[-tail:])
    events = summarize_webui_access_log.parse_access_events(text)
    return summarize_webui_access_log.format_summary(
        summarize_webui_access_log.summarize_events(events),
        top=top,
    )


def build_report(
    failure_log: Path | None,
    screenshot_dir: Path,
    webui_log: Path,
    timeline_limit: int,
    access_tail: int,
    top: int,
    viewer_base_url: str = DEFAULT_VIEWER_BASE_URL,
) -> str:
    failure_text = ""
    if failure_log is not None:
        failure_text = failure_log.read_text(encoding="utf-8", errors="replace")
    summary = parse_failure_log(failure_text, failure_log)
    screenshot_entries = latest_screenshot_entries(screenshot_dir, timeline_limit)

    lines = [
        "registration_failure_report",
        f"failure_log={summary.log_path if summary.log_path else 'none'}",
        f"root_cause={summary.root_cause}",
        f"stage={summary.stage}",
        f"operation_timed_out={'yes' if summary.operation_timed_out else 'no'}",
        f"generic_register_timeout={'yes' if summary.generic_register_timeout else 'no'}",
        f"screenshot_viewer={viewer_base_url.rstrip('/')}",
        "screenshots:",
    ]
    if summary.screenshot_paths:
        lines.extend(f"  {path}" for path in summary.screenshot_paths)
    else:
        lines.append("  none")

    lines.extend(
        [
            "failure_screenshot_files:",
            format_screenshot_file_status(summary.screenshot_paths),
            "failure_screenshot_viewer_urls:",
            format_failure_viewer_urls(summary.screenshot_paths, viewer_base_url),
            f"latest_timeline_correlation={timeline_correlation(summary, screenshot_entries)}",
            "latest_registration_screenshots:",
            format_screenshot_timeline(screenshot_entries),
            "latest_timeline_viewer_urls:",
            format_timeline_viewer_urls(screenshot_entries, viewer_base_url),
            "webui_access_summary:",
            format_webui_summary(webui_log, access_tail, top),
            "interpretation:",
            _interpret(summary),
            "safe_next_checks:",
            "  - Open the listed screenshots through the Tailscale screenshot viewer.",
            "  - If root_cause=auth_error_page, inspect proxy egress, DNS latency, and domain pool health before retrying.",
            "  - If root_cause=register_timeout with no auth screenshot, inspect child-process liveness and registration timeout settings.",
        ]
    )
    return "\n".join(lines)


def _interpret(summary: FailureSummary) -> str:
    if summary.root_cause == "auth_error_page":
        return (
            "  auth.openai.com returned an error page during browser registration; "
            "this is earlier than OTP/IMAP handling and should not be treated as a mail timeout."
        )
    if summary.root_cause == "register_timeout":
        return "  registration exceeded the outer timeout without a more specific browser-side root cause."
    if summary.root_cause == "no_failure_log":
        return "  no failure log was available for diagnosis."
    return "  failure log did not match a known registration timeout signature."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose the latest registration failure from offline evidence."
    )
    parser.add_argument("--failure-log", help="specific failure_*.log file to inspect")
    parser.add_argument("--log-dir", default="logs", help="directory used to find latest failure_*.log")
    parser.add_argument("--screenshot-dir", default="/tmp", help="directory containing browser_reg screenshots")
    parser.add_argument("--webui-log", default="output/webui.log", help="WebUI access log path")
    parser.add_argument("--timeline-limit", type=int, default=12, help="latest screenshot rows to print")
    parser.add_argument("--access-tail", type=int, default=300, help="latest WebUI access-log lines to inspect")
    parser.add_argument("--top", type=int, default=8, help="top WebUI routes to print")
    parser.add_argument(
        "--viewer-base-url",
        default=DEFAULT_VIEWER_BASE_URL,
        help="base URL for screenshot viewer links",
    )
    args = parser.parse_args(argv)

    if args.failure_log:
        failure_log = Path(args.failure_log)
        if not failure_log.exists():
            parser.error(f"failure log not found: {failure_log}")
    else:
        failure_log = choose_latest_failure_log(Path(args.log_dir))

    print(
        build_report(
            failure_log=failure_log,
            screenshot_dir=Path(args.screenshot_dir),
            webui_log=Path(args.webui_log),
            timeline_limit=args.timeline_limit,
            access_tail=args.access_tail,
            top=args.top,
            viewer_base_url=args.viewer_base_url,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
