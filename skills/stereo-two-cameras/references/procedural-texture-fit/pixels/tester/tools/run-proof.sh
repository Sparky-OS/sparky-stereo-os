#!/bin/sh
# One run of the Procedural Texture Rendering page in Debian's Chromium inside a container, watched by drive.py.
# run-proof.sh GPU OUTDIR TAG QUERY [TIMEOUT-S]
#   GPU: nvidia (the RTX through CDI; Chromium on an Xvfb inside the container), amd (the iGPU's render node,
#   headless), cpu (no GPU device: Mesa's lavapipe draws WebGL, the browser offers no WebGPU adapter).
#   QUERY: the page's address query (speed=d144&conns=6&player=wasm ...).
#   HOST=server (default): tools/serve.py serves the site with its link beside it (link=server in QUERY uses it).
#   HOST=static: Python's plain http.server serves a folder in which the site lies at SUBPATH (default
#   demos/procedural-texture-rendering/), as any static host would: no link routes, no types of ours.
#   TREE=DIR: run from a frozen copy of the tree. PAGE: another page of the site or of ALSO.
#   ALSO=PATH=DIR[,PATH=DIR]: more folders for the local server (proofs only); ALSOMOUNT=DIR: a folder outside the
#   tree to mount read-only for them. DRIVER: the program that watches the run (drive.py; a11y.py; hidden.py).
#   AMD_DEVICE: the render node of the GPU for the amd route (default /dev/dri/renderD128, with its group).
# The container: PREFIX-GPU-TAG (PREFIX default ptr-run), no network but its own loopback, core files off, the
# person's uid, at most two processors, no display of the person's. The page, the server and the driver all run
# inside it. IMAGE: an image with Chromium, Mesa's Vulkan drivers (radv, lavapipe), Xvfb and python3 (default
# ptr-webgpu:latest). SCRATCH: a folder for the browser's profile (default /var/tmp/ptr-proof). DOCKER_HOST is taken
# from the environment as it is.
set -eu
GPU=$1; OUT=$2; TAG=$3; QUERY=$4; T=${5:-7200}
# TREE: the folder that holds site/ and tools/ (default: the one this script lies in; a frozen copy for long runs, so
# later edits never reach a run that is under way)
W=${TREE:-$(cd "$(dirname "$0")/.." && pwd)}
S=${SCRATCH:-/var/tmp/ptr-proof}
IMAGE=${IMAGE:-ptr-webgpu:latest}
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
case $GPU in
  nvidia) DEV="--device nvidia.com/gpu=0"; ICD=/etc/vulkan/icd.d/nvidia_icd.json; XV=1; FL="--ozone-platform=x11 --enable-features=Vulkan --use-angle=vulkan" ;;
  amd) NODE=${AMD_DEVICE:-/dev/dri/renderD128}; DEV="--device $NODE --group-add $(stat -c %g "$NODE")"; ICD=/usr/share/vulkan/icd.d/radeon_icd.json; XV=0; FL="--headless=new --enable-features=Vulkan --use-angle=vulkan" ;;
  cpu) DEV=""; ICD=/usr/share/vulkan/icd.d/lvp_icd.json; XV=0; FL="--headless=new --enable-features=Vulkan --use-angle=vulkan" ;;
  *) echo "GPU must be nvidia, amd or cpu" >&2; exit 2 ;;
esac
NAME=${PREFIX:-ptr-run}-$GPU-$TAG
# WebGPU as Chromium ships it on Linux needs --enable-unsafe-webgpu; the cpu route leaves it off, so the page meets a
# browser that gives it no WebGPU adapter
[ "$GPU" = cpu ] && WG="" || WG="--enable-unsafe-webgpu"
HOSTMODE=${HOST:-server}
SUBPATH=${SUBPATH:-demos/procedural-texture-rendering/}
PORT=8537
mkdir -p "$S/home"
rm -f "$OUT/DONE"
docker run --rm --name "$NAME" --network none --ulimit core=0 --shm-size 1g --cpus 2 $DEV \
  --user "$(id -u):$(id -g)" -e HOME="$S/home" -e VK_DRIVER_FILES="$ICD" -e VK_ICD_FILENAMES="$ICD" -e XV="$XV" \
  -e HOSTMODE="$HOSTMODE" -e SUBPATH="$SUBPATH" -e ALSO="${ALSO:-}" -e WINDOW="${WINDOW:-1600,1500}" -e EXTRA="${EXTRA:-}" -e CONTROL="${CONTROL:-}" -e HIDE="${HIDE:-}" -e TAIL="${TAIL:-}" \
  -v "$W:$W:ro" -v "$OUT:$OUT" -v "$S/home:$S/home" ${ALSOMOUNT:+-v "$ALSOMOUNT:$ALSOMOUNT:ro"} \
  "$IMAGE" sh -c '
    PROF=$(mktemp -d "$HOME/profile.XXXXXX")
    if [ "$HOSTMODE" = static ]; then
      ROOT=$(mktemp -d "$HOME/static.XXXXXX")
      mkdir -p "$ROOT/$(dirname "$SUBPATH")"
      ln -s '"$W"'/site "$ROOT/${SUBPATH%/}"
      python3 -m http.server '"$PORT"' --bind 127.0.0.1 --directory "$ROOT" > "'"$OUT"'/'"$TAG"'-server.log" 2>&1 &
      SP=$!
      BASE="http://127.0.0.1:'"$PORT"'/$SUBPATH"
      LOGURL=""
    else
      ALSOARGS=""; for a in $(echo "$ALSO" | tr "," " "); do ALSOARGS="$ALSOARGS --also $a"; done
      python3 '"$W"'/tools/serve.py --port '"$PORT"' --prefix "/$SUBPATH" $ALSOARGS > "'"$OUT"'/'"$TAG"'-server.log" 2>&1 &
      SP=$!
      BASE="http://127.0.0.1:'"$PORT"'/$SUBPATH"
      LOGURL="${BASE}link/log"
    fi
    sleep 1
    if [ "$XV" = 1 ]; then Xvfb :93 -screen 0 1600x1500x24 -nolisten tcp > "$PROF/xvfb.log" 2>&1 & XP=$!; sleep 1; export DISPLAY=:93; fi
    chromium '"$FL"' --no-sandbox --disable-dev-shm-usage --no-first-run --user-data-dir="$PROF" \
      '"$WG"' --ignore-gpu-blocklist --window-size="$WINDOW" --autoplay-policy=user-gesture-required $EXTRA \
      --remote-debugging-port=9222 --enable-logging=stderr --v=0 \
      "${BASE}'"${PAGE:-}"'?proof=1&tag='"$TAG"'&'"$QUERY"'" > "'"$OUT"'/'"$TAG"'-chromium.log" 2>&1 &
    CP=$!
    case "'"$QUERY"'" in *link=server*) ;; *) LOGURL="" ;; esac
    python3 '"$W"'/tools/'"${DRIVER:-drive.py}"' "'"$OUT"'" "'"$TAG"'" 9222 '"$PORT"' '"$T"' "$LOGURL" || echo "driver failed"
    kill $CP 2>/dev/null || true; sleep 1; kill $SP 2>/dev/null || true
    [ -n "${XP:-}" ] && kill $XP 2>/dev/null || true
    rm -rf "$PROF" ${ROOT:+"$ROOT"}
    [ -f "'"$OUT"'/DONE" ] && echo "'"$TAG"': done" || echo "'"$TAG"': no result"
  '
