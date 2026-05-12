from datetime import datetime, timezone
from pathlib import Path

from sdd_monitor.html_report import generate
from sdd_monitor.models import MetricRecord
from sdd_monitor.storage import Storage


def _record(device="switch-core", oid="1.3.6.1.4.1.9.9.109.1.1.1.1.8.1", value="42", label="CPU 5min %"):
    return MetricRecord(
        device_name=device,
        oid=oid,
        raw_value=value,
        timestamp_utc=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        label=label,
    )


def _devices(device_type="switch"):
    return [
        {
            "name": "switch-core",
            "type": device_type,
            "host": "10.0.0.1",
            "snmp_version": "2c",
            "community": "public",
            "oids": [{"oid": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1", "label": "CPU 5min %"}],
        }
    ]


def test_generate_creates_html_file(tmp_path):
    db = tmp_path / "metrics.db"
    html_path = tmp_path / "report.html"
    metrics = [_record()]
    generate(metrics, _devices(), {}, db, html_path, poll_interval=60)
    assert html_path.exists()


def test_generate_html_contains_device_name(tmp_path):
    db = tmp_path / "metrics.db"
    html_path = tmp_path / "report.html"
    generate([_record()], _devices(), {}, db, html_path, poll_interval=60)
    content = html_path.read_text()
    assert "switch-core" in content


def test_generate_html_auto_refresh_via_js(tmp_path):
    db = tmp_path / "metrics.db"
    html_path = tmp_path / "report.html"
    generate([_record()], _devices(), {}, db, html_path, poll_interval=30)
    content = html_path.read_text()
    assert 'setTimeout' in content
    assert '_pollInterval=30' in content


def test_generate_html_contains_chart_canvas_for_numeric_oid(tmp_path):
    from datetime import timedelta
    db = tmp_path / "metrics.db"
    html_path = tmp_path / "report.html"
    now = datetime.now(timezone.utc)
    with Storage(db) as s:
        s.insert([
            MetricRecord("switch-core", "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1", str(i * 10), now - timedelta(minutes=i * 5))
            for i in range(3)
        ])
    generate([_record()], _devices(), {}, db, html_path, poll_interval=60)
    content = html_path.read_text()
    assert "<canvas" in content
    assert "Chart" in content


def test_generate_html_shows_device_icon(tmp_path):
    db = tmp_path / "metrics.db"
    html_path = tmp_path / "report.html"
    generate([_record()], _devices(device_type="switch"), {}, db, html_path, poll_interval=60)
    content = html_path.read_text()
    assert "🔀" in content


def test_generate_no_chart_for_text_oid(tmp_path):
    db = tmp_path / "metrics.db"
    html_path = tmp_path / "report.html"
    metrics = [_record(oid="1.3.6.1.2.1.1.1.0", value="Linux switch 5.15", label="Descripción")]
    devices = [
        {
            "name": "switch-core",
            "type": "switch",
            "host": "10.0.0.1",
            "snmp_version": "2c",
            "community": "public",
            "oids": [{"oid": "1.3.6.1.2.1.1.1.0", "label": "Descripción"}],
        }
    ]
    generate(metrics, devices, {}, db, html_path, poll_interval=60)
    content = html_path.read_text()
    assert "<canvas" not in content


def test_generate_error_does_not_raise(tmp_path):
    db = tmp_path / "metrics.db"
    bad_path = Path("/nonexistent/path/report.html")
    generate([_record()], _devices(), {}, db, bad_path, poll_interval=60)


def test_generate_shows_error_card_for_unreachable_device(tmp_path):
    db = tmp_path / "metrics.db"
    html_path = tmp_path / "report.html"
    errors = {"switch-core": "No SNMP response received before timeout"}
    generate([], _devices(), errors, db, html_path, poll_interval=60)
    content = html_path.read_text()
    assert "switch-core" in content
    assert "Sin respuesta" in content
    assert "No SNMP response received before timeout" in content
    assert "error-card" in content


def test_generate_utc6_timestamp_in_table(tmp_path):
    db = tmp_path / "metrics.db"
    html_path = tmp_path / "report.html"
    generate([_record()], _devices(), {}, db, html_path, poll_interval=60)
    content = html_path.read_text()
    assert "UTC-6" in content
