#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not, as the [crash trap](../../SKILL.md#traps-that-fooled-us) explains.
# SPDX-License-Identifier: MIT
# drun.sh IMAGE NAME [VAR=value ...]: one fresh container (PREFIX-NAME) for one row of a VLC proof; the row's files end in $WORK/rows/NAME.
# Environment: DOCKER_HOST (the lane's own daemon socket), WORK (scratch folder with fix/ = the films and bin/ = the fake input client),
# RENDER_GID (the group of the render node, default 125), PREFIX (container name prefix, default rig). The VAR=value words go to session.sh.
set -eu
image=$1 name=$2; shift 2
here=$(cd "$(dirname "$0")" && pwd)
W=${WORK:?the scratch folder}; mkdir -p "$W/rows"
[ -f "$W/passwd" ] || { docker run --rm --entrypoint "" "$image" cat /etc/passwd > "$W/passwd"; echo "builder:x:1000:1000::/home/builder:/bin/bash" >> "$W/passwd"; }
docker run --rm --name "${PREFIX:-rig}-$name" --ulimit core=1 --cpus 2 --network none --user 1000:1000 --cap-add SYS_NICE \
	--device /dev/dri/renderD128 --group-add "${RENDER_GID:-125}" -v "$W/passwd:/etc/passwd:ro" --tmpfs /tmp \
	-v "$W/rows:/rows" -v "$W/fix:/fix:ro" -v "$W/bin:/fakeinput:ro" -v "$here/..:/tools:ro" -v "$here:/rig:ro" \
	--entrypoint "" "$image" env OUT=/rows/$name "$@" bash /rig/session.sh
