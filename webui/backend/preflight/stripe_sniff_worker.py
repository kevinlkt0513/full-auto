"""Standalone worker: launches Playwright Firefox (Camoufox-compatible),
navigates chatgpt.com pricing, captures Stripe runtime hashes from network,
prints NDJSON lines on stdout.

NDJSON format: {"event": "<type>", "data": {...}}
Events: status (phase progress), result (final hashes), error (fatal)
"""
import json
import re
import sys
import time


def _emit(event, data):
    sys.stdout.write(json.dumps({"event": event, "data": data}) + "\n")
    sys.stdout.flush()


def main():
    _emit("status", {"phase": "navigating_pricing"})
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        _emit("error", {"reason": f"playwright import failed: {e}"})
        return 1

    version = js_checksum = rv_timestamp = None
    js_re = re.compile(r"/v3/([a-f0-9]+)\.js")
    rv_re = re.compile(r"rv=(\d+)")

    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            ctx = browser.new_context()
            page = ctx.new_page()

            def on_request(req):
                nonlocal version, js_checksum, rv_timestamp
                u = req.url
                if "js.stripe.com" in u:
                    m = js_re.search(u)
                    if m:
                        js_checksum = m.group(1)
                    m2 = rv_re.search(u)
                    if m2:
                        rv_timestamp = m2.group(1)
                if "checkout.stripe.com" in u and version is None:
                    parts = u.split("/")
                    if len(parts) > 4 and len(parts[4]) >= 8:
                        version = parts[4]

            page.on("request", on_request)
            _emit("status", {"phase": "intercepting_stripe"})
            try:
                page.goto("https://chatgpt.com/#pricing", timeout=30000)
            except Exception as e:
                _emit("error", {"reason": f"navigation failed: {e}"})
                browser.close()
                return 1

            # Give Stripe a moment to load
            for _ in range(20):
                if js_checksum and rv_timestamp:
                    break
                time.sleep(0.5)

            browser.close()
    except Exception as e:
        _emit("error", {"reason": str(e)})
        return 1

    if js_checksum and rv_timestamp:
        _emit("result", {
            "version": version or "fed52f3bc6",
            "js_checksum": js_checksum,
            "rv_timestamp": rv_timestamp,
        })
        return 0
    _emit("error", {"reason": "did not capture stripe runtime within timeout"})
    return 1


if __name__ == "__main__":
    sys.exit(main())
