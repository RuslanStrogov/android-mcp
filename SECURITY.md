# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ |

## Reporting a Vulnerability

Open a private security advisory on GitHub
(https://github.com/RuslanStrogov/android-mcp/security/advisories/new)
or contact the maintainer directly: ruslan@strogov.com.

## Security model (important)

This server grants an AI agent **full control of an Android device over ADB**.
ADB access is equivalent to physical access — treat the channel accordingly:

- Run the server only on trusted networks, or bind it to loopback.
- Prefer reachability over an encrypted tunnel (WireGuard / Tailscale) rather than
  exposing the ADB port directly.
- On Android 11+ always use wireless-debugging **pairing** (`adb pair`) — never the
  legacy fixed-port `adb tcpip 5555` on an untrusted network.
- Dangerous operations (payments, deletions, sending messages) are gated behind an
  approval step (see `security.py`, roadmap stage 4).
