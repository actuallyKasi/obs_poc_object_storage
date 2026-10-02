#!/usr/bin/env python3
"""Install the pinned official Symphony executable into this repo's ignored .tools."""
import hashlib
import os
import platform
from pathlib import Path
import urllib.request

VERSION = "v0.0.3"
ROOT = Path(__file__).resolve().parents[2]


def main():
    system = {"Darwin": "macos", "Linux": "linux"}.get(platform.system())
    arch = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x86_64"}.get(platform.machine())
    if not system or not arch:
        raise SystemExit("Unsupported Symphony release platform")
    name = f"symphony-{VERSION}-{system}_{arch}"
    base = f"https://github.com/openai/symphony/releases/download/{VERSION}/{name}"
    target = ROOT / ".tools" / "symphony" / name
    expected = urllib.request.urlopen(base + ".sha256", timeout=60).read().decode().split()[0]
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
        print(f"Verified existing executable: {target}")
        return
    payload = urllib.request.urlopen(base, timeout=60).read()
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise SystemExit("Release checksum mismatch; executable not installed")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_suffix(".download")
    staging.write_bytes(payload)
    staging.chmod(0o755)
    os.replace(staging, target)
    print(f"Installed {target}\nSHA256 {actual}")


if __name__ == "__main__":
    main()
