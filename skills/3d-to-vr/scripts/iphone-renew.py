#!/usr/bin/env python3
"""Historical Linux helper; the active Mac procedure is references/iphone-session.md.

Re-sign/install the three reviewed iPhone apps with an already authenticated xtool.

Manifest: {"udid": "...", "apps": [{"role": "kdeconnect", "path": "...ipa",
"sha256": "...", "bundle_id": "..."}, ...]}.
Paths are relative to the manifest. No passwords belong in the manifest.
This orchestrates xtool; it does not bypass provisioning limits.
"""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
import zipfile

ROLES = ("kdeconnect", "cardboard", "flat-headset")


def prepare(manifest_path):
    manifest = json.loads(manifest_path.read_text())
    udid = manifest["udid"]
    if not isinstance(udid, str) or not re.fullmatch(r"[A-Fa-f0-9-]{20,64}", udid):
        raise ValueError("Set the intended phone's UDID explicitly in the manifest")
    apps = manifest["apps"]
    if not isinstance(apps, list) or len(apps) != 3:
        raise ValueError("Exactly three apps are required")
    by_role = {app["role"]: app for app in apps}
    if set(by_role) != set(ROLES):
        raise ValueError("Required roles: kdeconnect, cardboard, flat-headset")
    prepared, identifiers = [], set()
    for role in ROLES:
        app = by_role[role]
        path = (manifest_path.parent / app["path"]).resolve(strict=True)
        if path.suffix.lower() != ".ipa" or not path.is_file():
            raise ValueError(f"{role}: expected an IPA file")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != app["sha256"]:
            raise ValueError(f"{role}: SHA-256 mismatch; obtain the reviewed release manifest")
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            infos = [name for name in names if re.fullmatch(r"Payload/[^/]+\.app/Info\.plist", name)]
            if len(infos) != 1:
                raise ValueError(f"{role}: expected one top-level application")
            if any(".appex/" in name or "/Watch/" in name for name in names):
                raise ValueError(f"{role}: this three-ID recipe requires a build without extensions or Watch apps")
            info = plistlib.loads(archive.read(infos[0]))
        bundle_id = info["CFBundleIdentifier"]
        if bundle_id != app["bundle_id"] or bundle_id in identifiers:
            raise ValueError(f"{role}: unexpected or duplicate bundle identifier")
        identifiers.add(bundle_id)
        prepared.append((role, path))
    return udid, prepared


def verify_signer(executable):
    result = subprocess.run([executable, "sparky-policy"], check=False, capture_output=True, text=True, timeout=20)
    if result.returncode or not result.stdout.splitlines() or result.stdout.splitlines()[0] != "sparky-shared-pairing-1":
        raise ValueError("Use the reviewed shared-pairing xtool build; stock xtool drops the required keychain group")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--xtool", default="xtool", help="Path to the reviewed xtool executable")
    parser.add_argument("--dry-run", action="store_true", help="Validate all inputs and print commands without running xtool")
    args = parser.parse_args()
    try:
        udid, prepared = prepare(args.manifest.resolve(strict=True))
        executable = shutil.which(args.xtool)
        if not executable:
            raise ValueError("xtool not found; install the reviewed Linux release first")
        if not args.dry_run:
            verify_signer(executable)
        for role, path in prepared:
            command = [executable, "install", "--usb", "--udid", udid, str(path)]
            if args.dry_run:
                print(shlex.join(command))
                continue
            print(f"Renewing {role}", flush=True)
            result = subprocess.run(command, check=False)
            if result.returncode:
                print(f"Stopped: {role} failed (exit {result.returncode}); earlier apps may already be renewed. No remaining apps were attempted. If authentication expired, run xtool auth login --mode password yourself in a terminal.", file=sys.stderr)
                return 1
        if not args.dry_run:
            print("xtool reported all three installations successful. Open each app on the phone; this does not prove desktop reception or seven-day refresh.")
        return 0
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError, zipfile.BadZipFile, plistlib.InvalidFileException) as error:
        print(f"No further action: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
