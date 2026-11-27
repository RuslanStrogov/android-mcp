"""Unit tests for device-state parsing (no device required)."""

from __future__ import annotations

from android_mcp.state import format_state, parse_state

BATTERY = """Current Battery Service state:
  level: 27
  voltage: 3818
  temperature: 210
  health: 2
"""
POWER = """Power Manager State:
  mWakefulness=Awake
"""
WINDOW = """  mCurrentFocus=Window{c4ecd1 u0 com.android.settings/com.android.settings.MainSettings}
"""


def test_parse_state_full() -> None:
    st = parse_state(BATTERY, POWER, WINDOW)
    assert st.battery_level == 27
    assert st.battery_temp_c == 21.0
    assert st.screen_awake is True
    assert st.foreground == "com.android.settings"


def test_parse_state_missing_fields() -> None:
    st = parse_state("", "", "")
    assert st.battery_level is None
    assert st.screen_awake is None
    assert st.foreground is None


def test_format_state() -> None:
    out = format_state(parse_state(BATTERY, POWER, WINDOW))
    assert "27%" in out
    assert "21.0" in out
    assert "com.android.settings" in out
