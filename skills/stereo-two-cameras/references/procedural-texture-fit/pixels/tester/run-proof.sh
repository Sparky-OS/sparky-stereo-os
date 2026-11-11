#!/bin/sh
# One scene tester run in Debian's Chromium inside a container (ORDER 508, milestone 3), watched by drive.py.
# run-proof.sh GPU OUTDIR TAG QUERY [TIMEOUT-S]
#   GPU: nvidia (the RTX through CDI; Chromium on an Xvfb inside the container), amd (the iGPU's render node,
#   headless), cpu (no GPU device). QUERY: the tester's address query (speed=d144&conns=6&player=wasm ...).
# The container: ppx-508-tester-*, no network but its own loopback, core files off, the person's uid, no display of
# the person's. The page, the server and the driver all run inside it.
set -eu
GPU=$1; OUT=$2; TAG=$3; QUERY=$4; T=${5:-7200}
W=/K3D/partners/queue/procedures-from-pixels-508; S=/var/tmp/procedures-from-pixels-508
export DOCKER_HOST=unix://$W/docker.sock
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
case $GPU in
  nvidia) DEV="--device nvidia.com/gpu=0"; ICD=/etc/vulkan/icd.d/nvidia_icd.json; XV=1; FL="--ozone-platform=x11 --enable-features=Vulkan --use-angle=vulkan" ;;
  amd) DEV="--device /dev/dri/renderD128 --group-add 125"; ICD=/usr/share/vulkan/icd.d/radeon_icd.json; XV=0; FL="--headless=new --enable-features=Vulkan --use-angle=vulkan" ;;
  cpu) DEV=""; ICD=/usr/share/vulkan/icd.d/lvp_icd.json; XV=0; FL="--headless=new --enable-features=Vulkan --use-angle=vulkan" ;;
  *) echo "GPU must be nvidia, amd or cpu" >&2; exit 2 ;;
esac
NAME=ppx-508-tester-$GPU-$TAG
# WebGPU as Chromium ships it on Linux needs --enable-unsafe-webgpu; the cpu route leaves it off, so the page meets a
# browser that gives it no WebGPU adapter (Mesa's lavapipe draws its WebGL)
[ "$GPU" = cpu ] && WG="" || WG="--enable-unsafe-webgpu"
mkdir -p "$S/m3/home"
rm -f "$OUT/DONE"
docker run --rm --name "$NAME" --network none --ulimit core=0 --shm-size 1g --cpus 2 $DEV \
  --user "$(id -u):$(id -g)" -e HOME="$S/m3/home" -e VK_DRIVER_FILES="$ICD" -e VK_ICD_FILENAMES="$ICD" -e XV="$XV" \
  -v "$W/src:$W/src:ro" -v "$OUT:$OUT" -v "$S/m3/home:$S/m3/home" -e NPM="${NPM:-}" ${NPM:+-v "$NPM:$NPM:ro"} -e SCENE="${SCENE:-}" ${SCENE:+-v "$SCENE:$SCENE:ro"} \
  ppx-508-webgpu:forky sh -c '
    PROF=$(mktemp -d "$HOME/profile.XXXXXX")
    python3 '"$W"'/src/tester/serve.py --save "'"$OUT"'" --port 8508 ${NPM:+--npm $NPM} ${SCENE:+--scene $SCENE} > "'"$OUT"'/'"$TAG"'-server.log" 2>&1 &
    SP=$!
    sleep 1
    if [ "$XV" = 1 ]; then Xvfb :93 -screen 0 1600x1500x24 -nolisten tcp > "$PROF/xvfb.log" 2>&1 & XP=$!; sleep 1; export DISPLAY=:93; fi
    chromium '"$FL"' --no-sandbox --disable-dev-shm-usage --no-first-run --user-data-dir="$PROF" \
      '"$WG"' --ignore-gpu-blocklist --window-size=1600,1500 --autoplay-policy=user-gesture-required \
      --remote-debugging-port=9222 --enable-logging=stderr --v=0 \
      "http://127.0.0.1:8508/'"${PAGE:-}"'?proof=1&tag='"$TAG"'&'"$QUERY"'" > "'"$OUT"'/'"$TAG"'-chromium.log" 2>&1 &
    CP=$!
    python3 '"$W"'/src/tester/drive.py "'"$OUT"'" "'"$TAG"'" 9222 8508 '"$T"' || echo "driver failed"
    kill $CP 2>/dev/null || true; sleep 1; kill $SP 2>/dev/null || true
    [ -n "${XP:-}" ] && kill $XP 2>/dev/null || true
    rm -rf "$PROF"
    [ -f "'"$OUT"'/DONE" ] && echo "'"$TAG"': done" || echo "'"$TAG"': no result"
  '
