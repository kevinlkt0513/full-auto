"""Verify screenshot viewer service globs are documented.

This is read-only: it reads the live systemd unit by default and checks that
the debugging runbook contains every SHOT_VIEW_GLOBS pattern.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def extract_shot_view_globs(unit_text: str) -> list[str]:
    for line in unit_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "SHOT_VIEW_GLOBS=" not in line:
            continue
        raw = line.split("SHOT_VIEW_GLOBS=", 1)[1].strip().strip('"').strip("'")
        return [part for part in raw.split(":") if part]
    return []


def read_unit_text(service: str, service_file: str | None = None) -> str:
    if service_file:
        return Path(service_file).read_text(encoding="utf-8")

    result = subprocess.run(
        ["systemctl", "cat", service],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"systemctl cat {service} failed")
    return result.stdout


def verify_docs_cover_globs(docs_text: str, globs: list[str]) -> list[str]:
    return [pattern for pattern in globs if pattern not in docs_text]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check docs/debugging.md covers screenshot-viewer SHOT_VIEW_GLOBS."
    )
    parser.add_argument("--service", default="screenshot-viewer.service")
    parser.add_argument("--service-file", help="read unit text from a file instead of systemctl")
    parser.add_argument("--docs", default="docs/debugging.md")
    args = parser.parse_args(argv)

    unit_text = read_unit_text(args.service, args.service_file)
    globs = extract_shot_view_globs(unit_text)
    if not globs:
        raise SystemExit("no SHOT_VIEW_GLOBS patterns found")

    docs_text = Path(args.docs).read_text(encoding="utf-8")
    missing = verify_docs_cover_globs(docs_text, globs)
    if missing:
        print("missing screenshot viewer docs:")
        for pattern in missing:
            print(f"- {pattern}")
        return 1

    print(f"screenshot viewer docs ok: {len(globs)} patterns covered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
