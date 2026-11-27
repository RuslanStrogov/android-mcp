#!/usr/bin/env bash
# Provision an Android test device for android-mcp.
#
# Usage:
#   scripts/provision.sh                 # use the single connected device
#   scripts/provision.sh <serial>        # target a specific serial / ip:port
#
# Re-applies the settings that get lost on reboot / factory reset:
#   * keep awake while charging   (svc power stayon)
#   * disable lockscreen          (locksettings set-disabled)
#   * low screen brightness       (screen_brightness)
#   * wireless ADB on port 5555   (adb tcpip)  -- Android <11 legacy method
#
# Manual steps NOT doable over adb (ROM-gated):
#   * MIUI: enable "USB debugging (Security settings)" to allow input injection
#   * Android 11+: use "Wireless debugging" pairing instead of `adb tcpip`
set -euo pipefail

ADB="${ADB:-adb}"
SERIAL="${1:-}"

if [[ -n "$SERIAL" ]]; then
  S=(-s "$SERIAL")
else
  S=()
fi

echo "== waiting for a device =="
"$ADB" "${S[@]}" wait-for-device
"$ADB" "${S[@]}" get-state

model="$("$ADB" "${S[@]}" shell getprop ro.product.model | tr -d '\r')"
rel="$("$ADB" "${S[@]}" shell getprop ro.build.version.release | tr -d '\r')"
echo "== device: $model (Android $rel) =="

echo "== keep awake while charging =="
"$ADB" "${S[@]}" shell svc power stayon true

echo "== disable lockscreen =="
"$ADB" "${S[@]}" shell locksettings set-disabled true || true

echo "== low brightness (screen longevity) =="
"$ADB" "${S[@]}" shell settings put system screen_brightness_mode 0 || true
"$ADB" "${S[@]}" shell settings put system screen_brightness 10 || true

echo "== wake + home =="
"$ADB" "${S[@]}" shell input keyevent 224 || true

echo "== wireless ADB (legacy tcpip; skip on Android 11+) =="
"$ADB" "${S[@]}" tcpip 5555 || true
ip="$("$ADB" "${S[@]}" shell ip -4 addr show wlan0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | tr -d '\r')"
if [[ -n "$ip" ]]; then
  echo "   connect with: adb connect ${ip}:5555"
fi

echo "== done. Manual (if needed): MIUI -> 'USB debugging (Security settings)' =="
