from dataclasses import dataclass
from datetime import datetime


@dataclass
class MetricRecord:
    device_name: str
    oid: str
    raw_value: str
    timestamp_utc: datetime
    label: str | None = None


@dataclass
class LivenessRecord:
    device_name: str
    is_up: bool
    ping_rtt_ms: float | None
    https_up: bool
    error: str | None
    timestamp_utc: datetime
