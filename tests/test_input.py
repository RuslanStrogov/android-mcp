"""Unit tests for input helpers (pure functions, no device)."""

from __future__ import annotations

import pytest

from android_mcp.input import escape_text, resolve_keycode


def test_escape_text_spaces_become_percent_s() -> None:
    assert escape_text("hello world") == "hello%sworld"
    assert escape_text("a b c") == "a%sb%sc"


def test_escape_text_without_spaces_unchanged() -> None:
    assert escape_text("abc123") == "abc123"


def test_resolve_keycode_named() -> None:
    assert resolve_keycode("home") == 3
    assert resolve_keycode("back") == 4
    assert resolve_keycode("wakeup") == 224


def test_resolve_keycode_numeric_passthrough() -> None:
    assert resolve_keycode("66") == 66


def test_resolve_keycode_unknown_raises() -> None:
    with pytest.raises(ValueError, match="unknown key"):
        resolve_keycode("nope")
