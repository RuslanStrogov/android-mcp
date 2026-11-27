"""MCP server: registers the tools exposed to AI clients.

Stage 1 (MVP): device listing, screenshot (image), UI dump, input, app control.
"""

from __future__ import annotations

from mcp.server.mcpserver import Image, MCPServer

from . import apps, capabilities, capture, state
from . import input as input_ops
from .adb import run_adb
from .config import Config
from .device import parse_devices
from .ui import find_by_text, format_elements, parse_ui


def build_server(config: Config | None = None) -> MCPServer:
    """Create and configure the MCP server instance."""
    cfg = config or Config.from_env()
    app = MCPServer("android-mcp")

    async def _ui_text(serial: str | None) -> str:
        xml = await capture.dump_ui_xml(cfg, serial=serial)
        return format_elements(parse_ui(xml))

    @app.tool()
    async def device_list() -> str:
        """List connected Android devices (USB or wireless ADB)."""
        result = await run_adb(
            ["devices", "-l"], binary=cfg.adb_binary, timeout=cfg.adb_timeout, check=True
        )
        devices = parse_devices(result.text)
        if not devices:
            return "No devices connected. Wireless: adb connect <ip>:5555"
        return "\n".join(
            f"{d.serial}  [{d.state}]" + (f"  {d.model.replace('_', ' ')}" if d.model else "")
            for d in devices
        )

    @app.tool()
    async def screenshot(serial: str | None = None) -> Image:
        """Capture the device screen and return it as a PNG image."""
        png = await capture.screenshot_png(cfg, serial=serial)
        return Image(data=png, format="png")

    @app.tool()
    async def dump_ui(serial: str | None = None) -> str:
        """Return the screen's interactive elements as text (index, position, label)."""
        return await _ui_text(serial)

    @app.tool()
    async def tap(x: int, y: int, serial: str | None = None) -> str:
        """Tap at absolute screen coordinates (pixels)."""
        return await input_ops.tap(cfg, x, y, serial)

    @app.tool()
    async def tap_text(text: str, serial: str | None = None) -> str:
        """Find an element by its visible text/description and tap its center."""
        xml = await capture.dump_ui_xml(cfg, serial=serial)
        el = find_by_text(parse_ui(xml), text)
        if el is None:
            raise ValueError(f"no element matching '{text}'")
        cx, cy = el.bounds.center
        return await input_ops.tap(cfg, cx, cy, serial)

    @app.tool()
    async def swipe(
        x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300, serial: str | None = None
    ) -> str:
        """Swipe from (x1,y1) to (x2,y2) over duration_ms milliseconds."""
        return await input_ops.swipe(cfg, x1, y1, x2, y2, duration_ms, serial)

    @app.tool()
    async def type_text(text: str, serial: str | None = None) -> str:
        """Type text into the currently focused field."""
        return await input_ops.type_text(cfg, text, serial)

    @app.tool()
    async def press_key(key: str, serial: str | None = None) -> str:
        """Press a key: back, home, recents, menu, power, wakeup, enter, delete, volume, camera, call."""  # noqa: E501
        return await input_ops.press_key(cfg, key, serial)

    @app.tool()
    async def wake(serial: str | None = None) -> str:
        """Wake the screen (KEYCODE_WAKEUP)."""
        return await input_ops.wake(cfg, serial)

    @app.tool()
    async def app_launch(package: str, serial: str | None = None) -> str:
        """Launch an app by package name."""
        return await apps.launch(cfg, package, serial)

    @app.tool()
    async def app_stop(package: str, serial: str | None = None) -> str:
        """Force-stop an app by package name."""
        return await apps.stop(cfg, package, serial)

    @app.tool()
    async def app_list(contains: str | None = None, serial: str | None = None) -> str:
        """List installed packages (optionally filtered by substring)."""
        pkgs = await apps.list_packages(cfg, contains, serial)
        return "\n".join(pkgs) if pkgs else "no packages matched"

    @app.tool()
    async def device_state(serial: str | None = None) -> str:
        """Get read-only state: battery level/temperature, screen, foreground app."""
        return state.format_state(await state.get_state(cfg, serial))

    @app.tool()
    async def device_capabilities(serial: str | None = None) -> str:
        """Probe the device and report which automation capabilities actually work."""
        report = await capabilities.probe(cfg, serial)
        return capabilities.format_report(report)

    return app
