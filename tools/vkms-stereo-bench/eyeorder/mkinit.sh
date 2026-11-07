#!/bin/sh
# mkinit.sh OUT: the guest initramfs of this bench: the kscreen-line bench's BusyBox base with this lane's phase and steps.
set -eu
B=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d "$B/tmp.XXXXXX")
cp -a "$B/initramfs/." "$T/"
rm -rf "$T/dev/console" "$T/dev/null" "$T/kscreen" "$T/kwinvm" "$T/kwin" "$T/phases/kscreen.sh" "$T/phases/kwin.sh"
mkdir -p "$T/eyeorder"
cp "$B"/guest/phases/*.sh "$T/phases/"
cp "$B"/guest/eyeorder/*.sh "$T/eyeorder/"
cp "$B"/edid/*.bin "$T/data/"
cp "$B"/bin/drm-grab "$B"/bin/drm-flipwatch "$B"/bin/fullscreen-2d "$B"/bin/egl-stereo-subsurface "$B"/bin/drm-planelog "$T/bin/"
python3 "$B/mkcpio.py" "$T" "$1"
rm -rf "$T"
