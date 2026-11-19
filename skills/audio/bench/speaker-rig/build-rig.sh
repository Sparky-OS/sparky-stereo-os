#!/bin/bash
# Builds the speaker rig image from a base that has pipewire, wireplumber, pipewire-pulse, libasound2-dev, gcc, python3-numpy:
# build-rig.sh BASE_IMAGE NEW_IMAGE ; needs DOCKER_HOST (the lane's socket). The fake ALSA device is ../rig/pcm_sa631.c, built into /opt/sa631.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
NAME=${NAME:-sp23-rigbuild}
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run --name "$NAME" --pull=never --network none --ulimit core=0 --cpus 2 -v "$HERE":/src:ro -v "$HERE/../rig":/rig:ro "$1" sh -c '
set -e
id rig >/dev/null 2>&1 || useradd -m -u 1001 rig
mkdir -p /opt/sa631 /run/sa631 /etc/wireplumber/wireplumber.conf.d
sh /rig/build-plugin.sh /opt/sa631
cp /src/asound.conf /etc/asound.conf
cp /src/rig-alsa-nodes.lua /usr/share/wireplumber/scripts/
cp /src/90-sp23-rig.conf /etc/wireplumber/wireplumber.conf.d/'
docker commit "$NAME" "$2" >/dev/null
docker rm "$NAME" >/dev/null
