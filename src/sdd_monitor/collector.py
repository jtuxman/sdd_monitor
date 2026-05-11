import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    UsmUserData,
    get_cmd,
    usmAesCfb128Protocol,
    usmHMACSHAAuthProtocol,
)

from sdd_monitor.models import MetricRecord

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = {"name", "host", "snmp_version", "oids"}


def _normalize_oid(raw: str | dict) -> tuple[str, str | None]:
    if isinstance(raw, str):
        return raw, None
    return raw["oid"], raw.get("label")


def load_devices(config_path: str | Path) -> list[dict[str, Any]]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {path}")

    with open(path) as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error al parsear {path}: {e}") from e

    devices = data.get("devices", []) if data else []
    for device in devices:
        missing = _REQUIRED_FIELDS - set(device.keys())
        if missing:
            raise ValueError(
                f"Dispositivo '{device.get('name', '?')}' falta campos: {missing}"
            )
        device["oids"] = [
            {"oid": oid, "label": label}
            for oid, label in (_normalize_oid(o) for o in device["oids"])
        ]
    return devices


def _make_auth(device: dict[str, Any]) -> CommunityData | UsmUserData:
    version = str(device["snmp_version"]).lower()
    if version == "2c":
        return CommunityData(device.get("community", "public"), mpModel=1)
    if version == "3":
        return UsmUserData(
            os.environ["SNMPV3_USERNAME"],
            authKey=os.environ["SNMPV3_AUTH_KEY"],
            privKey=os.environ["SNMPV3_PRIV_KEY"],
            authProtocol=usmHMACSHAAuthProtocol,
            privProtocol=usmAesCfb128Protocol,
        )
    raise ValueError(f"Versión SNMP no soportada: {version}")


async def _query_oid(
    engine: SnmpEngine,
    auth: CommunityData | UsmUserData,
    transport: UdpTransportTarget,
    oid: str,
) -> tuple[str | None, str | None]:
    """Returns (value, error_msg). One of them is always None."""
    error_indication, error_status, error_index, var_binds = await get_cmd(
        engine, auth, transport, ContextData(), ObjectType(ObjectIdentity(oid))
    )
    if error_indication:
        msg = str(error_indication)
        logger.warning("Error SNMP para OID %s: %s", oid, msg)
        return None, msg
    if error_status:
        msg = error_status.prettyPrint()
        logger.warning("OID %s no encontrado: %s at %s", oid, msg, error_index)
        return None, msg
    _, value = var_binds[0]
    return value.prettyPrint(), None


async def _collect_async(
    devices: list[dict[str, Any]],
) -> tuple[list[MetricRecord], dict[str, str]]:
    records: list[MetricRecord] = []
    errors: dict[str, str] = {}

    for device in devices:
        name = device["name"]
        engine = SnmpEngine()
        try:
            auth = _make_auth(device)
            transport = await UdpTransportTarget.create(
                (device["host"], device.get("port", 161)),
                timeout=device.get("timeout", 2),
                retries=device.get("retries", 1),
            )
        except Exception as exc:
            logger.error("Error configurando dispositivo '%s': %s", name, exc)
            errors[name] = str(exc)
            continue

        device_start = len(records)
        last_error: str | None = None

        for oid_entry in device["oids"]:
            oid, label = (
                _normalize_oid(oid_entry)
                if isinstance(oid_entry, str)
                else (oid_entry["oid"], oid_entry.get("label"))
            )
            try:
                raw, err = await _query_oid(engine, auth, transport, oid)
            except Exception as exc:
                last_error = str(exc)
                logger.error("Error inesperado en '%s' OID %s: %s", name, oid, exc)
                continue

            if raw is not None:
                records.append(
                    MetricRecord(
                        device_name=name,
                        oid=oid,
                        raw_value=raw,
                        timestamp_utc=datetime.now(timezone.utc),
                        label=label,
                    )
                )
            elif err and last_error is None:
                last_error = err

        if len(records) == device_start and last_error:
            errors[name] = last_error

    return records, errors


def collect(
    devices: list[dict[str, Any]],
) -> tuple[list[MetricRecord], dict[str, str]]:
    return asyncio.run(_collect_async(devices))
