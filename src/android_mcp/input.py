"""Input primitives: taps, swipes, typing, key events. All async, all via adb."""

from __future__ import annotations

from .adb import run_adb
from .config import Config

_KEYCODES = {
    "back": 4,
    "home": 3,
    "recents": 187,
    "menu": 82,
    "power": 26,
    "wakeup": 224,
    "sleep": 223,
    "volume_up": 24,
    "volume_down": 25,
    "enter": 66,
    "delete": 67,
    "camera": 27,
    "call": 5,
}


async def _shell(cfg: Config, args: list[str], serial: str | None) -> str:
    result = await run_adb(
        ["shell", *args],
        binary=cfg.adb_binary,
        serial=serial or cfg.default_serial,
        timeout=cfg.adb_timeout,
    )
    blob = result.text + result.stderr.decode("utf-8", "replace")
    if "INJECT_EVENTS" in blob or "SecurityException" in blob:
        raise RuntimeError(
            "input injection blocked by this ROM (INJECT_EVENTS). "
            "On MIUI enable 'USB debugging (Security settings)' or grant root."
        )
    if not result.ok:
        raise RuntimeError(f"adb shell failed ({result.returncode}): {blob.strip()}")
    return result.text.strip()


async def tap(cfg: Config, x: int, y: int, serial: str | None = None) -> str:
    await _shell(cfg, ["input", "tap", str(x), str(y)], serial)
    return f"tapped ({x}, {y})"


async def swipe(
    cfg: Config,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    duration_ms: int = 300,
    serial: str | None = None,
) -> str:
    await _shell(
        cfg,
        ["input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)],
        serial,
    )
    return f"swiped ({x1},{y1})->({x2},{y2}) in {duration_ms}ms"


async def type_text(cfg: Config, text: str, serial: str | None = None) -> str:
    # adb `input text` uses %s for spaces; escape is done by the caller for specials.
    escaped = text.replace(" ", "%s")
    await _shell(cfg, ["input", "text", escaped], serial)
    return f"typed {len(text)} chars"


async def press_key(cfg: Config, key: str, serial: str | None = None) -> str:
    code = _KEYCODES.get(key)
    if code is None:
        try:
            code = int(key)
        except ValueError:
            raise ValueError(f"unknown key '{key}'; known: {', '.join(_KEYCODES)}") from None
    await _shell(cfg, ["input", "keyevent", str(code)], serial)
    return f"key {key} ({code})"


async def wake(cfg: Config, serial: str | None = None) -> str:
    await _shell(cfg, ["input", "keyevent", str(_KEYCODES["wakeup"])], serial)
    return "screen woken"
