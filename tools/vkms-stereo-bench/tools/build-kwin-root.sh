#!/bin/bash
# Created by Daniel Ramos (Capitain Jack) 2026/10/11
# Copyright 2026 under the GNU GPL3 License
# Last update 2026/10/13
#
# Builds the root file system for the bench's kwin phase: Stereo KWin with the DisplayXR window-geometry
# publisher, kscreen-doctor (with Qt's Wayland shell integration), Mesa, D-Bus, the edition's protocols,
# KPipeWire and KRdp (the phone headset as a display), the stereo declaration and stereo layer libraries
# with their development files, and gcc with wayland-scanner and the Wayland, EGL and GL development files
# the two test clients need. Debian testing plus Sparky Stereo OS's packages,
# pinned above Debian's. No root needed: mmdebstrap runs in a user namespace.
#   tools/build-kwin-root.sh STEREO_SOURCE OUT.tar.zst
# STEREO_SOURCE is an apt source line for Sparky Stereo OS's packages, for example
#   "deb [trusted=yes] copy:///srv/sparky-stereo-repo ./" (copy:// for a local folder: dpkg runs in the
# chroot and cannot reach a file:/ path; mmdebstrap copies the packages in). Set TMPDIR to a roomy disk:
# the root is assembled there first (about 2 GB).
# Unpack with:  mkdir sparky-root && tar -C sparky-root --exclude='./dev/*' -xf OUT.tar.zst
# (the guest mounts its own /dev), then:  ./bench ... --kwin-root sparky-root run kwin
set -euo pipefail
[ $# -eq 2 ] || { sed -n '8,18p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }
STEREO_SOURCE=$1
OUT=$2
command -v mmdebstrap >/dev/null || { echo "mmdebstrap is needed (apt install mmdebstrap)" >&2; exit 1; }
DMO_KEYRING=/usr/share/keyrings/deb-multimedia-keyring.pgp
[ -f "$DMO_KEYRING" ] || { echo "$DMO_KEYRING is needed (install deb-multimedia-keyring from the repository's carried/ folder)" >&2; exit 1; }
PACKAGES=ca-certificates,kwin-wayland,displayxr-window-geometry-publisher-kwin,libkscreen-bin,qt6-wayland,mesa-libgallium,libgl1-mesa-dri,libegl-mesa0,dbus,dbus-bin,gcc,libc6-dev,pkg-config,libwayland-bin,libwayland-dev,wayland-protocols,libegl-dev,libgl-dev,plasma-wayland-protocols,krdp,libkpipewire6,libkpipewirerecord6,libkpipewiredmabuf6,libstereo-declare1,libstereo-declare-dev,libstereo-layer1,libstereo-layer-dev
mmdebstrap --mode=unshare --variant=apt --components=main --include="$PACKAGES" \
	--setup-hook='mkdir -p "$1/etc/apt/preferences.d" && printf "Package: *\nPin: release o=Sparky Stereo OS\nPin-Priority: 1001\n" > "$1/etc/apt/preferences.d/sparky-stereo"' \
	--setup-hook='mkdir -p "$1/usr/share/keyrings" && cp '"$DMO_KEYRING"' "$1/usr/share/keyrings/"' \
	--customize-hook='chroot "$1" dpkg-query -W -f="\${Package}\t\${Version}\n" > "$1/etc/sparky-stereo-kwin-root.packages"' \
	testing "$OUT" "deb http://deb.debian.org/debian testing main" "$STEREO_SOURCE" \
	"deb [signed-by=$DMO_KEYRING] https://www.deb-multimedia.org forky main non-free"
echo "built $OUT; package list inside at /etc/sparky-stereo-kwin-root.packages"
