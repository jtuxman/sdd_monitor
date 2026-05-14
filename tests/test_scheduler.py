from pathlib import Path
from unittest.mock import patch

from sdd_monitor.scheduler import _poll_cycle


@patch("sdd_monitor.scheduler.html_report.generate")
@patch("sdd_monitor.scheduler.presentation.render")
@patch("sdd_monitor.scheduler.Storage")
@patch("sdd_monitor.scheduler.processor.process")
@patch("sdd_monitor.scheduler.collector_liveness.collect")
@patch("sdd_monitor.scheduler.collector.collect")
def test_poll_cycle_propagates_liveness(
    mock_collect_snmp,
    mock_collect_liveness,
    mock_process,
    mock_storage,
    mock_render,
    mock_generate,
):
    mock_collect_snmp.return_value = ([], {})
    mock_collect_liveness.return_value = ["live-record"]
    mock_process.return_value = []
    storage_cm = mock_storage.return_value.__enter__.return_value

    _poll_cycle([{"name": "ap-1"}], Path("data/metrics.db"), Path("data/report.html"), 60)

    storage_cm.insert_liveness.assert_called_once_with(["live-record"])
    mock_render.assert_called_once()
    assert mock_render.call_args.args[2] == ["live-record"]
    assert mock_generate.call_args.args[6] == ["live-record"]
