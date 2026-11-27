"""Tests that the server registers the expected tool surface (no device needed)."""

from __future__ import annotations

import asyncio

from android_mcp.server import build_server

EXPECTED = {
    "device_list",
    "device_state",
    "device_capabilities",
    "screenshot",
    "dump_ui",
    "tap",
    "tap_text",
    "swipe",
    "type_text",
    "press_key",
    "wake",
    "app_launch",
    "app_stop",
    "app_list",
}


def _tool_names() -> set[str]:
    app = build_server()
    tools = asyncio.run(app.list_tools())
    return {t.name for t in tools}


def test_expected_tools_present() -> None:
    assert EXPECTED <= _tool_names()


def test_tool_count_is_reasonable() -> None:
    names = _tool_names()
    assert len(names) == len(EXPECTED)
