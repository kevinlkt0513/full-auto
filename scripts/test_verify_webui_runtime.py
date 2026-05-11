import textwrap

import verify_webui_runtime as verifier


def test_parse_exec_start_endpoint_supports_split_options():
    unit_text = textwrap.dedent(
        """
        [Service]
        ExecStart=/opt/444/.venv/bin/uvicorn webui.server:create_app --factory --host 100.89.13.34 --port 8765
        """
    )

    endpoint = verifier.parse_exec_start_endpoint(unit_text)

    assert endpoint.host == "100.89.13.34"
    assert endpoint.port == 8765


def test_parse_exec_start_endpoint_supports_equals_options():
    unit_text = textwrap.dedent(
        """
        [Service]
        ExecStart=/bin/uvicorn app:create --host=100.64.0.1 --port=9000
        """
    )

    endpoint = verifier.parse_exec_start_endpoint(unit_text)

    assert endpoint.host == "100.64.0.1"
    assert endpoint.port == 9000


def test_tailscale_host_detection():
    assert verifier.is_tailscale_host("100.89.13.34")
    assert not verifier.is_tailscale_host("0.0.0.0")
    assert not verifier.is_tailscale_host("127.0.0.1")
