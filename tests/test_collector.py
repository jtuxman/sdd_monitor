import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

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


# ── consulta SNMP v2c ──────────────────────────────────────────────────────────

def _make_var_bind(oid_str, value_str):
    from pysnmp.proto.rfc1902 import OctetString
    from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

    var_bind = MagicMock()
    var_bind.__iter__ = MagicMock(return_value=iter([oid_str, MagicMock(prettyPrint=lambda: value_str)]))
    return var_bind


def _snmp_ok_response(value="Linux router"):
    oid_mock = MagicMock()
    value_mock = MagicMock()
    value_mock.prettyPrint.return_value = value
    return (None, None, None, [(oid_mock, value_mock)])


def _snmp_timeout_response():
    return ("No SNMP response received", None, None, [])


def _snmp_no_such_object_response():
    error_status = MagicMock()
    error_status.prettyPrint.return_value = "noSuchObject"
    return (None, error_status, 0, [])


@patch("sdd_monitor.collector.getCmd")
def test_collect_v2c_success(mock_get_cmd):
    oid_mock = MagicMock()
    value_mock = MagicMock()
    value_mock.prettyPrint.return_value = "Linux router 5.15"
    mock_get_cmd.return_value = iter([(None, None, None, [(oid_mock, value_mock)])])

    devices = [
        {
            "name": "router",
            "host": "192.168.1.1",
            "snmp_version": "2c",
            "community": "public",
            "oids": ["1.3.6.1.2.1.1.1.0"],
        }
    ]
    records = collect(devices)
    assert len(records) == 1
    assert records[0].device_name == "router"
    assert records[0].raw_value == "Linux router 5.15"
    assert records[0].oid == "1.3.6.1.2.1.1.1.0"


# ── manejo de timeout ──────────────────────────────────────────────────────────

@patch("sdd_monitor.collector.getCmd")
def test_collect_device_timeout(mock_get_cmd):
    mock_get_cmd.return_value = iter([("No SNMP response received", None, None, [])])

    devices = [
        {
            "name": "router",
            "host": "192.168.1.1",
            "snmp_version": "2c",
            "community": "public",
            "oids": ["1.3.6.1.2.1.1.1.0"],
        }
    ]
    records = collect(devices)
    assert records == []


# ── OID no encontrado ──────────────────────────────────────────────────────────

@patch("sdd_monitor.collector.getCmd")
def test_collect_oid_not_found(mock_get_cmd):
    error_status = MagicMock()
    error_status.prettyPrint.return_value = "noSuchObject"
    mock_get_cmd.return_value = iter([(None, error_status, 0, [])])

    devices = [
        {
            "name": "router",
            "host": "192.168.1.1",
            "snmp_version": "2c",
            "community": "public",
            "oids": ["1.3.6.1.99.99.99.0"],
        }
    ]
    records = collect(devices)
    assert records == []


# ── un dispositivo falla, los demás continúan ──────────────────────────────────

@patch("sdd_monitor.collector.getCmd")
def test_collect_one_device_fails_others_continue(mock_get_cmd):
    value_mock = MagicMock()
    value_mock.prettyPrint.return_value = "ok"
    oid_mock = MagicMock()

    # primer dispositivo: timeout; segundo: ok
    mock_get_cmd.side_effect = [
        iter([("Timeout", None, None, [])]),
        iter([(None, None, None, [(oid_mock, value_mock)])]),
    ]

    devices = [
        {
            "name": "bad",
            "host": "10.0.0.1",
            "snmp_version": "2c",
            "community": "public",
            "oids": ["1.3.6.1.2.1.1.1.0"],
        },
        {
            "name": "good",
            "host": "10.0.0.2",
            "snmp_version": "2c",
            "community": "public",
            "oids": ["1.3.6.1.2.1.1.1.0"],
        },
    ]
    records = collect(devices)
    assert len(records) == 1
    assert records[0].device_name == "good"
