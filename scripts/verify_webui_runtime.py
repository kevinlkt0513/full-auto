"""Read-only checks for the WebUI runtime and auth gate."""
from __future__ import annotations

import argparse
import shlex
import socket
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WebuiEndpoint:
    host: str
    port: int


def parse_exec_start_endpoint(unit_text: str) -> WebuiEndpoint:
    for raw_line in unit_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("ExecStart="):
            continue
        parts = shlex.split(line.split("=", 1)[1])
        host = _option_value(parts, "--host")
        port = _option_value(parts, "--port")
        if host and port:
            return WebuiEndpoint(host=host, port=int(port))
    raise ValueError("ExecStart does not contain --host and --port")


def _option_value(parts: list[str], option: str) -> str | None:
    for index, part in enumerate(parts):
        if part == option and index + 1 < len(parts):
            return parts[index + 1]
        if part.startswith(f"{option}="):
            return part.split("=", 1)[1]
    return None


def is_tailscale_host(host: str) -> bool:
    return host.startswith("100.")


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


def read_service_state(service: str) -> str:
    result = subprocess.run(
        ["systemctl", "is-active", service],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return (result.stdout or result.stderr).strip() or "unknown"


def tcp_connects(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_status(url: str, timeout: float = 3.0) -> int:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify WebUI is Tailscale-bound, reachable, and auth protected."
    )
    parser.add_argument("--service", default="444-webui.service")
    parser.add_argument("--service-file", help="read unit text from a file instead of systemctl")
    parser.add_argument("--health-path", default="/api/healthz")
    parser.add_argument("--protected-path", default="/webui/api/run/status")
    args = parser.parse_args(argv)

    unit_text = read_unit_text(args.service, args.service_file)
    endpoint = parse_exec_start_endpoint(unit_text)
    if not is_tailscale_host(endpoint.host):
        print(f"webui host is not a Tailscale 100.x address: {endpoint.host}")
        return 1

    state = read_service_state(args.service) if not args.service_file else "not-checked"
    if not tcp_connects(endpoint.host, endpoint.port):
        print(f"webui runtime unreachable: {endpoint.host}:{endpoint.port} service_state={state}")
        return 1

    base_url = f"http://{endpoint.host}:{endpoint.port}"
    health = http_status(base_url + args.health_path)
    protected = http_status(base_url + args.protected_path)
    if health != 200:
        print(f"webui health check failed: {args.health_path} -> {health}")
        return 1
    if protected != 401:
        print(f"webui auth gate unexpected: {args.protected_path} -> {protected}")
        return 1

    print(
        "webui runtime ok: "
        f"service_state={state} endpoint={endpoint.host}:{endpoint.port} "
        f"health={health} protected_noauth={protected}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
