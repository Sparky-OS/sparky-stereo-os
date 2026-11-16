#!/bin/bash
# Two programs in one session inside Qt's own frame (run by case.sh with WAIT_CLIENT=1): qdiscs whose frame
# cannot be drawn into both views (the egl-fail-shared-gl shim), then qdiscs that gets its pair; the person's kept
# problems after each. The first must keep one-view:opengl-frame:DRIVER, the second must end it.
set -u
step() {
  "$@" & local pid=$!
  sleep 6
  kill $pid 2>/dev/null; wait $pid 2>/dev/null
}
step env LD_PRELOAD=/bin-fx/egl-fail-shared-gl.so QF583_FAIL_SHARED_GL=3 /bin-fx/qdiscs
echo "== after the program whose frame could not be drawn into both views"
sparky-stereo-problems list --json
step /bin-fx/qdiscs
echo "== after the program that got its pair"
sparky-stereo-problems list --json
