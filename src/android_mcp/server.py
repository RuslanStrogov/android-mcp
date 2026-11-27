"""MCP server: registers the tools exposed to AI clients.

Stage 0/1 scaffold — exposes ``device_list`` and ``screenshot`` (returned as an
actual image, not a file path). More tools are added per the roadmap in PLAN.md.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP, Image

from .adb import run_adb
from .config import Config
from .device import parse_devices


def build_server(config: Config | None = None) -> FastMCP:
    """Create and configure the MCP server instance."""
    cfg = config or Config.from_env()
    app = FastMCP("android-mcp")

    @app.tool()
    async def device_list() -> str:
        """List connected Android devices (USB or wireless ADB)."""
        result = await run_adb(
            ["devices", "-l"],
            binary=cfg.adb_binary,
            timeout=cfg.adb_timeout,
            check=True,
        )
        devices = parse_devices(result.text)
        if not devices:
            return "No devices connected. Use wireless ADB: adb pair / adb connect."
        lines = []
        for dev in devices:
            model = f"  {dev.model.replace('_', ' ')}" if dev.model else ""
            lines.append(f"{dev.serial}  [{dev.state}]{model}")
        return "\n".join(lines)

    @app.tool()
    async def screenshot(serial: str | None = None) -> Image:
        """Capture the device screen and return it as a PNG image."""
        result = await run_adb(
            ["exec-out", "screencap", "-p"],
            binary=cfg.adb_binary,
            serial=serial or cfg.default_serial,
            timeout=cfg.adb_timeout,
            check=True,
        )
        return Image(data=result.stdout, format="png")

    return app
