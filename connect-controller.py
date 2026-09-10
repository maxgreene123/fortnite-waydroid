#!/usr/bin/env python3
"""Check the Xbox controller in Waydroid and expose its missing input node."""

import os
from pathlib import Path
import shlex
import stat
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
    candidates = []
    for event in Path("/sys/class/input").glob("event*"):
        name = (event / "device/name").read_text().strip()
        if "Xbox" in name:
            candidates.append((event.name, name))
    if len(candidates) != 1:
        raise SystemExit(f"Expected one connected Xbox controller; found {len(candidates)}.")
    event, name = candidates[0]
    device = Path("/dev/input") / event
    info = device.stat()
    if not stat.S_ISCHR(info.st_mode):
        raise SystemExit("Controller path is not a character device.")
    if subprocess.run(["sudo", "-v"]).returncode:
        raise SystemExit("Sudo authentication failed.")
    output = Path(__file__).resolve().parent / ".diagnostics"
    output.mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="controller-", dir=output))
    before = android("dumpsys", "input")
    (output / "input-before.txt").write_text(before)
    (output / "nodes-before.txt").write_text(android("ls", "-l", "/dev/input"))
    if name not in before:
        # EventHub watches IN_CREATE, not IN_MOVED_TO. A hard link publishes
        # the prepared node with the correct event and permissions together.
        target = shlex.quote(str(device))
        alias = shlex.quote(f"/dev/input/fortnite-controller-{event}")
        script = f"""set -e
staging=$(mktemp -d /dev/fortnite-controller.XXXXXX)
trap 'rm -rf "$staging"' EXIT
mknod "$staging/controller" c {os.major(info.st_rdev)} {os.minor(info.st_rdev)}
chown 0:1004 "$staging/controller"
chmod 660 "$staging/controller"
if [ -e {target} ]; then
    if [ -e {alias} ]; then
        echo 'Repair node already exists; collecting diagnostics without changing it.'
    else
        ln "$staging/controller" {alias}
        echo 'Published controller node with an Android device-create event.'
    fi
else
    ln "$staging/controller" {target}
    echo 'Added controller node for this Waydroid session: {device}'
fi
"""
        print(android("sh", "-c", script), end="")
    for _ in range(5):
        after = android("dumpsys", "input")
        if name in after:
            print(f"Android now detects: {name}. Try D-pad and A in Fortnite.")
            break
        time.sleep(1)
    else:
        print("Android still does not detect the controller. Diagnostics saved for review.")
    (output / "input-after.txt").write_text(after)
    (output / "nodes-after.txt").write_text(android("ls", "-lZ", "/dev/input"))
    (output / "logcat.txt").write_text(android("logcat", "-b", "all", "-d", "-t", "1000"))
    print(f"Diagnostics: {output}")


if __name__ == "__main__":
    main()
