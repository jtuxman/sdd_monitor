from datetime import datetime, timezone

from sdd_monitor.models import MetricRecord
from sdd_monitor.processor import process


def _record(raw: str) -> MetricRecord:
    return MetricRecord(
        device_name="router",
        oid="1.3.6.1.2.1.1.1.0",
        raw_value=raw,
        timestamp_utc=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


def test_process_integer_counter():
    records = process([_record("12345")])
    assert records[0].raw_value == "12345"


def test_process_hex_string_to_text():
    # "hello" en hex
    hex_val = "0x" + "hello".encode().hex()
    records = process([_record(hex_val)])
    assert records[0].raw_value == "hello"


def test_process_plain_string_unchanged():
    records = process([_record("Linux 5.15.0-generic")])
    assert records[0].raw_value == "Linux 5.15.0-generic"


def test_process_empty_list():
    assert process([]) == []


def test_process_preserves_metadata():
    original = _record("42")
    result = process([original])[0]
    assert result.device_name == original.device_name
    assert result.oid == original.oid
    assert result.timestamp_utc == original.timestamp_utc


def test_process_strips_whitespace():
    records = process([_record("  42  ")])
    assert records[0].raw_value == "42"
