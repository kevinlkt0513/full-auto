import textwrap

import summarize_webui_access_log as summary


SAMPLE_LOG = textwrap.dedent(
    """
    INFO:     100.106.63.36:57199 - "GET /webui/api/run/status HTTP/1.1" 200 OK
    INFO:     100.106.63.36:57199 - "POST /webui/api/run/start HTTP/1.1" 200 OK
    INFO:     100.106.63.36:57209 - "GET /webui/api/run/stream HTTP/1.1" 200 OK
    INFO:     100.89.13.34:45172 - "GET /api/healthz HTTP/1.1" 200 OK
    INFO:     100.89.13.34:45200 - "GET /webui/api/run/status HTTP/1.1" 401 Unauthorized
    """
)


def test_parse_access_events_extracts_method_path_and_status():
    events = summary.parse_access_events(SAMPLE_LOG)

    assert len(events) == 5
    assert events[1].method == "POST"
    assert events[1].path == "/webui/api/run/start"
    assert events[1].status == 200


def test_summarize_events_finds_latest_run_and_auth_gate():
    result = summary.summarize_events(summary.parse_access_events(SAMPLE_LOG))

    assert result["run_start"].path == "/webui/api/run/start"
    assert result["run_stream"].path == "/webui/api/run/stream"
    assert result["healthz"].status == 200
    assert result["auth_gate_401"].status == 401


def test_format_summary_is_stable_and_human_readable():
    text = summary.format_summary(summary.summarize_events(summary.parse_access_events(SAMPLE_LOG)))

    assert "total_access_events=5" in text
    assert "run_start=line:3 client:100.106.63.36 POST /webui/api/run/start -> 200" in text
    assert "auth_gate_401=line:6 client:100.89.13.34 GET /webui/api/run/status -> 401" in text
    assert "top_routes:" in text
