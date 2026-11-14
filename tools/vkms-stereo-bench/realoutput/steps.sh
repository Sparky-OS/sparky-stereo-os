# SPDX-License-Identifier: GPL-2.0-or-later
# Starts Stereo KWin on the DRM device, sets the output's mode, then runs /mnt/case.sh, which uses grab and setmode.
log() { echo "STEREO|realoutput|$*"; }
dpkg-query -W -f '${Package} ${Version}\n' kwin-wayland libkwin6 mesa-vulkan-drivers mesa-vulkan-layer-stereo libgl1-mesa-dri libstereo-declare1 libqt6gui6 libqt6waylandclient6 libqt6quick6 libqt6quick3d6 libqt6multimedia6 libstereo-policy1 stereo3ddemo libkscreen-bin 2>/dev/null > /mnt/versions.txt
# the person's depth limits, as System Settings writes them (DEPTH_LIMITS in /mnt/limits: sunk,popped,element)
[ -f /mnt/limits ] && { mkdir -p $HOME/.config; printf '[StereoDepth]\nSunkLimit=%s\nPoppedLimit=%s\nElementLimit=%s\n' $(tr ',' ' ' < /mnt/limits) > $HOME/.config/kwinrc; }
# a whole kwinrc for the case (/mnt/kwinrc), when it needs more than the limits
[ -f /mnt/kwinrc ] && { mkdir -p $HOME/.config; cp /mnt/kwinrc $HOME/.config/kwinrc; }
kwin_wayland --drm --socket=wl-stereo --no-lockscreen --no-global-shortcuts --no-kactivities > /mnt/kwin.log 2>&1 &
kp=$!
i=0
while [ $i -lt 120 ] && [ ! -S $XDG_RUNTIME_DIR/wl-stereo ]; do sleep 0.5; i=$((i + 1)); done
log "kwin: socket after $i half seconds"
export WAYLAND_DISPLAY=wl-stereo QT_QPA_PLATFORM=wayland LIBGL_ALWAYS_SOFTWARE=1
sleep 4
kscreen-doctor -o 2>&1 | sed 's/\x1b\[[0-9;]*m//g' > /mnt/doctor.txt
modeid() { # modeid SIZE RATE TAGS: the lowest id of that mode
    python3 - "$1" "$2" "$3" <<'PY'
import re, sys
best = None
for m in re.finditer(r"(\d+):(\d+x\d+)@([0-9.]+)((?:\([^)]*\))*)[*!]*", open("/mnt/doctor.txt").read()):
    if (m.group(2), m.group(3), m.group(4)) == tuple(sys.argv[1:4]):
        best = int(m.group(1)) if best is None else min(best, int(m.group(1)))
print(best if best is not None else "")
PY
}
setmode() { # setmode TAG: plain, sbs-full, sbs-half, tab, fp
    case $1 in
    plain) id=$(modeid 1920x1080 60.00 "") ;;
    sbs-full) id=$(modeid 1920x1080 60.00 "(3D-SBS-full)") ;;
    sbs-half) id=$(modeid 1920x1080 60.00 "(3D-SBS)") ;;
    tab) id=$(modeid 1920x1080 60.00 "(3D-TaB)") ;;
    fp) id=$(modeid 1920x1080 24.00 "(3D-FP)") ;;
    esac
    [ -n "$id" ] || { log "$1: no such mode"; return 1; }
    kscreen-doctor output.HDMI-A-1.mode.$id > /mnt/set-$1.txt 2>&1
    log "$1: mode id $id, kscreen-doctor exit $?"
    sleep 3
}
grab() { # grab TAG: the output's scanned-out frame once two grabs a second apart are the same
    t=0
    while [ $t -lt ${GRAB_TRIES:-20} ]; do
        /tmp/drm-grab /dev/dri/card0 /tmp/a.ppm HDMI-A-1 > /tmp/a.txt 2>&1
        sleep 1
        /tmp/drm-grab /dev/dri/card0 /tmp/b.ppm HDMI-A-1 > /tmp/b.txt 2>&1
        cmp -s /tmp/a.ppm /tmp/b.ppm && [ "$(sed -n 's/^nonblack //p' /tmp/b.txt)" -gt 0 ] 2>/dev/null && break
        t=$((t + 1))
    done
    cp /tmp/b.ppm /mnt/$1.ppm
    cp /tmp/b.txt /mnt/grab-$1.txt
    log "$1: $(grep '^mode\|^fb' /tmp/b.txt | tr '\n' ' ')after $((t + 1)) pairs"
}
passes() { # passes TAG: KWin's own choice per frame since the last call
    n=$(wc -l < /mnt/kwin.log)
    tail -n +$((${last:-0} + 1)) /mnt/kwin.log | grep -o 'scene pass[^,]*' | sort | uniq -c | tr '\n' ';' | sed "s/^/STEREO|realoutput|$1 kwin: /"; echo
    last=$n
}
. /mnt/case.sh
kill $kp
wait $kp
log "kwin exit $?"
