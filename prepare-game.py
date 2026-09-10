#!/usr/bin/env python3
"""Disable Android debugging and collect graphics evidence without spoofing hardware."""

import json
from pathlib import Path
import subprocess
import tempfile
import time


def android(*args):
    result = subprocess.run(
        ["sudo", "-n", "waydroid", "shell", "--", *args],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, timeout=30,
    )
    if result.returncode:
        raise SystemExit(result.stdout)
    return result.stdout


def main():
    boot = subprocess.check_output(
        ["waydroid", "prop", "get", "sys.boot_completed"], text=True,
    ).strip()
    if boot != "1":
        raise SystemExit("Start Waydroid full UI and wait for Android to finish booting first.")
    if subprocess.run(["sudo", "-v"]).returncode:
        raise SystemExit("Sudo authentication failed.")
    root = Path(__file__).resolve().parent / ".diagnostics"
    root.mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="graphics-", dir=root))
    settings = ("adb_enabled", "adb_wifi_enabled", "development_settings_enabled")
    previous = {key: android("settings", "get", "global", key).strip()
                for key in settings}
    previous["persist.sys.usb.config"] = android("getprop", "persist.sys.usb.config").strip()
    (output / "debugging-before.json").write_text(json.dumps(previous, indent=2) + "\n")
    for key in settings:
        android("settings", "put", "global", key, "0")
    # Remove ADB from the persistent USB configuration while keeping other USB
    # functions. Waydroid's local LXC shell does not depend on ADB.
    functions = [part for part in previous["persist.sys.usb.config"].split(",")
                 if part and part not in ("adb", "none")]
    android("setprop", "persist.sys.usb.config", ",".join(functions) or "none")
    android("stop", "adbd")
    time.sleep(2)
    current = {key: android("settings", "get", "global", key).strip()
               for key in settings}
    current["init.svc.adbd"] = android("getprop", "init.svc.adbd").strip()
    current["persist.sys.usb.config"] = android("getprop", "persist.sys.usb.config").strip()
    (output / "debugging-after.json").write_text(json.dumps(current, indent=2) + "\n")
    for key, value in current.items():
        print(f"{key}: {value}", flush=True)
    surface = android("dumpsys", "SurfaceFlinger")
    (output / "surfaceflinger.txt").write_text(surface)
    for line in surface.splitlines():
        if "GLES:" in line:
            print(line.strip(), flush=True)
    reports = {
        "display.txt": ("dumpsys", "display"),
        "resolution.txt": ("wm", "size"),
        "thermal.txt": ("dumpsys", "thermalservice"),
        "graphics-properties.txt": ("sh", "-c", "getprop | grep -iE 'egl|vulkan|gralloc|native.bridge|ndk_translation|debuggable'"),
        "logcat.txt": ("logcat", "-b", "all", "-d", "-t", "1500"),
    }
    for name, args in reports.items():
        (output / name).write_text(android(*args))
    print(f"Diagnostics: {output}")
    if any(current[key] != "0" for key in settings) or current["init.svc.adbd"] not in ("", "stopped"):
        raise SystemExit("Debugging did not fully stop. Review diagnostics before retrying Fortnite.")
    android("am", "force-stop", "com.epicgames.fortnite")
    subprocess.run(["waydroid", "app", "launch", "com.epicgames.fortnite"], check=True)
    print("Debugging disabled; Fortnite relaunched. Matchmaking and performance still need testing.")


if __name__ == "__main__":
    main()
