"""Async wrapper around the ``adb`` binary.

Every device interaction goes through here. Non-blocking: uses
``asyncio.create_subprocess_exec`` (never a blocking ``subprocess.run``).
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class AdbResult:
    stdout: bytes
    stderr: bytes
    returncode: int

    @property
    def text(self) -> str:
        return self.stdout.decode("utf-8", "replace")

    @property
    def ok(self) -> bool:
        return self.returncode == 0


async def run_adb(
    args: Sequence[str],
    *,
    binary: str = "adb",
    serial: str | None = None,
    timeout: float = 30.0,
    check: bool = False,
) -> AdbResult:
    """Run ``adb <args>`` and return its output.

    Args:
        args: adb arguments (without the binary or ``-s`` serial).
        binary: path/name of the adb executable.
        serial: target device serial; adds ``-s <serial>`` when set.
        timeout: seconds before the command is killed.
        check: raise ``RuntimeError`` on a non-zero exit code.
    """
    cmd = [binary]
    if serial:
        cmd += ["-s", serial]
    cmd += list(args)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise TimeoutError(f"adb command timed out after {timeout}s: {' '.join(cmd)}") from None

    result = AdbResult(stdout, stderr, proc.returncode or 0)
    if check and not result.ok:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"adb failed ({result.returncode}): {detail}")
    return result
