"""Screen capture helpers: screenshot (PNG) and UI hierarchy dump (with retry)."""

from __future__ import annotations

import asyncio

from .adb import run_adb
from .config import Config

_DUMP_PATH = "/sdcard/window_dump.xml"


async def screenshot_png(cfg: Config, serial: str | None = None) -> bytes:
    """Capture the framebuffer and return raw PNG bytes."""
    result = await run_adb(
        ["exec-out", "screencap", "-p"],
        binary=cfg.adb_binary,
        serial=serial or cfg.default_serial,
        timeout=cfg.adb_timeout,
        check=True,
    )
    if not result.stdout:
        raise RuntimeError("screencap returned empty output")
    return result.stdout


async def dump_ui_xml(
    cfg: Config, serial: str | None = None, retries: int = 4, timeout: float = 12.0
) -> str:
    """Dump the UI hierarchy, retrying on the transient 'could not get idle state' error."""
    target = serial or cfg.default_serial
    last = ""
    for attempt in range(retries):
        dump = await run_adb(
            ["shell", "uiautomator", "dump", "--compressed", _DUMP_PATH],
            binary=cfg.adb_binary,
            serial=target,
            timeout=timeout,
        )
        out = dump.text.strip()
        if dump.ok and "dumped to" in out:
            xml = await run_adb(
                ["shell", "cat", _DUMP_PATH],
                binary=cfg.adb_binary,
                serial=target,
                timeout=timeout,
                check=True,
            )
            if xml.text.strip():
                return xml.text
        last = out or "empty dump"
        await asyncio.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"uiautomator dump failed after {retries} attempts: {last}")
