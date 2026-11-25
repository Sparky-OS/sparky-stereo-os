#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# run-case.sh IMAGE OUTDIR [VAR=VALUE ...]: one fresh container, one new account, its first and second login
# (welcome-login.sh); the results in OUTDIR. KWin runs on the NVIDIA card through CDI (never on the AMD card); the
# session's programs draw with Mesa's software renderer (llvmpipe): welcome-login.sh's kwin_wayland shim takes the
# software settings out of KWin's own environment.
# Environment: DOCKER_HOST (the lane's socket), RENDER_GROUP (the group of the card's render node inside the container),
# CONTAINER_IDS (the lane's .container-ids), FAKEINPUT_DIR (folder with the built fake input client), RIG_SCRIPTS
# (the skill's stereo-proof-rig/scripts folder), RUN_MOUNTS ("SRC:DST[:ro] ...", more bind mounts).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
IMG=$1; OUT=$(mkdir -p "$2" && cd "$2" && pwd); shift 2
[ -z "$(ls -A "$OUT")" ] || { echo "$OUT is not empty" >&2; exit 1; }
: "${RENDER_GROUP:?}" "${CONTAINER_IDS:?}" "${FAKEINPUT_DIR:?}" "${RIG_SCRIPTS:?}"
envs=(); for kv in "$@"; do envs+=(-e "$kv"); done
mounts=(); for m in ${RUN_MOUNTS:-}; do IFS=: read -r a b c <<< "$m"; mounts+=(--mount "type=bind,src=$a,dst=$b${c:+,readonly}"); done
name=kw63-case-$$
docker create --name "$name" --ulimit core=1 --network none --cap-add SYS_NICE --cpus 4 \
	--device nvidia.com/gpu=0 --group-add "$RENDER_GROUP" --user "$(id -u):$(id -g)" \
	--mount "type=bind,src=$RIG_SCRIPTS,dst=/rig,readonly" --mount "type=bind,src=$HERE,dst=/lane,readonly" \
	--mount "type=bind,src=$FAKEINPUT_DIR,dst=/tools,readonly" --mount "type=bind,src=$OUT,dst=/case" "${mounts[@]}" \
	-e CASE=/case -e RIG=/rig -e FAKEINPUT=/tools/fakeinput \
	-e LIBGL_ALWAYS_SOFTWARE=1 -e __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json \
	"${envs[@]}" "$IMG" timeout 420 bash /lane/welcome-login.sh > /dev/null
docker inspect -f '{{.Id}}' "$name" >> "$CONTAINER_IDS"
status=0; docker start -a "$name" > "$OUT/container.log" 2>&1 || status=$?
docker rm -f "$name" > /dev/null
rm -rf "$OUT/home/.cache"
echo "case $OUT: exit $status"
exit "$status"
