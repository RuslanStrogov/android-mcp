"""Unit tests for the uiautomator XML parser and element matching (no device needed)."""

from __future__ import annotations

from android_mcp.ui import find_by_text, format_elements, parse_ui

SAMPLE = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" bounds="[0,0][1080,2340]">
    <node index="0" text="Sign in" resource-id="com.app:id/title" class="android.widget.TextView" clickable="false" enabled="true" bounds="[40,200][600,260]" />
    <node index="1" text="" content-desc="Email" resource-id="com.app:id/email" class="android.widget.EditText" focusable="true" clickable="true" enabled="true" bounds="[40,300][1040,380]" />
    <node index="2" text="Continue" resource-id="com.app:id/continue" class="android.widget.Button" clickable="true" enabled="true" bounds="[40,400][1040,480]" />
    <node index="3" text="" resource-id="com.app:id/decoration" class="android.widget.ImageView" clickable="false" enabled="true" bounds="[0,0][10,10]" />
  </node>
</hierarchy>
"""


def test_parse_ui_keeps_interactive_only() -> None:
    elements = parse_ui(SAMPLE)
    ids = [e.resource_id.split("/")[-1] for e in elements]
    assert "email" in ids  # EditText (focusable)
    assert "continue" in ids  # Button (interactive class)
    assert "decoration" not in ids  # no text/desc/id/clickable → skipped


def test_element_center_and_flags() -> None:
    elements = {e.resource_id.split("/")[-1]: e for e in parse_ui(SAMPLE)}
    btn = elements["continue"]
    assert btn.bounds.center == (540, 440)
    assert btn.clickable is True
    assert btn.enabled is True


def test_find_by_text() -> None:
    elements = parse_ui(SAMPLE)
    assert find_by_text(elements, "sign in") is not None
    assert find_by_text(elements, "continue") is not None
    assert find_by_text(elements, "nonexistent") is None


def test_format_elements_renders_lines() -> None:
    out = format_elements(parse_ui(SAMPLE))
    assert "Continue" in out
    assert "@540,440" in out


def test_parse_ui_empty() -> None:
    assert parse_ui("<hierarchy/>") == []
