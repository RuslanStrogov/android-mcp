"""Device model and adb ``devices`` output parsing (pure, testable)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Device:
    serial: str
    state: str  # "device", "offline", "unauthorized", ...
    model: str | None = None


def parse_devices(output: str) -> list[Device]:
    """Parse ``adb devices -l`` output into a list of :class:`Device`."""
    devices: list[Device] = []
    for raw in output.splitlines():
        line = raw.rstrip()
        if not line or line.startswith("List of devices"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        model = None
        for token in parts[2:]:
            if token.startswith("model:"):
                model = token.split(":", 1)[1]
        devices.append(Device(serial=serial, state=state, model=model))
    return devices
