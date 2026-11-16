#!/bin/bash
# Builds the green image: the rig's image with the staged package installed by apt (the published edition's repository
# beside Debian's, the stage as a flat repository). prep-green.sh STAGE EVIDENCE_DIR; needs DOCKER_HOST (the lane's socket).
set -euo pipefail
APT_MOUNTS=${APT_MOUNTS:-}
APT_PREP=${APT_PREP:-:}
REPO_MOUNT=${REPO_MOUNT:-}
STAGE=$1 EV=$2
HERE=$(cd "$(dirname "$0")" && pwd)
docker rm -f sa631-green-prep >/dev/null 2>&1 || true
docker run --name sa631-green-prep --cpus 2 --ulimit core=0 \
	$APT_MOUNTS $REPO_MOUNT -v "$STAGE":/stage:ro -v "$HERE/proc-asound":/opt/sa631/proc-asound:ro -v "$EV":/ev \
	sa631-rig:builder sh -c '
set -e
$APT_PREP
echo "deb [trusted=yes] file:///stage ./" > /etc/apt/sources.list.d/sparky-stage.list
apt-get update >/dev/null 2>&1
apt-cache policy sparky-stereo-audio sparky-stereo-problems pipewire wireplumber | grep -E "^[a-z]|Candidate" > /ev/green-policy.txt
apt-get -s -y install sparky-stereo-audio | grep -E "^(Inst|Remv|Conf)" > /ev/green-upgrade-inst.txt
SPARKY_STEREO_AUDIO_PROC=/opt/sa631/proc-asound DEBIAN_FRONTEND=noninteractive apt-get -y install sparky-stereo-audio > /ev/green-install.log 2>&1
tail -4 /ev/green-install.log
dpkg -l sparky-stereo-audio | tail -1
ls -la /etc/pipewire/*.d /etc/wireplumber/wireplumber.conf.d
' 
docker commit sa631-green-prep sa631-rig:green >/dev/null
docker rm sa631-green-prep >/dev/null
