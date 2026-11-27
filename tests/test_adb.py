"""Tests for the adb result wrapper."""

from __future__ import annotations

from android_mcp.adb import AdbResult


def test_ok_true_on_zero_exit() -> None:
    r = AdbResult(stdout=b"ok\n", stderr=b"", returncode=0)
    assert r.ok is True
    assert r.text == "ok\n"


def test_ok_false_on_nonzero_exit() -> None:
    r = AdbResult(stdout=b"", stderr=b"boom", returncode=1)
    assert r.ok is False


def test_text_decodes_with_replacement() -> None:
    r = AdbResult(stdout=b"\xff", stderr=b"", returncode=0)
    assert r.text == "\ufffd"
