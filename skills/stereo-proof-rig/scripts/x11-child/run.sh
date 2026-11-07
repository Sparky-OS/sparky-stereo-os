#!/bin/bash
# SPDX-License-Identifier: MIT
# run.sh MODE EVDIR: one fresh container and session per case, then the verdict of child_clip_analyze.py.
# Needs: DOCKER_HOST (your docker socket), IMG (an image with the edition's Stereo KWin, Xwayland, Mesa and libstereo-declare,
# plus python3-gi, python3-xlib and numpy/PIL), RENDER_GID (the render node's group for --group-add), the scripts' folder mounted.
# GPU: --device nvidia.com/gpu=0 (CDI) gives KWin its render node; give a Mesa client LLVMPIPE with CLIENT_SW=1 when the client cannot use that node.
set -u
mode=$1 ev=$(readlink -f "$2"); HERE=$(cd "$(dirname "$0")" && pwd); SCRIPTS=$(readlink -f "$HERE/..")
: "${IMG:?set IMG}" "${RENDER_GID:?set RENDER_GID}"
mkdir -p "$ev"
docker run --rm --ulimit core=0 --network none --user "$(id -u):$(id -g)" --cap-add SYS_NICE --device nvidia.com/gpu=0 --group-add "$RENDER_GID" \
  -v "$SCRIPTS:$SCRIPTS:ro" -v "$ev:$ev" -v "${PASSWD:?set PASSWD}:/etc/passwd:ro" -v "${GROUP:?set GROUP}:/etc/group:ro" -e HOME="$ev" \
  ${CLIENT_SW:+-e CLIENT_SW=$CLIENT_SW} -e CLIENT_ENV="${CLIENT_ENV:-}" -e GLXV="${GLXV:-mesa}" ${EXTRA_DOCKER:-} "$IMG" bash "$HERE/inner.sh" "$mode" "$ev"
python3 -I "$HERE/child_clip_analyze.py" "$ev" "$mode" | tee "$ev/verdict.json" | python3 -c 'import json,sys; d=json.load(sys.stdin); [print(("PASS " if r["pass"] else "FAIL ")+r["row"]+" :: "+r["detail"]) for r in d["rows"]]'
