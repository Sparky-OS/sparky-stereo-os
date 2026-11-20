#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not, as the [crash trap](../../../stereo-proof-rig/SKILL.md#traps-that-fooled-us) explains.
# rigrun.sh NAME [--proto] [--no-engine] COMMAND... : one rig container per case, removed when it ends.
# Needs DOCKER_HOST (the lane's socket) and RIG_DIR (this folder), OUT_DIR (a world-writable scratch folder) and, with --proto,
# BUILD_DIR (a cmake build of plasma-pa with `make install DESTDIR=$BUILD_DIR/dest`). PG_IMAGE is the rig image (Debian testing with
# plasma-pa, systemsettings, pipewire, wireplumber, pipewire-pulse, pulseaudio-utils, xvfb, xdotool, python3-pyatspi,
# at-spi2-core, qml-qt6, polkitd, libglib2.0-bin and the fake ALSA device of ../rig built into /opt/sa631).
# PG_POLKIT=yes|no starts the system bus and polkitd and lets the Sound page's action through (yes) or refuses it (no).
set -u
NAME=$1; shift
docker rm -f pg-$NAME >/dev/null 2>&1
docker run --rm --name pg-$NAME -e PG_POLKIT="${PG_POLKIT:-}" --pull=never --ulimit core=1 --cpus 2 ${PG_MOUNTS:-} \
  -v "${RIG_DIR:?}":/src:ro -v "${RIG_DIR}/rig-alsa-nodes.lua":/usr/share/wireplumber/scripts/rig-alsa-nodes.lua:ro \
  -v "${BUILD_DIR:-/nonexistent}":/build:ro -v "${OUT_DIR:?}":/ev "${PG_IMAGE:-page-rig:base}" bash /src/page-run.sh "$@"
