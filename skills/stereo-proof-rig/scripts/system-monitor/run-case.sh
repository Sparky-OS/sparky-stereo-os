#!/bin/bash
# run-case.sh NAME [ENV=VALUE ...]: one fresh rig container for one case of row 182; results in $OUT/NAME.
# KWin draws on the RTX 3060 through CDI (never the station's AMD render node); System Monitor uses Mesa's software
# renderer. A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
set -euo pipefail
NAME=${1:?case name}; shift
: "${DOCKER_HOST:?}" "${OUT:?results folder}" "${PKG:?package source folder}" "${CONTAINER_IDS:?}"
RIG=$(cd "$(dirname "$0")" && pwd)
RIGS=${RIGS:?the proof rig skill scripts folder}
MACHINES=${MACHINES:-$RIG/machines}
mkdir -p "$OUT/$NAME"
envs=(); for kv in "$@"; do envs+=(-e "$kv"); done
started=$(date --iso-8601=seconds)
docker create --name "${PREFIX:-sm182}-case-$NAME" --ulimit core=1 --cpus 4 --network none --platform linux/amd64 \
	--user 1000:1000 --group-add 125 --cap-add SYS_NICE --device nvidia.com/gpu=0 \
	-v "$PKG":/pkg:ro -v "$RIG":/rig:ro -v "$RIGS":/rigs:ro -v "$MACHINES":/machines:ro -v "$OUT/$NAME":/case \
	-e CASE=/case "${envs[@]}" "${IMAGE:-sm182-rig:r1123a}" bash /rig/session.sh > /dev/null
docker inspect -f '{{.Id}}' "${PREFIX:-sm182}-case-$NAME" >> "$CONTAINER_IDS"
status=0; timeout 240 docker start -a "${PREFIX:-sm182}-case-$NAME" > "$OUT/$NAME/container.log" 2>&1 || status=$?
docker rm -f "${PREFIX:-sm182}-case-$NAME" > /dev/null
echo "$NAME: container status $status"
coredumpctl list -q --since "$started" 2>/dev/null | grep -v '^No coredumps' || true
