import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pysnmp.hlapi import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    UsmUserData,
    getCmd,
    usmAesCfb128Protocol,
    usmHMACSHAAuthProtocol,
)

from sdd_monitor.models import MetricRecord

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = {"name", "host", "snmp_version", "oids"}


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


def _query_oid(
    engine: SnmpEngine,
    auth: CommunityData | UsmUserData,
    transport: UdpTransportTarget,
    oid: str,
) -> str | None:
    error_indication, error_status, error_index, var_binds = next(
        getCmd(engine, auth, transport, ContextData(), ObjectType(ObjectIdentity(oid)))
    )
    if error_indication:
        logger.warning("Error SNMP para OID %s: %s", oid, error_indication)
        return None
    if error_status:
        logger.warning(
            "OID %s no encontrado: %s at %s",
            oid,
            error_status.prettyPrint(),
            error_index,
        )
        return None
    _, value = var_binds[0]
    return value.prettyPrint()


def collect(devices: list[dict[str, Any]]) -> list[MetricRecord]:
    records: list[MetricRecord] = []
    engine = SnmpEngine()

    for device in devices:
        name = device["name"]
        try:
            auth = _make_auth(device)
            transport = UdpTransportTarget(
                (device["host"], device.get("port", 161)),
                timeout=device.get("timeout", 2),
                retries=device.get("retries", 1),
            )
        except Exception as exc:
            logger.error("Error configurando dispositivo '%s': %s", name, exc)
            continue

        for oid in device["oids"]:
            try:
                raw = _query_oid(engine, auth, transport, oid)
            except Exception as exc:
                logger.error(
                    "Error inesperado en dispositivo '%s' OID %s: %s", name, oid, exc
                )
                continue

            if raw is not None:
                records.append(
                    MetricRecord(
                        device_name=name,
                        oid=oid,
                        raw_value=raw,
                        timestamp_utc=datetime.now(timezone.utc),
                    )
                )
    return records
