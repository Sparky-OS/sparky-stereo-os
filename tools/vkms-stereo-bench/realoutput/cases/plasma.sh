# Plasma windows drawn by Qt Quick with Stereo Union's element depth (System Monitor, the application launcher),
# each minimized and restored by KWin, the output's frame read before and after. LIB as in stress.sh.
setmode sbs-full
export XDG_CURRENT_DESKTOP=KDE QT_QUICK_CONTROLS_STYLE=org.kde.union UNION_DISABLE_CACHE=1 QT_HASH_SEED=0
LIBENV=
if [ "$(cat /mnt/lib 2>/dev/null)" = fixed ]; then mkdir -p /tmp/qtlib; cp /mnt/libQt6Quick.so.6 /tmp/qtlib/; LIBENV="LD_LIBRARY_PATH=/tmp/qtlib"; fi
kwscript() {
    printf '%s\n' "$2" > /tmp/kw-$1.js
    id=$(dbus-send --session --print-reply --dest=org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript string:/tmp/kw-$1.js string:kw555-$1-$$-$(date +%s%N) 2>/dev/null | sed -n 's/.*int32 //p')
    dbus-send --session --print-reply --dest=org.kde.KWin /Scripting/Script$id org.kde.kwin.Script.run > /dev/null 2>&1
}
n=0
for cmd in "plasma-systemmonitor" "plasmawindowed org.kde.plasma.kickoff"; do
    n=$((n + 1))
    env $LIBENV WAYLAND_DEBUG=client QT_LOGGING_RULES="qt.scenegraph.renderloop=true" $cmd > /mnt/pl-$n.out 2> /mnt/pl-$n.err &
    p=$!
    sleep ${PLASMA_WAIT:-50}
    grab pl-$n-start
    kwscript min 'workspace.windowList().forEach(function (w) { if (w.normalWindow) { w.minimized = true; } });'
    sleep 4
    grab pl-$n-away
    kwscript unmin 'workspace.windowList().forEach(function (w) { if (w.minimized) { w.minimized = false; workspace.activeWindow = w; } });'
    sleep 15
    grab pl-$n-after
    kill -0 $p 2>/dev/null && st=alive || st=gone
    log "plasma $n [$cmd] $st: get_depth $(grep -c 'get_depth' /mnt/pl-$n.err) set_desktop_depth $(grep -c 'set_desktop_depth' /mnt/pl-$n.err) set_content3 $(grep -c 'set_content(3)' /mnt/pl-$n.err) exposes $(grep -c 'polishAndSync (in expose)' /mnt/pl-$n.err) normal $(grep -c 'polishAndSync (normal)' /mnt/pl-$n.err) library $(grep -m1 -o '/[^ ]*libQt6Quick\.so[^ ]*' /proc/$p/maps 2>/dev/null)"
    grep -E 'qt.scenegraph.renderloop: (polishAndSync|handleExposure)|\.commit\(\)|set_desktop_depth|set_content' /mnt/pl-$n.err | cut -c1-120 | tail -60 > /mnt/pl-$n-tail.txt
    kill $p 2>/dev/null; wait $p 2>/dev/null; sleep 2
done
