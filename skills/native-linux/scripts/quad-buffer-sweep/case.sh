#!/bin/sh
# case.sh OUTDIR WAIT CMD...   (inside the container; the program runs on Xwayland via DISPLAY=:0 unless ROUTE=wayland)
out=$1; wait=$2; shift 2
mkdir -p "$out"
export XDG_RUNTIME_DIR=/tmp/xdg-$$; mkdir -m700 -p $XDG_RUNTIME_DIR
[ -n "$QB_SESSION_ENV" ] && . /hw/etc/xdg/plasma-workspace/env/sparky-stereo-opengl.sh
env | grep -E '^(SPARKY_STEREO_OPENGL|__GLX_VENDOR|MESA_LOADER|LIBGL_KOPPER|__EGL_VENDOR)' > "$out/session-env.txt"
export QB_EGLV="$__EGL_VENDOR_LIBRARY_FILENAMES"; unset __EGL_VENDOR_LIBRARY_FILENAMES
exec dbus-run-session -- sh -c '
export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
kwin_wayland --virtual --xwayland --socket=w --width 1280 --height 800 >'$out'/kwin.log 2>&1 &
kp=$!
i=0; while [ ! -S $XDG_RUNTIME_DIR/w ] && [ $i -lt 100 ]; do sleep 0.2; i=$((i+1)); done
sleep 3
export WAYLAND_DISPLAY=w
[ -n "$QB_EGLV" ] && export __EGL_VENDOR_LIBRARY_FILENAMES="$QB_EGLV"
D=$(ls /tmp/.X11-unix | head -1 | tr -d "X"); export DISPLAY=:${D:-0}
echo "DISPLAY=$DISPLAY" >'$out'/env.txt
"$@" >'$out'/prog.log 2>&1 &
pp=$!
sleep '$wait'
if [ -n "$QB_ACT" ]; then sh $HOME/$(echo "$QB_ACT" | cut -d_ -f2) >'$out'/act.log 2>&1; sleep ${QB_SETTLE:-4}; fi
python3 /scripts/x11_props.py >'$out'/props.json 2>&1
python3 /scripts/capture.py '$out'/cap1.png >'$out'/cap1.json 2>&1
sleep 2
python3 /scripts/capture.py '$out'/cap2.png >'$out'/cap2.json 2>&1
kill $pp $kp 2>/dev/null; sleep 1
' sh "$@"
