from datetime import datetime, timezone

import pytest

from sdd_monitor.models import MetricRecord
from sdd_monitor.storage import Storage


def _record(device: str, oid: str = "1.3.6.1.2.1.1.1.0", value: str = "test") -> MetricRecord:
    return MetricRecord(
        device_name=device,
        oid=oid,
        raw_value=value,
        timestamp_utc=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def storage(tmp_path):
    db = tmp_path / "test.db"
    with Storage(db) as s:
        yield s


def test_schema_created_on_init(tmp_path):
    db = tmp_path / "metrics.db"
    with Storage(db):
        pass
    assert db.exists()


def test_insert_and_query(storage):
    storage.insert([_record("router")])
    results = storage.query_by_device("router")
    assert len(results) == 1
    assert results[0].device_name == "router"
    assert results[0].raw_value == "test"


def test_query_empty_device(storage):
    results = storage.query_by_device("nonexistent")
    assert results == []


def test_query_ordered_by_timestamp_desc(storage):
    r1 = MetricRecord(
        device_name="router",
        oid="1.3.6.1.2.1.1.1.0",
        raw_value="first",
        timestamp_utc=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    r2 = MetricRecord(
        device_name="router",
        oid="1.3.6.1.2.1.1.1.0",
        raw_value="second",
        timestamp_utc=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
    )
    storage.insert([r1, r2])
    results = storage.query_by_device("router")
    assert results[0].raw_value == "second"
    assert results[1].raw_value == "first"


def test_query_only_own_device(storage):
    storage.insert([_record("router"), _record("switch")])
    results = storage.query_by_device("router")
    assert all(r.device_name == "router" for r in results)
    assert len(results) == 1


def test_insert_multiple_records(storage):
    records = [_record("router", oid=f"1.3.6.1.{i}") for i in range(5)]
    storage.insert(records)
    results = storage.query_by_device("router")
    assert len(results) == 5


# ── query_recent ───────────────────────────────────────────────────────────────

def _record_ts(device, oid, value, hour):
    return MetricRecord(
        device_name=device,
        oid=oid,
        raw_value=value,
        timestamp_utc=datetime(2024, 1, 1, hour, 0, 0, tzinfo=timezone.utc),
    )


def test_query_recent_returns_oldest_first(storage):
    oid = "1.3.6.1.2.1.1.3.0"
    storage.insert([
        _record_ts("router", oid, "10", 10),
        _record_ts("router", oid, "20", 11),
        _record_ts("router", oid, "30", 12),
    ])
    results = storage.query_recent("router", oid)
    assert [r.raw_value for r in results] == ["10", "20", "30"]


def test_query_recent_respects_limit(storage):
    oid = "1.3.6.1.2.1.1.3.0"
    storage.insert([_record_ts("router", oid, str(i), i) for i in range(10)])
    results = storage.query_recent("router", oid, n=3)
    assert len(results) == 3
    assert results[-1].raw_value == "9"


def test_query_recent_empty(storage):
    results = storage.query_recent("nonexistent", "1.3.6.1.2.1.1.3.0")
    assert results == []


def test_query_recent_only_matching_oid(storage):
    storage.insert([
        _record_ts("router", "1.3.6.1.2.1.1.1.0", "desc", 10),
        _record_ts("router", "1.3.6.1.2.1.1.3.0", "42", 10),
    ])
    results = storage.query_recent("router", "1.3.6.1.2.1.1.3.0")
    assert len(results) == 1
    assert results[0].raw_value == "42"


# ── query_timerange ────────────────────────────────────────────────────────────

def test_query_timerange_returns_records_in_range(tmp_path):
    from datetime import timedelta
    db = tmp_path / "metrics.db"
    oid = "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1"
    now = datetime.now(timezone.utc)
    with Storage(db) as s:
        s.insert([
            MetricRecord("sw", oid, "10", now - timedelta(minutes=30)),
            MetricRecord("sw", oid, "20", now - timedelta(minutes=90)),  # fuera de 1h
        ])
        results = s.query_timerange("sw", oid, hours=1)
    assert len(results) == 1
    assert results[0].raw_value == "10"


def test_query_timerange_empty(tmp_path):
    db = tmp_path / "metrics.db"
    with Storage(db) as s:
        results = s.query_timerange("sw", "1.3.6.1.2.1.1.1.0", hours=24)
    assert results == []


def test_query_timerange_ordered_asc(tmp_path):
    from datetime import timedelta
    db = tmp_path / "metrics.db"
    oid = "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1"
    now = datetime.now(timezone.utc)
    with Storage(db) as s:
        s.insert([
            MetricRecord("sw", oid, "30", now - timedelta(minutes=10)),
            MetricRecord("sw", oid, "10", now - timedelta(minutes=30)),
            MetricRecord("sw", oid, "20", now - timedelta(minutes=20)),
        ])
        results = s.query_timerange("sw", oid, hours=1)
    assert [r.raw_value for r in results] == ["10", "20", "30"]


# ── _aggregate ─────────────────────────────────────────────────────────────────

def test_aggregate_empty():
    from sdd_monitor.html_report import _aggregate
    labels, data = _aggregate([], bucket_minutes=15)
    assert labels == [] and data == []


def test_aggregate_averages_bucket():
    from sdd_monitor.html_report import _aggregate
    from datetime import timedelta
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    records = [
        MetricRecord("sw", "oid", "10", now),
        MetricRecord("sw", "oid", "20", now + timedelta(minutes=5)),
        MetricRecord("sw", "oid", "90", now + timedelta(minutes=20)),
    ]
    labels, data = _aggregate(records, bucket_minutes=15)
    assert len(data) == 2
    assert data[0] == 15.0  # promedio de 10 y 20
    assert data[1] == 90.0


def test_aggregate_skips_non_numeric():
    from sdd_monitor.html_report import _aggregate
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    records = [MetricRecord("sw", "oid", "texto", now)]
    labels, data = _aggregate(records, bucket_minutes=1)
    assert labels == [] and data == []


def test_aggregate_fills_full_range_with_start_time():
    from datetime import timedelta
    from sdd_monitor.html_report import _aggregate
    now_utc = datetime.now(timezone.utc)
    start = now_utc - timedelta(hours=1)
    records = [MetricRecord("sw", "oid", "42", now_utc - timedelta(minutes=5))]
    labels, data = _aggregate(records, bucket_minutes=1, start_time=start)
    assert len(labels) >= 60
    assert any(v is None for v in data)
    assert any(v == 42.0 for v in data)


def test_aggregate_empty_with_start_time():
    from datetime import timedelta
    from sdd_monitor.html_report import _aggregate
    now_utc = datetime.now(timezone.utc)
    start = now_utc - timedelta(hours=1)
    labels, data = _aggregate([], bucket_minutes=1, start_time=start)
    assert len(labels) >= 60
    assert all(v is None for v in data)
