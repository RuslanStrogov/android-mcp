"""Tests for environment-driven configuration."""

from __future__ import annotations

import pytest

from android_mcp.config import Config

_ENV = ("ANDROID_MCP_ADB", "ANDROID_MCP_SERIAL", "ANDROID_MCP_ADB_TIMEOUT")


def test_from_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ENV:
        monkeypatch.delenv(key, raising=False)
    cfg = Config.from_env()
    assert cfg.adb_binary == "adb"
    assert cfg.default_serial is None
    assert cfg.adb_timeout == 30.0


def test_from_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANDROID_MCP_ADB", "/opt/platform-tools/adb")
    monkeypatch.setenv("ANDROID_MCP_SERIAL", "192.168.10.210:5555")
    monkeypatch.setenv("ANDROID_MCP_ADB_TIMEOUT", "5")
    cfg = Config.from_env()
    assert cfg.adb_binary == "/opt/platform-tools/adb"
    assert cfg.default_serial == "192.168.10.210:5555"
    assert cfg.adb_timeout == 5.0
