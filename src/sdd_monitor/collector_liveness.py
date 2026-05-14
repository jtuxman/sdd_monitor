import re
import socket
import subprocess
from datetime import datetime, timezone
from typing import Any

from sdd_monitor.models import LivenessRecord

_PING_RE = re.compile(r"time[=<]([0-9]+(?:\.[0-9]+)?)")


def _is_liveness_target(device: dict[str, Any]) -> bool:
    return bool(device.get("liveness") or device.get("type") == "ap")


def _ping(host: str, timeout_s: int) -> tuple[bool, float | None, str | None]:
    try:
        proc = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout_s), host],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        return False, None, str(exc)

    output = f"{proc.stdout}\n{proc.stderr}"
    if proc.returncode != 0:
        return False, None, output.strip() or "ping failed"

    match = _PING_RE.search(output)
    if not match:
        return True, None, None
    return True, float(match.group(1)), None


def _check_tcp_443(host: str, timeout_s: int) -> tuple[bool, str | None]:
    try:
        with socket.create_connection((host, 443), timeout=timeout_s):
            return True, None
    except Exception as exc:
        return False, str(exc)


def collect(
    devices: list[dict[str, Any]],
    ping_timeout_s: int = 1,
    tcp_timeout_s: int = 1,
) -> list[LivenessRecord]:
    records: list[LivenessRecord] = []
    now = datetime.now(timezone.utc)

    for device in devices:
        if not _is_liveness_target(device):
            continue

        name = str(device.get("name", "unknown"))
        host = str(device.get("ip_local") or device.get("host", "")).strip()
        if not host:
            records.append(
                LivenessRecord(
                    device_name=name,
                    is_up=False,
                    ping_rtt_ms=None,
                    https_up=False,
                    error="host vacío en configuración",
                    timestamp_utc=now,
                )
            )
            continue

        ping_ok, ping_rtt, ping_err = _ping(host, ping_timeout_s)
        https_ok, https_err = _check_tcp_443(host, tcp_timeout_s)
        err = "; ".join(e for e in [ping_err, https_err] if e) or None

        records.append(
            LivenessRecord(
                device_name=name,
                is_up=bool(ping_ok or https_ok),
                ping_rtt_ms=ping_rtt,
                https_up=https_ok,
                error=err,
                timestamp_utc=now,
            )
        )

    return records
