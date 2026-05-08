from dataclasses import dataclass
from datetime import datetime


@dataclass
class MetricRecord:
    device_name: str
    oid: str
    raw_value: str
    timestamp_utc: datetime
    label: str | None = None
