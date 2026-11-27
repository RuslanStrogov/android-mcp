"""End-to-end smoke test: connect to the android-mcp server over MCP (stdio)
and exercise the tools, exactly like a real AI client would.

Usage:
    ANDROID_MCP_SERIAL=192.168.10.210:5555 python scripts/smoke_mcp.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> int:
    env = dict(os.environ)
    env.setdefault("ANDROID_MCP_SERIAL", "")
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "android_mcp"],
        env=env,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = sorted(t.name for t in tools.tools)
            print(f"[tools] {len(names)}: {', '.join(names)}")

            res = await session.call_tool("device_list", {})
            print(f"[device_list]\n{res.content[0].text}")

            res = await session.call_tool("screenshot", {})
            block = res.content[0]
            data = getattr(block, "data", "")
            print(f"[screenshot] type={block.type} base64_chars={len(data)}")

            res = await session.call_tool("device_capabilities", {})
            print(f"[device_capabilities]\n{res.content[0].text}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
