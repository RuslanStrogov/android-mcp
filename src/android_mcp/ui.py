"""Parse `uiautomator dump` XML into a flat list of interactive elements.

Pure functions — no I/O — so this is fully unit-testable without a device.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_NODE_RE = re.compile(r"<node\b([^>]*?)/?>")
_BOUNDS_RE = re.compile(r"bounds=\"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\"")
_ATTR_RE = re.compile(r"([\w-]+)=\"([^\"]*)\"")

INTERACTIVE_CLASSES = {
    "android.widget.Button",
    "android.widget.ImageButton",
    "android.widget.EditText",
    "android.widget.CheckBox",
    "android.widget.Switch",
    "android.widget.RadioButton",
    "android.widget.Spinner",
    "android.widget.SeekBar",
}

_FLAG_ATTRS = (
    "focusable",
    "clickable",
    "long-clickable",
    "checkable",
    "scrollable",
    "selected",
    "password",
)


@dataclass(frozen=True)
class Bounds:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def center(self) -> tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)


@dataclass(frozen=True)
class Element:
    index: int
    text: str
    desc: str
    resource_id: str
    class_name: str
    bounds: Bounds
    clickable: bool
    long_clickable: bool
    scrollable: bool
    checkable: bool
    checked: bool
    focused: bool
    enabled: bool
    password: bool


def _attrs(raw: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in _ATTR_RE.finditer(raw)}


def _is_interactive(a: dict[str, str]) -> bool:
    if any(a.get(flag) == "true" for flag in _FLAG_ATTRS):
        return True
    return a.get("class", "") in INTERACTIVE_CLASSES


def parse_ui(xml: str) -> list[Element]:
    """Parse UI XML into interactive :class:`Element` objects."""
    elements: list[Element] = []
    index = 0
    for match in _NODE_RE.finditer(xml):
        a = _attrs(match.group(1))
        bm = _BOUNDS_RE.search(match.group(1))
        if not bm:
            continue
        text = a.get("text", "")
        desc = a.get("content-desc", "")
        # Keep interactive nodes AND any node with a visible label (text/description),
        # so the agent can read the screen, not just tap it.
        if not _is_interactive(a) and not text and not desc:
            continue
        bounds = Bounds(*(int(v) for v in bm.groups()))
        rid = a.get("resource-id", "")
        elements.append(
            Element(
                index=index,
                text=text,
                desc=desc,
                resource_id=rid,
                class_name=a.get("class", ""),
                bounds=bounds,
                clickable=a.get("clickable") == "true",
                long_clickable=a.get("long-clickable") == "true",
                scrollable=a.get("scrollable") == "true",
                checkable=a.get("checkable") == "true",
                checked=a.get("checked") == "true",
                focused=a.get("focused") == "true",
                enabled=a.get("enabled") == "true",
                password=a.get("password") == "true",
            )
        )
        index += 1
    return elements


def format_elements(elements: list[Element], limit: int = 300) -> str:
    """Human/LLM-readable rendering of the elements."""
    lines: list[str] = []
    for el in elements[:limit]:
        cx, cy = el.bounds.center
        flags = []
        if el.clickable:
            flags.append("clickable")
        if el.scrollable:
            flags.append("scrollable")
        if el.password:
            flags.append("password")
        if el.focused:
            flags.append("focused")
        if not el.enabled:
            flags.append("disabled")
        label = el.text or el.desc or ""
        rid = el.resource_id.split("/")[-1] if el.resource_id else ""
        parts = [f"#{el.index}", f"@{cx},{cy}"]
        if label:
            parts.append(f'"{label}"')
        if rid:
            parts.append(f"id={rid}")
        if flags:
            parts.append("[" + ",".join(flags) + "]")
        lines.append(" ".join(parts))
    if not lines:
        return "(no interactive elements)"
    if len(elements) > limit:
        lines.append(f"... {len(elements) - limit} more truncated")
    return "\n".join(lines)


def find_by_text(elements: list[Element], text: str) -> Element | None:
    """First element whose text or description contains ``text`` (case-insensitive)."""
    needle = text.lower()
    for el in elements:
        if needle in el.text.lower() or needle in el.desc.lower():
            return el
    return None
