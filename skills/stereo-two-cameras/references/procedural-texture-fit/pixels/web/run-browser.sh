#!/bin/sh
# Open a page in Debian's Chromium, headless, inside a container, on one GPU, and wait until the page posts /done.
# run-browser.sh GPU ROOT OUTDIR [PAGE] [TIMEOUT-S]
#   GPU: nvidia (the RTX through CDI), amd (the iGPU's render node), cpu (no GPU device: SwiftShader or nothing)
#   ROOT: the folder served (the page and its data); OUTDIR: where the page's posts land (created)
# XVFB=1: Chromium with a window on an Xvfb inside the container (its own :93, never the person's display), for a
# GPU whose Vulkan has no headless surface (NVIDIA); FLAGS: Chromium's GPU switches.
# The container: ppx-508-web-*, no network but its own loopback, core files off, the person's uid, nothing on a display.
set -eu
FLAGS=${FLAGS:---enable-features=Vulkan}
GPU=$1; ROOT=$(cd "$2" && pwd); OUT=$3; PAGE=${4:-index.html}; T=${5:-600}
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
W=/K3D/partners/queue/procedures-from-pixels-508; S=/var/tmp/procedures-from-pixels-508
export DOCKER_HOST=unix://$W/docker.sock
case $GPU in
  nvidia) DEV="--device nvidia.com/gpu=0"; ICD=/etc/vulkan/icd.d/nvidia_icd.json ;;
  amd) DEV="--device /dev/dri/renderD128 --group-add 125"; ICD=/usr/share/vulkan/icd.d/radeon_icd.json ;;
  cpu) DEV=""; ICD="" ;;
  *) echo "GPU must be nvidia, amd or cpu" >&2; exit 2 ;;
esac
NAME=ppx-508-web-$GPU-$$
rm -f "$OUT/DONE"
docker run --rm --name "$NAME" --network none --ulimit core=0 --shm-size 1g $DEV \
  --user "$(id -u):$(id -g)" -e HOME="$S/m2c/home-$GPU" -e VK_DRIVER_FILES="$ICD" -e VK_ICD_FILENAMES="$ICD" -e VK_LOADER_DEBUG="${VKDEBUG:-}" -e XVFB="${XVFB:-0}" \
  -v "$ROOT:$ROOT:ro" -v "$OUT:$OUT" -v "$W:$W:ro" -v "$S/m2c:$S/m2c" \
  ppx-508-webgpu:forky sh -c '
    mkdir -p "$HOME"; PROF=$(mktemp -d "$HOME/profile.XXXXXX")
    python3 '"$W"'/src/web/serve.py "'"$ROOT"'" "'"$OUT"'" 8508 &
    sleep 1
    if [ "${XVFB:-0}" = 1 ]; then Xvfb :93 -screen 0 1280x1024x24 -nolisten tcp > "$HOME/xvfb.log" 2>&1 & XP=$!; sleep 1; export DISPLAY=:93; HL="--ozone-platform=x11"; else HL="--headless=new"; fi
    chromium $HL --no-sandbox --disable-dev-shm-usage --no-first-run --user-data-dir="$PROF" \
      --enable-unsafe-webgpu --ignore-gpu-blocklist '"$FLAGS"' \
      --enable-logging=stderr --v=0 --remote-debugging-port=0 \
      "http://127.0.0.1:8508/'"$PAGE"'" > "'"$OUT"'/chromium.log" 2>&1 &
    CP=$!
    n=0; while [ ! -f "'"$OUT"'/DONE" ] && [ $n -lt '"$T"' ]; do sleep 1; n=$((n+1)); done
    kill $CP 2>/dev/null || true; sleep 1; rm -rf "$PROF"; [ -n "${XP:-}" ] && kill $XP 2>/dev/null || true
    [ -f "'"$OUT"'/DONE" ] && echo "page done in $n s" || echo "TIMEOUT after $n s"
  '
