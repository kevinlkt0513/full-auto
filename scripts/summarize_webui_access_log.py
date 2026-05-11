"""Summarize WebUI access-log evidence without calling live workflows."""
from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ACCESS_RE = re.compile(
    r'^(?P<prefix>.*?)'
    r'(?P<client>\d+\.\d+\.\d+\.\d+):(?P<port>\d+) - '
    r'"(?P<method>[A-Z]+) (?P<path>\S+) HTTP/[^"]+" '
    r'(?P<status>\d{3}) (?P<reason>.*)$'
)


@dataclass(frozen=True)
class AccessEvent:
    line_no: int
    client: str
    method: str
    path: str
    status: int
    raw: str


def parse_access_events(text: str) -> list[AccessEvent]:
    events: list[AccessEvent] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = ACCESS_RE.match(line.strip())
        if not match:
            continue
        events.append(
            AccessEvent(
                line_no=line_no,
                client=match.group("client"),
                method=match.group("method"),
                path=match.group("path"),
                status=int(match.group("status")),
                raw=line,
            )
        )
    return events


def summarize_events(events: list[AccessEvent]) -> dict:
    route_counts = Counter((event.method, event.path, event.status) for event in events)
    return {
        "total": len(events),
        "run_start": _last_event(events, "POST", "/webui/api/run/start"),
        "run_status": _last_event(events, "GET", "/webui/api/run/status"),
        "run_stream": _last_event(events, "GET", "/webui/api/run/stream"),
        "setup_status": _last_event(events, "GET", "/webui/api/setup/status"),
        "healthz": _last_event(events, "GET", "/api/healthz"),
        "auth_gate_401": _last_status(events, 401),
        "route_counts": route_counts,
    }


def _last_event(events: list[AccessEvent], method: str, path: str) -> AccessEvent | None:
    for event in reversed(events):
        if event.method == method and event.path == path:
            return event
    return None


def _last_status(events: list[AccessEvent], status: int) -> AccessEvent | None:
    for event in reversed(events):
        if event.status == status:
            return event
    return None


def format_summary(summary: dict, top: int = 8) -> str:
    lines = [f"total_access_events={summary['total']}"]
    for key in ("run_start", "run_status", "run_stream", "setup_status", "healthz", "auth_gate_401"):
        lines.append(_format_event(key, summary.get(key)))

    lines.append("top_routes:")
    for (method, path, status), count in summary["route_counts"].most_common(top):
        lines.append(f"  {count:4d} {method} {path} -> {status}")
    return "\n".join(lines)


def _format_event(label: str, event: AccessEvent | None) -> str:
    if event is None:
        return f"{label}=none"
    return (
        f"{label}=line:{event.line_no} client:{event.client} "
        f"{event.method} {event.path} -> {event.status}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize WebUI access-log activity for run/status diagnosis."
    )
    parser.add_argument("--log", default="output/webui.log")
    parser.add_argument("--tail", type=int, default=0, help="only inspect the last N lines")
    parser.add_argument("--top", type=int, default=8, help="number of route counts to print")
    args = parser.parse_args(argv)

    path = Path(args.log)
    text = path.read_text(encoding="utf-8", errors="replace")
    if args.tail > 0:
        text = "\n".join(text.splitlines()[-args.tail:])
    print(format_summary(summarize_events(parse_access_events(text)), top=args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
