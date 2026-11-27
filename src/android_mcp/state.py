"""Read-only device state: battery, screen, orientation, foreground app.

Works on restricted ROMs (no input injection needed), unlike tap/swipe/uiautomator.
Parsing is split into a pure function so it is unit-testable without a device.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .adb import run_adb
from .config import Config

_FOCUS_RE = re.compile(r"mCurrentFocus=.*?([\w.]+)/")


@dataclass(frozen=True)
class DeviceState:
    battery_level: int | None
    battery_temp_c: float | None
    screen_awake: bool | None
    foreground: str | None


def parse_state(battery: str, power: str, window: str) -> DeviceState:
    """Parse raw dumpsys output into a :class:`DeviceState`."""
    level = temp = None
    if m := re.search(r"level:\s*(\d+)", battery):
        level = int(m.group(1))
    if m := re.search(r"temperature:\s*(\d+)", battery):
        temp = int(m.group(1)) / 10.0

    awake = None
    if m := re.search(r"mWakefulness=(\w+)", power):
        awake = m.group(1).lower() == "awake"

    fg = None
    if m := _FOCUS_RE.search(window):
        fg = m.group(1)

    return DeviceState(battery_level=level, battery_temp_c=temp, screen_awake=awake, foreground=fg)


async def _shell(cfg: Config, args: list[str], serial: str | None) -> str:
    result = await run_adb(
        ["shell", *args],
        binary=cfg.adb_binary,
        serial=serial or cfg.default_serial,
        timeout=cfg.adb_timeout,
    )
    return result.text


async def get_state(cfg: Config, serial: str | None = None) -> DeviceState:
    battery = await _shell(cfg, ["dumpsys", "battery"], serial)
    power = await _shell(cfg, ["dumpsys", "power"], serial)
    window = await _shell(cfg, ["dumpsys", "window"], serial)
    return parse_state(battery, power, window)


def format_state(state: DeviceState) -> str:
    parts = []
    if state.battery_level is not None:
        temp = f", {state.battery_temp_c:.1f}°C" if state.battery_temp_c is not None else ""
        parts.append(f"battery {state.battery_level}%{temp}")
    if state.screen_awake is not None:
        parts.append("screen awake" if state.screen_awake else "screen off")
    if state.foreground:
        parts.append(f"foreground: {state.foreground}")
    return " | ".join(parts) or "(no state)"
