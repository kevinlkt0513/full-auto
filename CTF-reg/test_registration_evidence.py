from pathlib import Path
import os

import registration_evidence as evidence


def _touch(path: Path, mtime: int) -> None:
    path.write_bytes(b"png")
    os.utime(path, (mtime, mtime))


def test_collect_evidence_parses_step_and_legacy_files(tmp_path):
    _touch(tmp_path / "browser_reg_step_20260505_162858_BJT_001_home.png", 1)
    _touch(tmp_path / "browser_reg_auth_error_password-wait.png", 2)
    _touch(tmp_path / "not_registration.png", 3)

    rows = evidence.collect_evidence(tmp_path)

    assert [row.kind for row in rows] == ["step", "legacy"]
    assert rows[0].sequence == 1
    assert rows[0].stage == "home"
    assert rows[1].stage == "auth_error_password-wait"


def test_latest_step_sequence_uses_last_seen_sequence_start(tmp_path):
    _touch(tmp_path / "browser_reg_step_20260505_160001_BJT_001_old_start.png", 1)
    _touch(tmp_path / "browser_reg_step_20260505_160002_BJT_002_old_end.png", 2)
    _touch(tmp_path / "browser_reg_step_20260505_170001_BJT_001_new_start.png", 3)
    _touch(tmp_path / "browser_reg_step_20260505_170002_BJT_002_new_end.png", 4)

    latest = evidence.latest_step_sequence(evidence.collect_evidence(tmp_path))

    assert [row.stage for row in latest] == ["new_start", "new_end"]


def test_format_table_is_tab_separated_and_stable(tmp_path):
    _touch(tmp_path / "browser_reg_step_20260505_162858_BJT_001_home.png", 1)

    text = evidence.format_table(evidence.collect_evidence(tmp_path))

    assert text.splitlines()[0] == "kind\tseq\tstamp\tstage\tpath"
    assert "\t001\t20260505_162858_BJT\thome\t" in text
