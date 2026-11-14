# System Monitor with Stereo Union's element depth: the output's frame sampled many times, steady and after a
# restore, each sample named pair (the eyes differ), flat (the window is there, the eyes are equal) or away.
setmode sbs-full
export XDG_CURRENT_DESKTOP=KDE QT_QUICK_CONTROLS_STYLE=org.kde.union UNION_DISABLE_CACHE=1 QT_HASH_SEED=0
LIBENV=
if [ "$(cat /mnt/lib 2>/dev/null)" = fixed ]; then mkdir -p /tmp/qtlib; cp /mnt/libQt6Quick.so.6 /tmp/qtlib/; LIBENV="LD_LIBRARY_PATH=/tmp/qtlib"; fi
kwscript() {
    printf '%s\n' "$2" > /tmp/kw-$1.js
    id=$(dbus-send --session --print-reply --dest=org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript string:/tmp/kw-$1.js string:kw555-$1-$$-$(date +%s%N) 2>/dev/null | sed -n 's/.*int32 //p')
    dbus-send --session --print-reply --dest=org.kde.KWin /Scripting/Script$id org.kde.kwin.Script.run > /dev/null 2>&1
}
cat > /tmp/sample.py <<'PY'
import subprocess, sys, time
import numpy as np
from PIL import Image
tag, count = sys.argv[1], int(sys.argv[2])
kept = {}
for i in range(count):
    subprocess.run(["/tmp/drm-grab", "/dev/dri/card0", "/tmp/g.ppm", "HDMI-A-1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    a = np.asarray(Image.open("/tmp/g.ppm").convert("RGB")).astype(int)
    w = a.shape[1] // 2
    differ = int((np.abs(a[:, :w] - a[:, w:2 * w]).sum(axis=2) > 24).sum())
    lit = int((a[:, :w].sum(axis=2) > 60).sum())
    name = "away" if lit < 20000 else ("pair" if differ else "flat")
    print("sample %s %d %.1f %s differing %d lit %d" % (tag, i, time.time(), name, differ, lit), flush=True)
    if name not in kept:
        kept[name] = True
        Image.open("/tmp/g.ppm").save("/mnt/sample-%s-%s.ppm" % (tag, name))
PY
env $LIBENV QT_LOGGING_RULES="qt.scenegraph.renderloop=true" plasma-systemmonitor > /mnt/sm.out 2> /mnt/sm.err &
p=$!
sleep 50
python3 /tmp/sample.py steady 12 > /mnt/samples-steady.txt 2>&1
if [ "$(cat /mnt/event 2>/dev/null)" = desktops ]; then
    dbus-send --session --print-reply --dest=org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop int32:2 > /dev/null 2>&1
    sleep 4
    python3 /tmp/sample.py otherdesktop 2 > /mnt/samples-otherdesktop.txt 2>&1
    dbus-send --session --print-reply --dest=org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop int32:1 > /dev/null 2>&1
else
kwscript min 'workspace.windowList().forEach(function (w) { if (w.normalWindow) { w.minimized = true; } });'
sleep 3
kwscript unmin 'workspace.windowList().forEach(function (w) { if (w.minimized) { w.minimized = false; workspace.activeWindow = w; } });'
fi
python3 /tmp/sample.py restored 30 > /mnt/samples-restored.txt 2>&1
kill -0 $p 2>/dev/null && st=alive || st=gone
for t in steady restored; do log "system monitor $t: pair $(grep -c ' pair ' /mnt/samples-$t.txt) flat $(grep -c ' flat ' /mnt/samples-$t.txt) away $(grep -c ' away ' /mnt/samples-$t.txt)"; done
log "system monitor $st: exposes $(grep -c 'polishAndSync (in expose)' /mnt/sm.err) normal $(grep -c 'polishAndSync (normal)' /mnt/sm.err) library $(grep -m1 -o '/[^ ]*libQt6Quick\.so[^ ]*' /proc/$p/maps 2>/dev/null)"
kill $p 2>/dev/null; wait $p 2>/dev/null
