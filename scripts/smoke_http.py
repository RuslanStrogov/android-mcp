"""Smoke test for the HTTP transport: start the server on HTTP, connect a client.

Usage:
    python scripts/smoke_http.py            # spawns the server itself
    python scripts/smoke_http.py <url>      # connect to an already-running server
"""

from __future__ import annotations

import asyncio
import os
import sys
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

HOST = os.environ.get("ANDROID_MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("ANDROID_MCP_PORT", "8811"))


async def _client(url: str) -> int:
    async with AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(streamable_http_client(url))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        tools = await session.list_tools()
        names = sorted(t.name for t in tools.tools)
        print(f"[http] connected, {len(names)} tools: {', '.join(names)}")
        res = await session.call_tool("device_list", {})
        print(f"[http] device_list -> {res.content[0].text!r}")
    return 0


async def main() -> int:
    if len(sys.argv) > 1:
        return await _client(sys.argv[1])

    env = dict(os.environ)
    env.setdefault("ANDROID_MCP_SERIAL", "")
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "android_mcp",
        "--transport",
        "streamable-http",
        "--host",
        HOST,
        "--port",
        str(PORT),
        env=env,
    )
    try:
        await asyncio.sleep(2.0)  # wait for startup
        return await _client(f"http://{HOST}:{PORT}/mcp")
    finally:
        proc.terminate()
        await proc.wait()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
