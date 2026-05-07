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
