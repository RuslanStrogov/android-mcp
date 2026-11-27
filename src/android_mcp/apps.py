"""App management: launch, stop, list. Minimal stage-1 surface."""

from __future__ import annotations

from .adb import run_adb
from .config import Config


async def launch(cfg: Config, package: str, serial: str | None = None) -> str:
    result = await run_adb(
        ["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"],
        binary=cfg.adb_binary,
        serial=serial or cfg.default_serial,
        timeout=cfg.adb_timeout,
        check=True,
    )
    if "No activities found" in result.text or "monkey aborted" in result.text.lower():
        raise RuntimeError(f"could not launch {package}: {result.text.strip()}")
    return f"launched {package}"


async def stop(cfg: Config, package: str, serial: str | None = None) -> str:
    await run_adb(
        ["shell", "am", "force-stop", package],
        binary=cfg.adb_binary,
        serial=serial or cfg.default_serial,
        timeout=cfg.adb_timeout,
        check=True,
    )
    return f"force-stopped {package}"


async def list_packages(
    cfg: Config, contains: str | None = None, serial: str | None = None
) -> list[str]:
    result = await run_adb(
        ["shell", "pm", "list", "packages", "--user", "0"],
        binary=cfg.adb_binary,
        serial=serial or cfg.default_serial,
        timeout=cfg.adb_timeout,
        check=True,
    )
    packages = [
        ln.removeprefix("package:").strip()
        for ln in result.text.splitlines()
        if ln.startswith("package:")
    ]
    if contains:
        needle = contains.lower()
        packages = [p for p in packages if needle in p.lower()]
    return sorted(packages)
