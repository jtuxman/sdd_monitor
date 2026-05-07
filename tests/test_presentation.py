from datetime import datetime, timezone
from io import StringIO

from rich.console import Console

from sdd_monitor.models import MetricRecord
from sdd_monitor.presentation import render


def _record(device: str = "router", value: str = "Linux") -> MetricRecord:
    return MetricRecord(
        device_name=device,
        oid="1.3.6.1.2.1.1.1.0",
        raw_value=value,
        timestamp_utc=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


def _capture(records, errors=None):
    buf = StringIO()
    import sdd_monitor.presentation as pres
    original = pres.console
    pres.console = Console(file=buf, no_color=True, width=200)
    try:
        render(records, errors)
    finally:
        pres.console = original
    return buf.getvalue()


def test_render_table_with_records():
    output = _capture([_record()])
    assert "router" in output
    assert "1.3.6.1.2.1.1.1.0" in output
    assert "Linux" in output


def test_render_empty_records_shows_message():
    output = _capture([])
    assert "Sin métricas" in output


def test_render_device_error_shown():
    output = _capture([], errors={"router": "Timeout"})
    assert "router" in output
    assert "Timeout" in output


def test_render_multiple_records():
    records = [_record("r1", "val1"), _record("r2", "val2")]
    output = _capture(records)
    assert "r1" in output
    assert "r2" in output


def test_render_errors_and_records_together():
    output = _capture(
        [_record("switch")],
        errors={"router": "unreachable"},
    )
    assert "router" in output
    assert "switch" in output
