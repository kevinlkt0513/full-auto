"""Camoufox-based Stripe runtime hash sniff.

run_sniff() yields dicts of {event: str, data: dict}. The route layer adapts
this to SSE. Spawns a Camoufox/Playwright subprocess, parses NDJSON stdout for
events, and yields them.
"""
import json
import subprocess
import sys
from pathlib import Path

WORKER_SCRIPT = Path(__file__).parent / "stripe_sniff_worker.py"


def run_sniff():
    """Yield {event, data} dicts. Spawns worker and parses NDJSON stdout."""
    yield {"event": "status", "data": {"phase": "launching_browser"}}
    proc = subprocess.Popen(
        [sys.executable, str(WORKER_SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            yield msg
        proc.wait(timeout=5)
        if proc.returncode != 0:
            yield {"event": "error",
                   "data": {"returncode": proc.returncode,
                            "stderr": proc.stderr.read()[:2000] if proc.stderr else ""}}
    finally:
        if proc.poll() is None:
            proc.kill()
    yield {"event": "done", "data": {}}
