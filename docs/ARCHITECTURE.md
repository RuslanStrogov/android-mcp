# Architecture

> See also [`PLAN.md`](../PLAN.md) for the roadmap and sub-product variants.

## Overview

```
AI client (Hermes / Cursor / Claude / …)
        │  MCP  (JSON-RPC 2.0 over stdio)
        ▼
  android-mcp  (Python 3.11+, asyncio)
        │  adb  (wireless / USB)
        ▼
  Android device
```

The server is an MCP **tool provider**: it exposes tools, the client's LLM decides
which to call. No business logic lives in the client — the server is universal.

## Layers

1. **Transport** — `server.py` speaks MCP to the client over stdio (HTTP/SSE optional).
2. **Tool layer** — thin, typed wrappers mapping MCP tool calls to device ops.
3. **Device layer** — `adb.py` (async subprocess) + `device.py` (device selection,
   multi-device). All device I/O goes through here.
4. **Domain modules** — `ui.py` (uiautomator XML parsing), `gestures.py`
   (`input` + `sendevent` injection), `screenshot.py`, `apps.py`, `sources.py`.
5. **Policy** — `security.py` (approval-gate), `config.py` (no hardcoded paths).

## Design rules

- **Non-blocking**: every `adb` call is an `asyncio` subprocess; never `spawnSync`-style blocking.
- **Screenshot = image content**: return `ImageContent` (base64 PNG), not a file path.
- **Multi-device first**: every tool accepts an optional device serial.
- **No secrets at rest**: never store plaintext credentials; defer to OS keyring if needed.
- **Configurable**: paths, adb binary, timeouts via config/env — no magic constants.
- **Fail loud**: typed errors surfaced to the client, not silent empty strings.
