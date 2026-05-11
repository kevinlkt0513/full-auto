import time

import pytest

import pipeline


def test_register_timeout_kills_silent_child(tmp_path):
    fake_python = tmp_path / "fake-python"
    fake_python.write_text("#!/bin/sh\nsleep 30\n", encoding="utf-8")
    fake_python.chmod(0o755)

    started = time.monotonic()
    with pytest.raises(pipeline.RegistrationError, match="注册超时"):
        pipeline.register(
            tmp_path / "missing-config.json",
            python=str(fake_python),
            timeout=1,
        )

    assert time.monotonic() - started < 5


def test_registration_error_record_keeps_auth_error_tail():
    message = _long_auth_error_message()

    summary = pipeline._compact_registration_error_for_record(message)

    assert len(summary) <= 500
    assert summary.startswith("注册失败 (exit=1)")
    assert "..." in summary
    assert "auth.openai.com 返回错误页" in summary
    assert "screenshot=/tmp/browser_reg_step_20260505_163032_BJT_012_auth_error_password-wait.png" in summary


def test_registration_error_status_prefix_keeps_auth_error_tail():
    status = pipeline._registration_error_status(
        pipeline.RegistrationError(_long_auth_error_message()),
        prefix="register_error: ",
    )

    assert len(status) <= 500
    assert status.startswith("register_error: 注册失败 (exit=1)")
    assert "auth.openai.com 返回错误页" in status
    assert "auth_error_password-wait.png" in status


def test_batch_worker_error_keeps_auth_error_tail(monkeypatch):
    def fail_pipeline(card_config_path, **kwargs):
        raise pipeline.RegistrationError(_long_auth_error_message())

    monkeypatch.setattr(pipeline, "pipeline", fail_pipeline)

    result = pipeline._run_one((7, "missing-card-config.json", {}))

    assert result["batch_index"] == 7
    assert result["status"] == "error"
    assert "auth.openai.com 返回错误页" in result["error"]
    assert "auth_error_password-wait.png" in result["error"]


def test_register_worker_error_keeps_auth_error_tail(monkeypatch):
    def fail_register(cardw_config_path):
        raise pipeline.RegistrationError(_long_auth_error_message())

    monkeypatch.setattr(pipeline, "register", fail_register)

    result = pipeline._register_one((3, "missing-cardw-config.json"))

    assert result["index"] == 3
    assert result["status"] == "error"
    assert "auth.openai.com 返回错误页" in result["error"]
    assert "auth_error_password-wait.png" in result["error"]


def _long_auth_error_message():
    return "\n".join(
        [
            "注册失败 (exit=1): Traceback (most recent call last):",
            "  File \"/opt/444/CTF-reg/browser_register.py\", line 554, in browser_register",
            "    _raise_if_auth_error(\"password-wait\")",
            "  File \"/opt/444/CTF-reg/browser_register.py\", line 244, in _raise_if_auth_error",
            "    raise RuntimeError(",
            *[f"  repeated playwright wait detail {i}" for i in range(20)],
            "RuntimeError: auth.openai.com 返回错误页 (password-wait): "
            "Oops, an error occurred! Operation timed out Try again; "
            "screenshot=/tmp/browser_reg_step_20260505_163032_BJT_012_auth_error_password-wait.png",
        ]
    )
