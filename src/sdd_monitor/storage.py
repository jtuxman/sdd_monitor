import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sdd_monitor.models import MetricRecord

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS metrics (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name   TEXT NOT NULL,
    oid           TEXT NOT NULL,
    value         TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL
)
"""


class Storage:
    def __init__(self, db_path: str | Path) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()

    def insert(self, records: list[MetricRecord]) -> None:
        rows = [
            (r.device_name, r.oid, r.raw_value, r.timestamp_utc.isoformat())
            for r in records
        ]
        self._conn.executemany(
            "INSERT INTO metrics (device_name, oid, value, timestamp_utc) VALUES (?, ?, ?, ?)",
            rows,
        )
        self._conn.commit()

    def query_by_device(self, device_name: str) -> list[MetricRecord]:
        cursor = self._conn.execute(
            "SELECT device_name, oid, value, timestamp_utc FROM metrics "
            "WHERE device_name = ? ORDER BY timestamp_utc DESC",
            (device_name,),
        )
        results = []
        for row in cursor.fetchall():
            results.append(
                MetricRecord(
                    device_name=row[0],
                    oid=row[1],
                    raw_value=row[2],
                    timestamp_utc=datetime.fromisoformat(row[3]).replace(
                        tzinfo=timezone.utc
                    ),
                )
            )
        return results

    def query_recent(self, device_name: str, oid: str, n: int = 20) -> list[MetricRecord]:
        cursor = self._conn.execute(
            "SELECT device_name, oid, value, timestamp_utc FROM metrics "
            "WHERE device_name = ? AND oid = ? "
            "ORDER BY timestamp_utc DESC LIMIT ?",
            (device_name, oid, n),
        )
        results = []
        for row in cursor.fetchall():
            results.append(
                MetricRecord(
                    device_name=row[0],
                    oid=row[1],
                    raw_value=row[2],
                    timestamp_utc=datetime.fromisoformat(row[3]).replace(
                        tzinfo=timezone.utc
                    ),
                )
            )
        results.reverse()
        return results

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Storage":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
