# The events that end in an expose, on Qt Quick windows drawn as a pair (pairstress), one fresh client per case in one
# KWin session: each case ends with the client still, the output's frame grabbed and the watchdog's lines counted.
# LIB=fixed puts /mnt/libQt6Quick.so.6 first; anything else runs the root's own library.
setmode sbs-full
LIBENV=
if [ "$(cat /mnt/lib 2>/dev/null)" = fixed ]; then mkdir -p /tmp/qtlib; cp /mnt/libQt6Quick.so.6 /tmp/qtlib/; LIBENV="LD_LIBRARY_PATH=/tmp/qtlib"; fi
kwscript() { # kwscript NAME 'javascript': run once in KWin
    printf '%s\n' "$2" > /tmp/kw-$1.js
    id=$(dbus-send --session --print-reply --dest=org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript string:/tmp/kw-$1.js string:kw555-$1-$$-$(date +%s%N) 2>/dev/null | sed -n 's/.*int32 //p')
    dbus-send --session --print-reply --dest=org.kde.KWin /Scripting/Script$id org.kde.kwin.Script.run > /dev/null 2>&1
    log "kwin script $1: id $id"
}
waitready() { # waitready FILE SECONDS
    t=0
    while [ $t -lt $2 ] && ! grep -q '^READY' $1 2>/dev/null; do sleep 1; t=$((t + 1)); done
    grep -q '^READY' $1 2>/dev/null
}
runcase() { # runcase NAME MODE READY_TIMEOUT
    c=$1
    env $LIBENV QT_LOGGING_RULES="qt.scenegraph.renderloop=true" /mnt/pairstress $2 > /mnt/s-$c.out 2> /mnt/s-$c.err &
    cp=$!
    waitready /mnt/s-$c.out $3 || log "$c: no READY line in $3 s"
}
endcase() {
    sleep ${1:-6}
    kill -0 $cp 2>/dev/null && st=alive || st="gone (exit $(wait $cp; echo $?))"
    grab s-$c
    log "$c: $st; $(grep -c '^READY' /mnt/s-$c.out) ready; exposes $(grep -c 'polishAndSync (in expose)' /mnt/s-$c.err); normal $(grep -c 'polishAndSync (normal)' /mnt/s-$c.err); watchdog $(grep -c '^WATCHDOG' /mnt/s-$c.err); library $(grep -m1 -o '/[^ ]*libQt6Quick\.so[^ ]*' /proc/$cp/maps 2>/dev/null)"
    kill $cp 2>/dev/null
    wait $cp 2>/dev/null
    sleep 2
}
runcase still still 40; endcase
runcase hideshow hideshow 60; endcase
runcase minimize minimize 40
sleep 3
grab s-minimize-away
kwscript unminimize 'workspace.windowList().forEach(function (w) { if (w.minimized) { w.minimized = false; } });'
endcase 8
runcase desktops still 40
dbus-send --session --print-reply --dest=org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop int32:2 > /mnt/desktop-2.txt 2>&1
sleep 4
grab s-desktops-away
dbus-send --session --print-reply --dest=org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop int32:1 > /mnt/desktop-1.txt 2>&1
endcase 8
runcase resize resize 60; endcase
runcase two two 40
kwscript place 'var n = 0; workspace.windowList().forEach(function (w) { if (w.normalWindow) { w.frameGeometry = {x: 100 + 700 * n, y: 150, width: w.frameGeometry.width, height: w.frameGeometry.height}; n++; } });'
endcase 8
runcase closeexpose closeexpose 90
kwscript list 'workspace.windowList().forEach(function (w) { if (w.normalWindow) { print("kw555 window " + w.caption + " " + w.frameGeometry.width + "x" + w.frameGeometry.height + " minimized " + w.minimized); } });'
endcase
runcase cycles cycles 120; endcase 8
