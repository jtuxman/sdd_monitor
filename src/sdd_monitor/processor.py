import re

from sdd_monitor.models import MetricRecord

_INTEGER_RE = re.compile(r"^\d+$")
_HEX_STRING_RE = re.compile(r"^0x[0-9a-fA-F]+$")


def _normalize(raw_value: str) -> str:
    stripped = raw_value.strip()

    # Counter32/Gauge32/Integer: valor numérico puro
    if _INTEGER_RE.match(stripped):
        return str(int(stripped))

    # OctetString expresado como hex: convertir a texto legible si es posible
    if _HEX_STRING_RE.match(stripped):
        try:
            hex_part = stripped[2:]
            decoded = bytes.fromhex(hex_part).decode("utf-8", errors="replace")
            return decoded.strip("\x00").strip()
        except ValueError:
            pass

    return stripped


def process(records: list[MetricRecord]) -> list[MetricRecord]:
    result = []
    for record in records:
        normalized = _normalize(record.raw_value)
        result.append(
            MetricRecord(
                device_name=record.device_name,
                oid=record.oid,
                raw_value=normalized,
                timestamp_utc=record.timestamp_utc,
            )
        )
    return result
