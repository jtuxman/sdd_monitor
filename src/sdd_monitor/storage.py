import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sdd_monitor.models import LivenessRecord, MetricRecord

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS metrics (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name   TEXT NOT NULL,
    oid           TEXT NOT NULL,
    value         TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL
)
"""

_CREATE_LIVENESS_TABLE = """
CREATE TABLE IF NOT EXISTS ap_liveness (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name   TEXT NOT NULL,
    is_up         INTEGER NOT NULL,
    ping_rtt_ms   REAL,
    https_up      INTEGER NOT NULL,
    error         TEXT,
    timestamp_utc TEXT NOT NULL
)
"""


class Storage:
    def __init__(self, db_path: str | Path) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.execute(_CREATE_TABLE)
        self._conn.execute(_CREATE_LIVENESS_TABLE)
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

    def query_timerange(self, device_name: str, oid: str, hours: int) -> list[MetricRecord]:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        cursor = self._conn.execute(
            "SELECT device_name, oid, value, timestamp_utc FROM metrics "
            "WHERE device_name = ? AND oid = ? AND timestamp_utc >= ? "
            "ORDER BY timestamp_utc ASC",
            (device_name, oid, cutoff),
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

    def insert_liveness(self, records: list[LivenessRecord]) -> None:
        if not records:
            return
        rows = [
            (
                r.device_name,
                int(r.is_up),
                r.ping_rtt_ms,
                int(r.https_up),
                r.error,
                r.timestamp_utc.isoformat(),
            )
            for r in records
        ]
        self._conn.executemany(
            "INSERT INTO ap_liveness "
            "(device_name, is_up, ping_rtt_ms, https_up, error, timestamp_utc) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        self._conn.commit()

    def query_latest_liveness(self) -> list[LivenessRecord]:
        cursor = self._conn.execute(
            "SELECT l.device_name, l.is_up, l.ping_rtt_ms, l.https_up, l.error, l.timestamp_utc "
            "FROM ap_liveness l "
            "JOIN (SELECT device_name, MAX(timestamp_utc) AS max_ts "
            "      FROM ap_liveness GROUP BY device_name) last "
            "  ON l.device_name = last.device_name AND l.timestamp_utc = last.max_ts "
            "ORDER BY l.device_name ASC"
        )
        results: list[LivenessRecord] = []
        for row in cursor.fetchall():
            results.append(
                LivenessRecord(
                    device_name=row[0],
                    is_up=bool(row[1]),
                    ping_rtt_ms=row[2],
                    https_up=bool(row[3]),
                    error=row[4],
                    timestamp_utc=datetime.fromisoformat(row[5]).replace(tzinfo=timezone.utc),
                )
            )
        return results

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Storage":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
