# Tool Reference

Detailed reference for every tool `android-mcp` exposes. All tools accept an optional
`serial` argument to target a specific device (otherwise `ANDROID_MCP_SERIAL`, else the
single connected device).

## Device

### `device_list`
List connected Android devices (USB and wireless ADB).
→ text: one line per device: `<serial>  [<state>]  <model>`.

### `device_state`
Read-only state. No input injection needed (works on restricted ROMs).
→ text: `battery 29%, 19.0°C | screen awake | foreground: com.android.settings`.

### `device_capabilities`
Doctor: probes what the ROM actually allows.
→ text: `✅/❌` per capability — `screenshot`, `input_inject`, `ui_dump`, `app_control`.
Use it first on a new device.

## Screen

### `screenshot`
Capture the screen, returned as **image content** (the model sees the picture).
→ image (PNG).

### `dump_ui`
UI hierarchy as text: `#index  @x,y  "label"  id=...  [flags]`.
Interactive nodes and any node with a visible label are included.
⚠️ Some ROMs (MIUI) fail with "could not get idle state"; prefer `screenshot`.

## Input

| Tool | Args | Notes |
|---|---|---|
| `tap` | `x`, `y` | absolute screen coordinates (px) |
| `tap_text` | `text` | find element by text/description, tap its center |
| `swipe` | `x1`, `y1`, `x2`, `y2`, `duration_ms=300` | |
| `type_text` | `text` | types into the focused field |
| `press_key` | `key` | `back`,`home`,`recents`,`menu`,`power`,`wakeup`,`enter`,`delete`,`volume_up`,`volume_down`,`camera`,`call`, or a numeric keycode |
| `wake` | — | wake the screen |

⚠️ On ROMs that block `INJECT_EVENTS` (MIUI without "USB debugging (Security settings)")
these raise a clear error. Check `device_capabilities` first.

## Apps

| Tool | Args | Notes |
|---|---|---|
| `app_launch` | `package` | launch by package (via monkey) |
| `app_stop` | `package` | force-stop |
| `app_list` | `contains` (optional) | list installed packages, filtered by substring |
