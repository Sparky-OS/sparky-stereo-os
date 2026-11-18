#!/bin/bash
# SPDX-License-Identifier: MIT
# run-case.sh IMAGE OUTDIR [VAR=VALUE ...]: one fresh login (login.sh) in a container of its own; the results in OUTDIR.
# Environment: DOCKER_HOST (your own socket), NAME_PREFIX (container names), RENDER_NODE (default /dev/dri/renderD128),
# RUN_MOUNTS="SRC:DST[:ro] ..." (more bind mounts: a development build, a theme folder over the package's).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
IMG=$1; OUT=$(mkdir -p "$2" && cd "$2" && pwd); shift 2
rm -rf "${OUT:?}"/*
NODE=${RENDER_NODE:-/dev/dri/renderD128}
envs=(); for kv in "$@"; do envs+=(-e "$kv"); done
mounts=(); for m in ${RUN_MOUNTS:-}; do IFS=: read -r a b c <<< "$m"; mounts+=(--mount "type=bind,src=$a,dst=$b${c:+,readonly}"); done
docker run --rm --name "${NAME_PREFIX:-splash-rig}-case-$$" --ulimit core=0 --network none --cap-add SYS_NICE --cpus 4 \
	--device "$NODE" --group-add "${RENDER_GROUP:-$(stat -c %g "$NODE")}" --user "$(id -u):$(id -g)" \
	--mount "type=bind,src=$HERE/..,dst=/rig-scripts,readonly" --mount "type=bind,src=$OUT,dst=/case" "${mounts[@]}" \
	-e CASE=/case "${envs[@]}" "$IMG" timeout 240 bash /rig-scripts/login-splash/login.sh
rm -rf "$OUT/home"
