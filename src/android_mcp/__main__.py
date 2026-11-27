"""Entrypoint: ``python -m android_mcp`` or the ``android-mcp`` console script."""

from __future__ import annotations

from .server import build_server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
