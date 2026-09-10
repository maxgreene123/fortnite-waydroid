#!/usr/bin/env python3
"""Collect read-only Waydroid sign-in diagnostics into user-owned files."""

import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    if subprocess.run(["sudo", "-v"]).returncode:
        raise SystemExit("Sudo authentication failed; no diagnostics collected.")

    root = Path(__file__).resolve().parent / ".diagnostics"
    root.mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="signin-", dir=root))
    commands = {
        "status.txt": ["waydroid", "status"],
        "input.txt": ["sudo", "-n", "waydroid", "shell", "--", "dumpsys", "input"],
        "windows.txt": ["sudo", "-n", "waydroid", "shell", "--", "dumpsys", "window", "windows"],
        "activities.txt": ["sudo", "-n", "waydroid", "shell", "--", "dumpsys", "activity", "activities"],
        "logcat.txt": ["sudo", "-n", "waydroid", "logcat", "--", "-d", "-t", "2000"],
    }
    for filename, command in commands.items():
        # A pipe separates container stdout from the destination file. The
        # unprivileged parent owns every report, regardless of LXC fd changes.
        try:
            result = subprocess.run(command, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=30)
            report = result.stdout
            if result.returncode:
                report += f"\nCommand exit code: {result.returncode}\n".encode()
        except subprocess.TimeoutExpired as error:
            report = (error.stdout or b"") + b"\nDiagnostic timed out after 30 seconds.\n"
        (output / filename).write_bytes(report)
        print(f"Saved {filename}", flush=True)
    print(f"Diagnostics saved locally: {output}")


if __name__ == "__main__":
    main()
