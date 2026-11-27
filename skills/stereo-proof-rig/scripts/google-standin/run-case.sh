#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# run-case.sh IMAGE OUTDIR [VAR=VALUE ...]: one fresh container and one fresh login (session.sh) for row 299; results in
# OUTDIR. No network: Google's four host names resolve to the container's loopback, where the stand-in listens.
# KWin runs on the NVIDIA card through CDI (never the AMD card); programs draw with Mesa's software renderer.
# Env: DOCKER_HOST, CONTAINER_IDS, SKILL_SCRIPTS (stereo-proof-rig/scripts), RED_DIR (folder with the upstream binary,
#      mounted at /red), RENDER_GROUP.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
IMG=$1; OUT=$(mkdir -p "$2" && cd "$2" && pwd); shift 2
[ -z "$(ls -A "$OUT")" ] || { echo "$OUT is not empty" >&2; exit 1; }
: "${CONTAINER_IDS:?}" "${SKILL_SCRIPTS:?}" "${RED_DIR:?}" "${RENDER_GROUP:?}"
envs=(); for kv in "$@"; do envs+=(-e "$kv"); done
mkdir -p "$OUT/home"
cp "$HERE/oauth.json" "$OUT/oauth.json"
name=${PREFIX:-standin}-case-$$
docker create --name "$name" --ulimit core=1 --network none --cpus "${CPUS:-4}" --memory 6g \
	--sysctl net.ipv4.ip_unprivileged_port_start=0 \
	--add-host www.googleapis.com:127.0.0.1 --add-host oauth2.googleapis.com:127.0.0.1 \
	--add-host openidconnect.googleapis.com:127.0.0.1 --add-host accounts.google.com:127.0.0.1 \
	--cap-add SYS_NICE --device nvidia.com/gpu=0 --group-add "$RENDER_GROUP" --user "$(id -u):$(id -g)" \
	--mount "type=bind,src=$HERE,dst=/lane,readonly" --mount "type=bind,src=$SKILL_SCRIPTS,dst=/skill,readonly" \
	--mount "type=bind,src=$RED_DIR,dst=/red,readonly" \
	--mount "type=bind,src=$OUT,dst=/case" --mount "type=bind,src=$OUT/home,dst=/home/person" \
	-e CASE=/case -e LANE=/lane -e SKILL=/skill -e FAKEINPUT=/tools/fakeinput \
	-e LIBGL_ALWAYS_SOFTWARE=1 -e __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json \
	"${envs[@]}" "$IMG" timeout "${CASE_TIMEOUT:-900}" bash /lane/session.sh > /dev/null
docker inspect -f '{{.Id}}' "$name" >> "$CONTAINER_IDS"
status=0; docker start -a "$name" > "$OUT/container.log" 2>&1 || status=$?
docker rm -f "$name" > /dev/null
rm -rf "$OUT/home/.cache"
echo "case $OUT: exit $status"
exit "$status"
