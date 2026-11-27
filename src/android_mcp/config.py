"""Runtime configuration. No hardcoded paths/magic constants — everything via env."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Server configuration, sourced from environment variables."""

    adb_binary: str = "adb"
    default_serial: str | None = None
    adb_timeout: float = 30.0

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            adb_binary=os.environ.get("ANDROID_MCP_ADB", "adb"),
            default_serial=os.environ.get("ANDROID_MCP_SERIAL") or None,
            adb_timeout=float(os.environ.get("ANDROID_MCP_ADB_TIMEOUT", "30")),
        )
