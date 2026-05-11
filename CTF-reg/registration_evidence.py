"""List browser registration screenshot evidence without running the flow."""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


STEP_RE = re.compile(
    r"^browser_reg_step_"
    r"(?P<stamp>\d{8}_\d{6}_BJT)_"
    r"(?P<seq>\d{3})_"
    r"(?P<stage>[A-Za-z0-9._-]+)\.png$"
)
LEGACY_RE = re.compile(r"^browser_reg_(?P<stage>[A-Za-z0-9._-]+)\.png$")


@dataclass(frozen=True)
class Evidence:
    path: Path
    kind: str
    stage: str
    sequence: int | None
    stamp: str
    mtime: float


def _entry_from_path(path: Path) -> Evidence | None:
    step = STEP_RE.match(path.name)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    if step:
        return Evidence(
            path=path,
            kind="step",
            stage=step.group("stage"),
            sequence=int(step.group("seq")),
            stamp=step.group("stamp"),
            mtime=mtime,
        )

    legacy = LEGACY_RE.match(path.name)
    if legacy:
        return Evidence(
            path=path,
            kind="legacy",
            stage=legacy.group("stage"),
            sequence=None,
            stamp="-",
            mtime=mtime,
        )
    return None


def collect_evidence(root: Path) -> list[Evidence]:
    entries: list[Evidence] = []
    for pattern in ("browser_reg_step_*_BJT_*.png", "browser_reg_*.png"):
        for path in root.glob(pattern):
            entry = _entry_from_path(path)
            if entry and entry not in entries:
                entries.append(entry)
    return sorted(entries, key=lambda item: (item.mtime, item.sequence or 0, item.path.name))


def latest_step_sequence(entries: Iterable[Evidence]) -> list[Evidence]:
    steps = [entry for entry in entries if entry.kind == "step"]
    if not steps:
        return []

    latest_idx = max(range(len(steps)), key=lambda idx: steps[idx].mtime)
    start_idx = latest_idx
    for idx in range(latest_idx, -1, -1):
        if steps[idx].sequence == 1:
            start_idx = idx
            break
    return steps[start_idx : latest_idx + 1]


def format_table(entries: Iterable[Evidence]) -> str:
    rows = ["kind\tseq\tstamp\tstage\tpath"]
    for entry in entries:
        rows.append(
            "\t".join(
                [
                    entry.kind,
                    f"{entry.sequence:03d}" if entry.sequence is not None else "-",
                    entry.stamp,
                    entry.stage,
                    str(entry.path),
                ]
            )
        )
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List browser registration screenshots in a reproducible order."
    )
    parser.add_argument("--dir", default="/tmp", help="directory containing screenshots")
    parser.add_argument(
        "--all",
        action="store_true",
        help="show every browser_reg*.png file instead of only the latest step sequence",
    )
    parser.add_argument("--limit", type=int, default=0, help="limit rows after filtering")
    args = parser.parse_args(argv)

    entries = collect_evidence(Path(args.dir))
    selected = entries if args.all else latest_step_sequence(entries)
    if args.limit > 0:
        selected = selected[-args.limit:]

    print(format_table(selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
