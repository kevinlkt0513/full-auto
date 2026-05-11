#!/usr/bin/env python3
"""Check whether forwarded alias addresses are visible in the IMAP inbox.

This script is intentionally read-only: it does not send email, create
accounts, or touch payment/auth flows. It only verifies whether messages
already present in the configured inbox still contain the original alias
recipient in headers that MailProvider can match.
"""
from __future__ import annotations

import argparse
import email
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config import Config  # noqa: E402
from mail_provider import MailProvider  # noqa: E402


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HEADER_FIELDS = (
    "DATE FROM TO CC DELIVERED-TO X-ORIGINAL-TO ENVELOPE-TO "
    "X-ENVELOPE-TO X-FORWARDED-TO X-ORIGINAL-RECIPIENT SUBJECT"
)


def load_aliases(path: Path) -> list[str]:
    aliases: list[str] = []
    seen: set[str] = set()
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Allow inline notes after whitespace + #.
        line = re.split(r"\s+#", line, maxsplit=1)[0].strip()
        key = line.lower()
        if not EMAIL_RE.match(line):
            raise SystemExit(f"Invalid email at {path}:{lineno}: {raw!r}")
        if key not in seen:
            seen.add(key)
            aliases.append(line)
    if not aliases:
        raise SystemExit(f"No email aliases found in {path}")
    return aliases


def fetch_header_message(conn, uid: int):
    status, msg_data = conn.uid(
        "fetch",
        str(uid),
        f"(BODY.PEEK[HEADER.FIELDS ({HEADER_FIELDS})])",
    )
    if status != "OK" or not msg_data:
        return None
    raw = b""
    for part in msg_data:
        if isinstance(part, tuple):
            raw += part[1]
    if not raw:
        return None
    return email.message_from_bytes(raw)


def scan_recent(provider: MailProvider, aliases: list[str], recent: int, show_subject: bool) -> dict[str, list[str]]:
    matches: dict[str, list[str]] = {alias: [] for alias in aliases}
    conn = None
    try:
        conn = provider._connect()
        conn.select("INBOX")
        uids = provider._search_uids(conn, "ALL")
        for uid in sorted(uids[-recent:], reverse=True):
            msg = fetch_header_message(conn, uid)
            if msg is None:
                continue
            from_value = provider._decode_header_value(msg.get("From", "")).replace("\n", " ").strip()
            date_value = provider._decode_header_value(msg.get("Date", "")).replace("\n", " ").strip()
            subject = provider._decode_header_value(msg.get("Subject", "")).replace("\n", " ").strip()
            for alias in aliases:
                if provider._match_recipient(msg, alias):
                    detail = f"uid={uid}"
                    if date_value:
                        detail += f" date={date_value}"
                    if from_value:
                        detail += f" from={from_value}"
                    if show_subject and subject:
                        detail += f" subject={subject}"
                    matches[alias].append(detail)
    finally:
        if conn is not None:
            try:
                conn.logout()
            except Exception:
                pass
    return matches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Probe whether forwarded alias addresses remain matchable in the configured IMAP inbox."
    )
    parser.add_argument(
        "--config",
        default=str(SCRIPT_DIR / "config.paypal-proxy.json"),
        help="CTF-reg JSON config containing IMAP settings.",
    )
    parser.add_argument(
        "--emails",
        required=True,
        help="Text file with one alias email address per line. Blank lines and # comments are ignored.",
    )
    parser.add_argument(
        "--recent",
        type=int,
        default=160,
        help="How many recent inbox messages to scan.",
    )
    parser.add_argument(
        "--show-subject",
        action="store_true",
        help="Include matched message subjects in output. Off by default to reduce accidental disclosure.",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config).expanduser().resolve()
    emails_path = Path(args.emails).expanduser().resolve()
    cfg = Config.from_file(str(config_path))
    aliases = load_aliases(emails_path)

    provider = MailProvider.from_config(cfg.mail)
    matches = scan_recent(provider, aliases, max(1, args.recent), args.show_subject)

    print(f"IMAP inbox: {cfg.mail.email} via {cfg.mail.imap_server}:{cfg.mail.imap_port}")
    print(f"Aliases loaded: {len(aliases)}")
    print(f"Recent messages scanned: {max(1, args.recent)}")
    print()

    ok_count = 0
    for alias in aliases:
        alias_matches = matches.get(alias) or []
        if alias_matches:
            ok_count += 1
            print(f"OK {alias} matched {len(alias_matches)} message(s)")
            for detail in alias_matches[:3]:
                print(f"  {detail}")
        else:
            print(f"MISS {alias} not found in recent message headers")

    print()
    print(f"Matched aliases: {ok_count}/{len(aliases)}")
    if ok_count < len(aliases):
        print("For misses, send a test message to that alias, wait for forwarding, then rerun this probe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
