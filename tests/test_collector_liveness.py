from unittest.mock import MagicMock, patch

from sdd_monitor.collector_liveness import collect


def _devices():
    return [
        {"name": "ap-1", "type": "ap", "host": "10.0.0.10"},
        {"name": "sw-1", "type": "switch", "host": "10.0.0.20", "liveness": True},
        {"name": "router-1", "type": "router", "host": "10.0.0.30"},
    ]


@patch("sdd_monitor.collector_liveness.socket.create_connection")
@patch("sdd_monitor.collector_liveness.subprocess.run")
def test_collect_up_from_ping_and_https(mock_run, mock_conn):
    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = "64 bytes from 10.0.0.10: icmp_seq=1 ttl=63 time=3.45 ms"
    proc.stderr = ""
    mock_run.return_value = proc
    mock_conn.return_value.__enter__.return_value = None

    records = collect(_devices())
    assert len(records) == 2
    assert records[0].device_name == "ap-1"
    assert records[0].is_up is True
    assert records[0].https_up is True
    assert records[0].ping_rtt_ms == 3.45


@patch("sdd_monitor.collector_liveness.socket.create_connection", side_effect=TimeoutError("tcp timeout"))
@patch("sdd_monitor.collector_liveness.subprocess.run")
def test_collect_down_with_errors(mock_run, _mock_conn):
    proc = MagicMock()
    proc.returncode = 1
    proc.stdout = ""
    proc.stderr = "100% packet loss"
    mock_run.return_value = proc

    records = collect([{"name": "ap-1", "type": "ap", "host": "10.0.0.10"}])
    assert len(records) == 1
    assert records[0].is_up is False
    assert records[0].https_up is False
    assert "packet loss" in (records[0].error or "")


def test_collect_skips_non_targets():
    records = collect([{"name": "router-1", "type": "router", "host": "10.0.0.30"}])
    assert records == []
