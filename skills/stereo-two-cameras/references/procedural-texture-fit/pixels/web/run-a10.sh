#!/bin/sh
# The A10 kit (ORDER 508, milestone 2c): draws the thirteen procedures in Chromium on WebGPU, on each GPU in turn, and
# keeps the drawings and the timings in OUTDIR. Run by a person or the main session on the A10, from this folder:
#   sh run-a10.sh [OUTDIR]
# Needs python3 and Debian's chromium (156 was used on the station), and Mesa's Vulkan driver (radv) for each GPU.
# The GPU is chosen with DRI_PRIME (0: the GPU that drives the screen, Carrizo; 1: the other one, Hainan); the page
# writes the adapter it was given in each result file, so a wrong choice shows there. Nothing is sent anywhere: the
# page posts only to its own server on 127.0.0.1.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HERE/results}
mkdir -p "$OUT"
command -v chromium >/dev/null || { echo "chromium is not installed (apt install chromium)" >&2; exit 1; }
run() {
    tag=$1; prime=$2; query=$3
    rm -f "$OUT/DONE"
    python3 "$HERE/serve.py" "$HERE/page" "$OUT" 8508 &
    sp=$!
    sleep 1
    prof=$(mktemp -d)
    DRI_PRIME=$prime chromium --headless=new --no-first-run --user-data-dir="$prof" --enable-unsafe-webgpu \
        --enable-features=Vulkan --use-angle=vulkan --ignore-gpu-blocklist --enable-logging=stderr \
        "http://127.0.0.1:8508/index.html?tag=$tag&$query" > "$OUT/$tag-chromium.log" 2>&1 &
    cp=$!
    n=0
    while [ ! -f "$OUT/DONE" ] && [ $n -lt 1800 ]; do sleep 1; n=$((n + 1)); done
    kill $cp 2>/dev/null || true
    kill $sp 2>/dev/null || true
    rm -rf "$prof"
    if [ -f "$OUT/DONE" ]; then echo "$tag: done in $n s ($(cat "$OUT/DONE"))"; mv "$OUT/DONE" "$OUT/$tag-DONE"; else echo "$tag: no answer in $n s (see $OUT/$tag-chromium.log)"; fi
}
# each GPU: the thirteen at 2048 (whole and 16 tiles), then at 1024 with fewer octaves (what a lighter device draws)
for prime in 0 1; do
    run "a10-gpu$prime-2048" "$prime" "wasm=0&repeat=3"
    run "a10-gpu$prime-1024-lod6" "$prime" "wasm=0&repeat=3&size=1024&lod=6"
done
echo "results in $OUT: *-result.json (timings, the adapter), *.png (the drawings)"
