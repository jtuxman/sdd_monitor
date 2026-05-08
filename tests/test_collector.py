import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sdd_monitor.collector import collect, load_devices


# ── carga de YAML ──────────────────────────────────────────────────────────────

def test_load_devices_valid(tmp_path):
    cfg = tmp_path / "devices.yaml"
    cfg.write_text(textwrap.dedent("""\
        devices:
          - name: router
            host: 192.168.1.1
            snmp_version: 2c
            community: public
            oids:
              - 1.3.6.1.2.1.1.1.0
    """))
    devices = load_devices(cfg)
    assert len(devices) == 1
    assert devices[0]["name"] == "router"


def test_load_devices_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_devices(tmp_path / "nonexistent.yaml")


def test_load_devices_malformed_yaml(tmp_path):
    cfg = tmp_path / "devices.yaml"
    cfg.write_text("devices: [unclosed")
    with pytest.raises(ValueError, match="Error al parsear"):
        load_devices(cfg)


def test_load_devices_missing_required_field(tmp_path):
    cfg = tmp_path / "devices.yaml"
    cfg.write_text(textwrap.dedent("""\
        devices:
          - name: router
            host: 192.168.1.1
            snmp_version: 2c
    """))  # falta 'oids'
    with pytest.raises(ValueError, match="falta campos"):
        load_devices(cfg)


def test_load_devices_oids_as_strings(tmp_path):
    cfg = tmp_path / "devices.yaml"
    cfg.write_text(textwrap.dedent("""\
        devices:
          - name: router
            host: 192.168.1.1
            snmp_version: 2c
            community: public
            oids:
              - 1.3.6.1.2.1.1.1.0
              - 1.3.6.1.2.1.1.3.0
    """))
    devices = load_devices(cfg)
    oids = devices[0]["oids"]
    assert oids[0] == {"oid": "1.3.6.1.2.1.1.1.0", "label": None}
    assert oids[1] == {"oid": "1.3.6.1.2.1.1.3.0", "label": None}


def test_load_devices_oids_as_objects(tmp_path):
    cfg = tmp_path / "devices.yaml"
    cfg.write_text(textwrap.dedent("""\
        devices:
          - name: switch
            host: 10.0.0.1
            snmp_version: 2c
            community: public
            oids:
              - oid: 1.3.6.1.4.1.9.9.109.1.1.1.1.8.1
                label: CPU 5min %
    """))
    devices = load_devices(cfg)
    oids = devices[0]["oids"]
    assert oids[0] == {"oid": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1", "label": "CPU 5min %"}


def test_load_devices_oids_mixed(tmp_path):
    cfg = tmp_path / "devices.yaml"
    cfg.write_text(textwrap.dedent("""\
        devices:
          - name: switch
            host: 10.0.0.1
            snmp_version: 2c
            community: public
            oids:
              - 1.3.6.1.2.1.1.1.0
              - oid: 1.3.6.1.4.1.9.9.109.1.1.1.1.8.1
                label: CPU 5min %
    """))
    devices = load_devices(cfg)
    oids = devices[0]["oids"]
    assert oids[0] == {"oid": "1.3.6.1.2.1.1.1.0", "label": None}
    assert oids[1] == {"oid": "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1", "label": "CPU 5min %"}


# ── helpers para tests de collect ─────────────────────────────────────────────

def _devices(oids=None):
    return [
        {
            "name": "router",
            "host": "192.168.1.1",
            "snmp_version": "2c",
            "community": "public",
            "oids": oids or [{"oid": "1.3.6.1.2.1.1.1.0", "label": None}],
        }
    ]


def _snmp_ok(value="Linux router"):
    oid_mock = MagicMock()
    value_mock = MagicMock()
    value_mock.prettyPrint.return_value = value
    return (None, None, None, [(oid_mock, value_mock)])


# ── consulta SNMP v2c ──────────────────────────────────────────────────────────

@patch("sdd_monitor.collector.UdpTransportTarget")
@patch("sdd_monitor.collector.get_cmd", new_callable=AsyncMock)
def test_collect_v2c_success(mock_get_cmd, mock_transport_cls):
    mock_transport_cls.create = AsyncMock(return_value=MagicMock())
    mock_get_cmd.return_value = _snmp_ok("Linux router 5.15")

    records = collect(_devices())
    assert len(records) == 1
    assert records[0].device_name == "router"
    assert records[0].raw_value == "Linux router 5.15"
    assert records[0].oid == "1.3.6.1.2.1.1.1.0"


# ── manejo de timeout ──────────────────────────────────────────────────────────

@patch("sdd_monitor.collector.UdpTransportTarget")
@patch("sdd_monitor.collector.get_cmd", new_callable=AsyncMock)
def test_collect_device_timeout(mock_get_cmd, mock_transport_cls):
    mock_transport_cls.create = AsyncMock(return_value=MagicMock())
    mock_get_cmd.return_value = ("No SNMP response received", None, None, [])

    records = collect(_devices())
    assert records == []


# ── OID no encontrado ──────────────────────────────────────────────────────────

@patch("sdd_monitor.collector.UdpTransportTarget")
@patch("sdd_monitor.collector.get_cmd", new_callable=AsyncMock)
def test_collect_oid_not_found(mock_get_cmd, mock_transport_cls):
    mock_transport_cls.create = AsyncMock(return_value=MagicMock())
    error_status = MagicMock()
    error_status.prettyPrint.return_value = "noSuchObject"
    mock_get_cmd.return_value = (None, error_status, 0, [])

    records = collect(_devices(oids=[{"oid": "1.3.6.1.99.99.99.0", "label": None}]))
    assert records == []


# ── un dispositivo falla, los demás continúan ──────────────────────────────────

@patch("sdd_monitor.collector.UdpTransportTarget")
@patch("sdd_monitor.collector.get_cmd", new_callable=AsyncMock)
def test_collect_one_device_fails_others_continue(mock_get_cmd, mock_transport_cls):
    value_mock = MagicMock()
    value_mock.prettyPrint.return_value = "ok"
    oid_mock = MagicMock()

    mock_transport_cls.create = AsyncMock(return_value=MagicMock())
    mock_get_cmd.side_effect = [
        ("Timeout", None, None, []),
        (None, None, None, [(oid_mock, value_mock)]),
    ]

    devices = [
        {"name": "bad",  "host": "10.0.0.1", "snmp_version": "2c", "community": "public",
         "oids": [{"oid": "1.3.6.1.2.1.1.1.0", "label": None}]},
        {"name": "good", "host": "10.0.0.2", "snmp_version": "2c", "community": "public",
         "oids": [{"oid": "1.3.6.1.2.1.1.1.0", "label": None}]},
    ]
    records = collect(devices)
    assert len(records) == 1
    assert records[0].device_name == "good"
