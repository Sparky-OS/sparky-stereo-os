#!/bin/bash
# run-proof.sh OUT: the on-screen keyboard proof of row 71 (prove.sh) with its environment named in one place.
# RED_IMAGE: the published set's rig image (mkrig.sh, then rig/mklayer.sh with gwenview, konsole, zenity, the Stereo
# Browser and qml-qt6); STAGED_IMAGE: the same with the staged packages a round starts from; GREEN_IMAGE: the red image with
# the packages under test, each installed by rig/mklayer.sh. FAKEINPUT_DIR holds fakeinput (the built client of
# ../fakeinput.c, linked with -lm) and RIG_SCRIPTS the skills' stereo-proof-rig/scripts. DOCKER_HOST, CONTAINER_IDS and
# NAME_PREFIX as the lane's brief sets them. PARTS selects a subset (see prove.sh).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
: "${DOCKER_HOST:?}" "${CONTAINER_IDS:?}" "${RED_IMAGE:?}" "${STAGED_IMAGE:?}" "${GREEN_IMAGE:?}"
export DOCKER_HOST CONTAINER_IDS RED_IMAGE STAGED_IMAGE GREEN_IMAGE \
	RENDER_GROUP=${RENDER_GROUP:-$(getent group render | cut -d: -f3)} \
	FAKEINPUT_DIR=${FAKEINPUT_DIR:?the folder of the built fakeinput client} \
	RIG_SCRIPTS=${RIG_SCRIPTS:-$(cd "$HERE/.." && pwd)}
exec bash "$HERE/prove.sh" "${1:?a new output folder}"
