#!/home/jmanuel/sdd_monitor/.venv/bin/python3
"""CGI script: consulta on-demand de estadísticas de interfaces en switches Cisco.

Uso: GET /cgi-bin/interfaces.py?device=<nombre>
Retorna JSON con array de interfaces ordenado por tráfico total descendente.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

import yaml
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    next_cmd,
)

# OIDs ifXTable (contadores 64-bit para Cisco)
_OID_IF_NAME = "1.3.6.1.2.1.31.1.1.1.1"
_OID_HC_IN = "1.3.6.1.2.1.31.1.1.1.6"
_OID_HC_OUT = "1.3.6.1.2.1.31.1.1.1.10"
_OID_IF_ALIAS = "1.3.6.1.2.1.31.1.1.1.18"
_OID_OPER_STATUS = "1.3.6.1.2.1.2.2.1.8"

# Fallback ifTable (contadores 32-bit)
_OID_IN_OCTETS = "1.3.6.1.2.1.2.2.1.10"
_OID_OUT_OCTETS = "1.3.6.1.2.1.2.2.1.16"

_SCRIPT_DIR = Path(__file__).resolve().parent
_CONFIG_PATH = Path(
    os.environ.get(
        "SDD_CONFIG",
        str(_SCRIPT_DIR.parent / "config" / "devices.yaml"),
    )
)


def _respond(status: int, body: dict) -> None:
    reason = {
        200: "OK",
        400: "Bad Request",
        404: "Not Found",
        502: "Bad Gateway",
    }.get(status, "Error")
    sys.stdout.write(f"Status: {status} {reason}\r\n")
    sys.stdout.write("Content-Type: application/json\r\n")
    sys.stdout.write("Access-Control-Allow-Origin: *\r\n")
    sys.stdout.write("\r\n")
    sys.stdout.write(json.dumps(body))
    sys.stdout.flush()
    sys.exit(0)


def _load_device(name: str) -> dict | None:
    if not _CONFIG_PATH.exists():
        return None
    with open(_CONFIG_PATH) as f:
        data = yaml.safe_load(f)
    for device in (data or {}).get("devices", []):
        if device.get("name") == name:
            return device
    return None


def octets_to_gb(octets: str) -> float:
    try:
        return round(int(octets) / 1_073_741_824, 2)
    except (ValueError, TypeError):
        return 0.0


async def _walk_oid(
    engine: SnmpEngine,
    auth: CommunityData,
    transport: UdpTransportTarget,
    oid_prefix: str,
) -> dict[str, str]:
    """Recorre un subárbol OID y retorna {índice_de_interfaz: valor}."""
    results: dict[str, str] = {}
    current = oid_prefix
    while True:
        error_indication, error_status, _, var_binds = await next_cmd(
            engine, auth, transport, ContextData(),
            ObjectType(ObjectIdentity(current)),
        )
        if error_indication or error_status or not var_binds:
            break
        oid, value = var_binds[0]
        oid_str = str(oid)
        if not oid_str.startswith(oid_prefix + "."):
            break
        index = oid_str[len(oid_prefix) + 1:]
        results[index] = value.prettyPrint()
        current = oid_str
    return results


async def _walk_interfaces(
    host: str,
    community: str,
    port: int,
    timeout: int,
) -> list[dict]:
    engine = SnmpEngine()
    auth = CommunityData(community, mpModel=1)
    transport = await UdpTransportTarget.create(
        (host, port), timeout=timeout, retries=1
    )

    names = await _walk_oid(engine, auth, transport, _OID_IF_NAME)
    hc_in = await _walk_oid(engine, auth, transport, _OID_HC_IN)
    hc_out = await _walk_oid(engine, auth, transport, _OID_HC_OUT)
    statuses = await _walk_oid(engine, auth, transport, _OID_OPER_STATUS)
    aliases = await _walk_oid(engine, auth, transport, _OID_IF_ALIAS)

    # Fallback a contadores de 32-bit si el switch no soporta ifXTable
    if not hc_in:
        hc_in = await _walk_oid(engine, auth, transport, _OID_IN_OCTETS)
        hc_out = await _walk_oid(engine, auth, transport, _OID_OUT_OCTETS)

    interfaces = []
    for idx, if_name in names.items():
        in_gb = octets_to_gb(hc_in.get(idx, "0"))
        out_gb = octets_to_gb(hc_out.get(idx, "0"))
        total_gb = round(in_gb + out_gb, 2)
        status = "up" if statuses.get(idx, "2") == "1" else "down"
        interfaces.append({
            "name": if_name,
            "alias": aliases.get(idx, ""),
            "in_gb": in_gb,
            "out_gb": out_gb,
            "total_gb": total_gb,
            "status": status,
        })

    # Interfaces up primero ordenadas por total_gb desc, luego down por total_gb desc
    interfaces.sort(key=lambda x: (0 if x["status"] == "up" else 1, -x["total_gb"]))
    return interfaces


def main() -> None:
    qs = os.environ.get("QUERY_STRING", "")
    params: dict[str, str] = {}
    for part in qs.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v

    device_name = params.get("device", "").strip()
    if not device_name:
        _respond(400, {"error": "missing device parameter"})

    device = _load_device(device_name)
    if device is None:
        _respond(404, {"error": "device not found"})

    if device.get("type") != "switch":
        _respond(400, {"error": "device is not a switch"})

    host = device["host"]
    community = device.get("community", "public")
    port = int(device.get("port", 161))
    timeout = int(device.get("timeout", 5))

    try:
        interfaces = asyncio.run(
            _walk_interfaces(host, community, port, timeout)
        )
        _respond(200, {"interfaces": interfaces})
    except Exception as exc:
        _respond(502, {"error": str(exc)})


if __name__ == "__main__":
    main()
