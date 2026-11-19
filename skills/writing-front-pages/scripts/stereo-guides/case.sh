#!/bin/sh
# Inside the rig, under dbus-run-session: case.sh OUT NAME STEPFILE PROGRAM-ARGS...
# One fresh Stereo KWin (virtual, 3D twin modes listed) per case; steps: "cap TAG", "in STEP...", "wait S", "max", "js CODE", "title".
set -u
out=$1; name=$2; steps=$3; shift 3
export XDG_RUNTIME_DIR=/tmp/xdg-$(id -u); mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
[ "${TD:-0}" = 1 ] && export KWIN_VIRTUAL_STEREO_MODES=1
kwin_wayland --virtual ${XW:+--xwayland} --socket=sub --width ${W:-1280} --height ${H:-800} >"$out/$name.kwin.log" 2>&1 &
kp=$!
i=0; while [ ! -S "$XDG_RUNTIME_DIR/sub" ] && [ $i -lt 60 ]; do sleep 0.5; i=$((i+1)); done
[ -S "$XDG_RUNTIME_DIR/sub" ] || { echo "kwin did not start"; exit 3; }
export WAYLAND_DISPLAY=sub QT_QPA_PLATFORM=wayland
sleep 2
mkfifo "$XDG_RUNTIME_DIR/in" "$XDG_RUNTIME_DIR/ack"
/out/bin/fakeinput --serve "$XDG_RUNTIME_DIR/in" "$XDG_RUNTIME_DIR/ack" >"$out/$name.fakeinput.log" 2>&1 &
fp=$!
exec 7>"$XDG_RUNTIME_DIR/in" 8<"$XDG_RUNTIME_DIR/ack"
DISPLAY=${XW:+:0} LIBGL_ALWAYS_SOFTWARE=${SW:-1} WAYLAND_DEBUG=client "$@" >"$out/$name.prog.log" 2>"$out/$name.wl.log" &
pp=$!
sleep ${WAIT:-10}
rc=0
while IFS= read -r line; do
  cmd=${line%% *}; arg=${line#* }
  case $cmd in
    '#'*|'') ;;
    wait) sleep $arg ;;
    cap) python3 /scripts/capture.py "$out/$name.$arg.png" >"$out/$name.$arg.json" 2>>"$out/$name.capture.err" || { echo "capture $arg failed"; rc=1; } ;;
    in) echo "$arg" >&7; read -r r <&8; [ "$r" = ok ] || { echo "input refused: $arg ($r)"; rc=2; } ;;
    max) python3 /scripts/kwin_script.py "$out/$name.kwin.log" 'var l=workspace.windowList();for(var i=0;i<l.length;i++){if(l[i].normalWindow){l[i].frameGeometry={x:0,y:0,width:'"${W:-1280}"',height:'"${H:-800}"'};}}' ;;
    kd) kscreen-doctor $arg >>"$out/$name.kd.log" 2>&1 ;;
    win) python3 /scripts/kwin_windows.py "$out/$name.kwin.log" > "$out/$name.$arg.win.json" 2>>"$out/$name.capture.err" ;;
    *) echo "bad step: $line"; rc=4 ;;
  esac
done < "$steps"
grep -E 'kde_stereo_content|set_content|get_subsurface|place_below' "$out/$name.wl.log" | grep -v -E 'wl_registry' | head -30 > "$out/$name.decl.txt"
kill $pp 2>/dev/null; sleep 1; kill $kp 2>/dev/null; exec 7>&- 8<&-; kill $fp 2>/dev/null; wait 2>/dev/null
echo "$name rc=$rc"; exit $rc
