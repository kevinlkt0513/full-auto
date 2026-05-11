import textwrap

import verify_screenshot_viewer_docs as verifier


def test_extract_shot_view_globs_from_systemd_environment_line():
    unit_text = textwrap.dedent(
        """
        [Service]
        Environment=SHOT_VIEW_GLOBS=/tmp/browser_reg*.png:/tmp/paypal_*.png:/opt/444/output/**/*.png
        """
    )

    assert verifier.extract_shot_view_globs(unit_text) == [
        "/tmp/browser_reg*.png",
        "/tmp/paypal_*.png",
        "/opt/444/output/**/*.png",
    ]


def test_verify_docs_cover_globs_reports_missing_patterns():
    missing = verifier.verify_docs_cover_globs(
        "covered /tmp/browser_reg*.png",
        ["/tmp/browser_reg*.png", "/tmp/paypal_*.png"],
    )

    assert missing == ["/tmp/paypal_*.png"]


def test_verify_docs_cover_globs_accepts_all_patterns():
    patterns = ["/tmp/browser_reg*.png", "/tmp/paypal_*.png"]

    assert verifier.verify_docs_cover_globs(" ".join(patterns), patterns) == []
