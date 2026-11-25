#!/bin/bash
# run-proof.sh OUT: the on-screen keyboard proof of row 71 (prove.sh) with its environment named in one place.
# RED_IMAGE: the published set's rig image (mkrig.sh, then rig/mklayer.sh with gwenview); GREEN_IMAGE: the same with the
# packages under test installed by rig/mklayer.sh. WORK holds fakeinput (the built client of ../fakeinput.c) and a clone
# of the skills (RIG_SCRIPTS). DOCKER_HOST, CONTAINER_IDS and NAME_PREFIX as the lane's brief sets them.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
: "${DOCKER_HOST:?}" "${CONTAINER_IDS:?}" "${RED_IMAGE:?}" "${GREEN_IMAGE:?}"
export DOCKER_HOST CONTAINER_IDS RED_IMAGE GREEN_IMAGE \
	RENDER_GROUP=${RENDER_GROUP:-$(getent group render | cut -d: -f3)} \
	FAKEINPUT_DIR=${FAKEINPUT_DIR:?the folder of the built fakeinput client} \
	RIG_SCRIPTS=${RIG_SCRIPTS:-$(cd "$HERE/.." && pwd)}
exec bash "$HERE/prove.sh" "${1:?a new output folder}"
