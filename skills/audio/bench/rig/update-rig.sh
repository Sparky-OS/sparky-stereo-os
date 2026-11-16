#!/bin/bash
# Updates the rig images with the current rig files (asound.conf, the stand-in ALSA monitor script) and the tools the rows
# need: update-rig.sh IMAGE... ; needs DOCKER_HOST (the lane's socket).
set -euo pipefail
# APT_MOUNTS: docker -v options that give the container its apt setup (a CA bundle, a proxy file); APT_PREP: the command that
# applies it (empty if none); REPO_MOUNT: a -v option for a local copy of the edition's repository, if the image uses one.
APT_MOUNTS=${APT_MOUNTS:-}
APT_PREP=${APT_PREP:-:}
REPO_MOUNT=${REPO_MOUNT:-}
HERE=$(cd "$(dirname "$0")" && pwd)
for img in "$@"; do
	docker rm -f sa631-upd >/dev/null 2>&1 || true
	docker run --name sa631-upd --cpus 2 --ulimit core=0 $APT_MOUNTS -v "$HERE":/src:ro $REPO_MOUNT "$img" sh -c '
set -e
cp /src/asound.conf /etc/asound.conf
cp /src/rig-alsa-nodes.lua /usr/share/wireplumber/scripts/
cp /src/90-sa631-rig.conf /etc/wireplumber/wireplumber.conf.d/
if ! command -v paplay >/dev/null; then
	$APT_PREP
	apt-get update -qq >/dev/null 2>&1
	DEBIAN_FRONTEND=noninteractive apt-get -y -qq --no-install-recommends install pulseaudio-utils >/dev/null 2>&1
fi
paplay --version'
	docker commit sa631-upd "$img" >/dev/null
	docker rm sa631-upd >/dev/null
done
