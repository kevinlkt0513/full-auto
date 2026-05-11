import os
import textwrap
from pathlib import Path
import hashlib

import diagnose_registration_failure as diagnose


AUTH_FAILURE = textwrap.dedent(
    """
    [ERROR] 注册失败 (exit=1): RuntimeError: auth.openai.com 返回错误页 (anti-fraud-wait):
    Oops, an error occurred! Operation timed out Try again; screenshot=/tmp/browser_reg_auth_error_anti-fraud-wait.png
    """
)


def _touch(path: Path, mtime: int) -> None:
    path.write_bytes(b"png")
    os.utime(path, (mtime, mtime))


def test_parse_failure_log_identifies_auth_timeout_stage_and_screenshot():
    result = diagnose.parse_failure_log(AUTH_FAILURE, Path("logs/failure_2.log"))

    assert result.root_cause == "auth_error_page"
    assert result.stage == "anti-fraud-wait"
    assert result.operation_timed_out is True
    assert result.generic_register_timeout is False
    assert result.screenshot_paths == ("/tmp/browser_reg_auth_error_anti-fraud-wait.png",)


def test_parse_failure_log_preserves_generic_timeout_as_lower_specificity():
    result = diagnose.parse_failure_log("注册超时: child process silent")

    assert result.root_cause == "register_timeout"
    assert result.stage == "-"
    assert result.generic_register_timeout is True


def test_choose_latest_failure_log_uses_mtime(tmp_path):
    older = tmp_path / "failure_1.log"
    newer = tmp_path / "failure_2.log"
    older.write_text("old", encoding="utf-8")
    newer.write_text("new", encoding="utf-8")
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    assert diagnose.choose_latest_failure_log(tmp_path) == newer


def test_build_report_correlates_failure_screenshots_and_webui_log(tmp_path):
    failure_log = tmp_path / "failure_2.log"
    failure_screenshot = tmp_path / "browser_reg_auth_error_anti-fraud-wait.png"
    _touch(failure_screenshot, 3)
    failure_log.write_text(
        AUTH_FAILURE.replace("/tmp/browser_reg_auth_error_anti-fraud-wait.png", str(failure_screenshot)),
        encoding="utf-8",
    )
    screenshots = tmp_path / "shots"
    screenshots.mkdir()
    _touch(screenshots / "browser_reg_step_20260505_162858_BJT_001_home.png", 1)
    _touch(screenshots / "browser_reg_step_20260505_162900_BJT_002_auth_error_anti-fraud-wait.png", 2)
    webui_log = tmp_path / "webui.log"
    webui_log.write_text(
        textwrap.dedent(
            """
            INFO:     100.106.63.36:57199 - "POST /webui/api/run/start HTTP/1.1" 200 OK
            INFO:     100.106.63.36:57209 - "GET /webui/api/run/stream HTTP/1.1" 200 OK
            INFO:     100.89.13.34:45200 - "GET /webui/api/run/status HTTP/1.1" 401 Unauthorized
            """
        ),
        encoding="utf-8",
    )

    report = diagnose.build_report(
        failure_log=failure_log,
        screenshot_dir=screenshots,
        webui_log=webui_log,
        timeline_limit=12,
        access_tail=300,
        top=5,
        viewer_base_url="http://viewer.local",
    )
    expected_failure_id = hashlib.sha256(str(failure_screenshot.resolve()).encode()).hexdigest()[:20]

    assert "root_cause=auth_error_page" in report
    assert "stage=anti-fraud-wait" in report
    assert "screenshot_viewer=http://viewer.local" in report
    assert str(failure_screenshot) in report
    assert f"{failure_screenshot} exists=yes mtime_bjt=19700101_080003_BJT size_bytes=3" in report
    assert (
        f"{failure_screenshot} -> http://viewer.local/image/{expected_failure_id}/"
        "browser_reg_auth_error_anti-fraud-wait.png"
    ) in report
    assert "latest_timeline_correlation=matches_failure_stage" in report
    assert "browser_reg_step_20260505_162900_BJT_002_auth_error_anti-fraud-wait.png" in report
    assert "002 auth_error_anti-fraud-wait -> http://viewer.local/image/" in report
    assert "run_start=line:2 client:100.106.63.36 POST /webui/api/run/start -> 200" in report
    assert "auth_gate_401=line:4 client:100.89.13.34 GET /webui/api/run/status -> 401" in report


def test_timeline_correlation_warns_when_latest_sequence_is_different_run(tmp_path):
    screenshots = tmp_path / "shots"
    screenshots.mkdir()
    _touch(screenshots / "browser_reg_step_20260505_163032_BJT_001_auth_error_password-wait.png", 1)
    summary = diagnose.parse_failure_log(AUTH_FAILURE)
    entries = diagnose.latest_screenshot_entries(screenshots, limit=12)

    assert (
        diagnose.timeline_correlation(summary, entries)
        == "stage_not_in_latest_timeline latest_last_stage=auth_error_password-wait"
    )


def test_viewer_url_matches_screenshot_viewer_hashing(tmp_path):
    image = tmp_path / "browser_reg_step_20260505_162900_BJT_002_auth_error_anti-fraud-wait.png"
    _touch(image, 1)
    expected_id = hashlib.sha256(str(image.resolve()).encode()).hexdigest()[:20]

    assert diagnose.viewer_url(image, "http://viewer.local/") == (
        "http://viewer.local/image/"
        f"{expected_id}/browser_reg_step_20260505_162900_BJT_002_auth_error_anti-fraud-wait.png"
    )
