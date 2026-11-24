#!/bin/bash
# One program case inside a session (traced-xwayland-session.sh runs it with DISPLAY set; OUT_DIR receives its logs): the program presents, its window is
# resized, minimized, restored and covered by another X11 window, then it is closed.
# Usage: x11-program-actions.sh vkcube|chromium-gl|chromium-vulkan [SECONDS_BEFORE_ACTIONS]
#   vkcube: Mesa's or the driver's X11 Vulkan swapchain (explicit sync on Mesa drivers), recreated at each resize
#   chromium-*: Chromium on X11 (the engine of Electron programs such as Discord) with an animated canvas;
#               -gl is its default ANGLE on OpenGL, -vulkan asks ANGLE for Vulkan
set -uo pipefail
WHAT=$1
WAIT=${2:-4}
cd "${OUT_DIR:-.}" || exit 1
say() { printf '%s %s\n' "$(date -u +%T.%3N)" "$*"; }
page='data:text/html,<body style="margin:0"><canvas id=c width=600 height=400></canvas><script>var c=document.getElementById("c").getContext("2d"),t=0;function f(){t++;c.fillStyle="hsl("+(t%360)+",80%,50%)";c.fillRect(0,0,600,400);c.fillStyle="#fff";c.fillRect((t*4)%560,180,40,40);requestAnimationFrame(f)}f()</script></body>'
case "$WHAT" in
    vkcube) vkcube --wsi xcb > vk.log 2>&1 & PID=$!; NAME="Vkcube X11" ;;
    chromium-gl|chromium-vulkan)
        extra=()
        [ "$WHAT" = chromium-vulkan ] && extra=(--use-angle=vulkan --enable-features=Vulkan,DefaultANGLEVulkan,VulkanFromANGLE)
        chromium --no-sandbox --ozone-platform=x11 --user-data-dir="$HOME/chromium-$$" --no-first-run --no-default-browser-check \
            --ignore-gpu-blocklist --window-size=640,480 --enable-logging=stderr --v=0 "${extra[@]}" --app="$page" > chromium.log 2>&1 &
        PID=$!; NAME=chromium ;;
    *) echo "unknown case $WHAT" >&2; exit 2 ;;
esac
sleep "$WAIT"
xwininfo -root -tree > xtree.txt 2>&1
if [ "$NAME" = chromium ]; then
    W=$(xdotool search --onlyvisible --class chromium 2>/dev/null | head -1)
else
    W=$(awk -v n="\"$NAME\"" 'index($0, n) {print $1; exit}' xtree.txt)
fi
say "window $W"
[ -n "$W" ] || { say "no window found"; kill "$PID" 2>/dev/null; exit 1; }
xwininfo -id "$W" -tree -children 2>&1 | head -20
for w in "$W" $(xwininfo -id "$W" -children 2>/dev/null | awk '/^ +0x/ {print $1}'); do
    say "window $w: $(xwininfo -id "$w" 2>/dev/null | grep -E 'Depth:|Visual:|Map State:' | tr -s ' ' | tr '\n' ' ')"
done
for size in "800 600" "300 200" "640 480"; do
    xdotool windowsize "$W" $size; say "resized to $size"; sleep 1.5
done
xdotool windowminimize "$W"; say "minimized"; sleep 2
xdotool windowmap "$W"; xdotool windowactivate "$W" 2>/dev/null; say "restored"; sleep 2
${X11_SOLID:-x11-solid} cover 300 200 808080 > cover.log 2>&1 & COVER=$!
say "covered"; sleep 2
kill "$COVER" 2>/dev/null; wait "$COVER" 2>/dev/null; say "uncovered"; sleep 2
xdotool windowsize "$W" 500 350; say "resized to 500 350"; sleep 1.5
kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null
say "closed; X server: $(xdpyinfo >/dev/null 2>&1 && echo whole || echo gone)"
grep -i -E "vulkan|angle|gl_renderer|gpu" chromium.log 2>/dev/null | head -8
exit 0
