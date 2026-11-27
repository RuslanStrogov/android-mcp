"""Entrypoint: ``python -m android_mcp`` or the ``android-mcp`` console script.

Transports:
  * stdio (default)            — for local MCP clients (Hermes, Claude, Cursor)
  * streamable-http            — for remote agents (over LAN / VPN / Tailscale)
  * sse                        — legacy remote transport
"""

from __future__ import annotations

import argparse
import os

from .server import build_server


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="android-mcp",
        description="MCP server for controlling Android devices over ADB (Wi-Fi/USB).",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default=os.environ.get("ANDROID_MCP_TRANSPORT", "stdio"),
        help="MCP transport to serve on (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("ANDROID_MCP_HOST", "127.0.0.1"),
        help="bind host for HTTP transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("ANDROID_MCP_PORT", "8000")),
        help="bind port for HTTP transports (default: 8000)",
    )
    args = parser.parse_args()

    app = build_server()
    if args.transport == "stdio":
        app.run("stdio")
    elif args.transport == "sse":
        app.run("sse", host=args.host, port=args.port)
    else:
        app.run("streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
