"""Unit tests for pure device-output parsing (no device required)."""

from __future__ import annotations

from android_mcp.device import parse_devices


def test_parse_devices_empty() -> None:
    assert parse_devices("List of devices attached\n") == []


def test_parse_devices_usb_with_model() -> None:
    out = (
        "List of devices attached\n"
        "R58M12345\tdevice product:o1sxxx model:SM_G991B device:o1s transport_id:1\n"
    )
    devices = parse_devices(out)
    assert len(devices) == 1
    assert devices[0].serial == "R58M12345"
    assert devices[0].state == "device"
    assert devices[0].model == "SM_G991B"


def test_parse_devices_wireless() -> None:
    out = "List of devices attached\n192.168.10.50:5555\tdevice\n"
    devices = parse_devices(out)
    assert len(devices) == 1
    assert devices[0].serial == "192.168.10.50:5555"
    assert devices[0].model is None


def test_parse_devices_unauthorized_and_offline() -> None:
    out = "List of devices attached\nABC123\tunauthorized\nDEF456\toffline\n"
    devices = parse_devices(out)
    assert {d.state for d in devices} == {"unauthorized", "offline"}
