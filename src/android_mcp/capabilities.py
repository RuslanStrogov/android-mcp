"""Capability probe ("doctor"): what actually works on the connected device/ROM.

Some ROMs (notably MIUI) block input injection (`INJECT_EVENTS`) and can make
`uiautomator dump` fail. Rather than hang or return cryptic errors, the server
probes capabilities and tells the agent (and the human) what is available.
"""

from __future__ import annotations

from .adb import run_adb
from .capture import dump_ui_xml, screenshot_png
from .config import Config

_INJECT_HINTS = ("INJECT_EVENTS", "SecurityException", "Injecting to another application")


async def probe(cfg: Config, serial: str | None = None) -> dict[str, dict[str, str | bool]]:
    """Return {capability: {ok: bool, note: str}} for the target device."""
    target = serial or cfg.default_serial
    report: dict[str, dict[str, str | bool]] = {}

    # screenshot
    try:
        png = await screenshot_png(cfg, serial=target)
        report["screenshot"] = {"ok": bool(png), "note": f"{len(png)} bytes PNG"}
    except Exception as exc:  # noqa: BLE001 - report, don't crash
        report["screenshot"] = {"ok": False, "note": str(exc)}

    # input injection
    res = await run_adb(
        ["shell", "input", "tap", "1", "1"],
        binary=cfg.adb_binary,
        serial=target,
        timeout=cfg.adb_timeout,
    )
    blob = res.text + res.stderr.decode("utf-8", "replace")
    blocked = any(h in blob for h in _INJECT_HINTS)
    if blocked:
        report["input_inject"] = {
            "ok": False,
            "note": "blocked by ROM — enable 'USB debugging (Security settings)' "
            "(MIUI) or grant root",
        }
    else:
        report["input_inject"] = {"ok": True, "note": "tap/swipe/type/keyevent available"}

    # ui hierarchy
    try:
        xml = await dump_ui_xml(cfg, serial=target, retries=2, timeout=10.0)
        report["ui_dump"] = {"ok": True, "note": f"{len(xml)} bytes XML"}
    except Exception as exc:  # noqa: BLE001
        report["ui_dump"] = {"ok": False, "note": str(exc)}

    # app control (foreground query is a cheap proxy)
    res = await run_adb(
        ["shell", "dumpsys", "window"],
        binary=cfg.adb_binary,
        serial=target,
        timeout=cfg.adb_timeout,
    )
    report["app_control"] = {"ok": "mCurrentFocus" in res.text, "note": "monkey/am available"}

    return report


def format_report(report: dict[str, dict[str, str | bool]]) -> str:
    lines = []
    for name, info in report.items():
        mark = "✅" if info["ok"] else "❌"
        lines.append(f"{mark} {name}: {info['note']}")
    return "\n".join(lines)
