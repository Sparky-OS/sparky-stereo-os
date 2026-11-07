# SPDX-License-Identifier: GPL-2.0-or-later
log() { echo "STEREO|eyeorder|$*"; }
scenario=$(cat /tmp/scenario)
startkwin() {
    kwin_wayland --drm --socket=wl-stereo --no-lockscreen --no-global-shortcuts --no-kactivities > /mnt/kwin-$1.log 2>&1 &
    kp=$!
    i=0
    while [ $i -lt 120 ] && [ ! -S $XDG_RUNTIME_DIR/wl-stereo ]; do sleep 0.5; i=$((i + 1)); done
    log "kwin $1: socket after $i half seconds"
    export WAYLAND_DISPLAY=wl-stereo QT_QPA_PLATFORM=wayland
    sleep 4
}
stopkwin() {
    kill $kp
    wait $kp
    log "kwin exit $?"
    rm -f $XDG_RUNTIME_DIR/wl-stereo $XDG_RUNTIME_DIR/wl-stereo.lock
}
doctor() { kscreen-doctor -o 2>&1 | sed 's/\x1b\[[0-9;]*m//g' > /mnt/doctor-$1.txt; }
startkwin first
doctor first
stopkwin
ls -la /root/.config 2>&1 | sed 's/^/STEREO|info|config|/'
cp /root/.config/kwinoutputconfig.json /mnt/kwinoutputconfig-first.json 2>/dev/null
log "config: $(wc -c < /root/.config/kwinoutputconfig.json 2>/dev/null) bytes"
python3 - <<'PY'
import json
p = "/root/.config/kwinoutputconfig.json"
cfg = json.load(open(p))
n = 0
for entry in cfg:
    if entry.get("name") == "outputs":
        for o in entry["data"]:
            o["anaglyph"] = True
            o["otherStereoFormats"] = True
            n += 1
json.dump(cfg, open(p, "w"), indent=1)
print("STEREO|eyeorder|toggles set on", n, "outputs")
PY
startkwin second
doctor second
log "outputs: $(grep -c . /mnt/doctor-second.txt) lines"
if [ "$scenario" = list ]; then stopkwin; exit 0; fi

# the matrix: every 3D mode of the output with the eye swap off and on
cat > /tmp/pick.py <<'PICK'
import re, sys
text = open("/mnt/doctor-second.txt").read()
modes = {}
for m in re.finditer(r"(\d+):(\d+x\d+)@([0-9.]+)((?:\([^)]*\))*)[*!]*", text):
    modes.setdefault((m.group(2), m.group(3), m.group(4)), int(m.group(1)))
    modes[(m.group(2), m.group(3), m.group(4))] = min(modes[(m.group(2), m.group(3), m.group(4))], int(m.group(1)))
want = {
 "plain": ("1920x1080", "60.00", ""),
 "anaglyph-modern": ("1920x1080", "60.00", "(virtual-3D:5)"),
 "anaglyph-crt": ("1920x1080", "60.00", "(virtual-3D:6)"),
 "twin-sbs-half": ("1920x1080", "60.00", "(3D-SBS)(virtual-3D:1)"),
 "twin-tab": ("1920x1080", "60.00", "(3D-TaB)(virtual-3D:2)"),
 "rows-left": ("1920x1080", "60.00", "(virtual-3D:7)"),
 "rows-right": ("1920x1080", "60.00", "(virtual-3D:8)"),
 "columns-left": ("1920x1080", "60.00", "(virtual-3D:9)"),
 "columns-right": ("1920x1080", "60.00", "(virtual-3D:10)"),
 "checkerboard-left": ("1920x1080", "60.00", "(virtual-3D:11)"),
 "checkerboard-right": ("1920x1080", "60.00", "(virtual-3D:12)"),
 "fs-left": ("1920x1080", "120.00", "(virtual-3D:13)"),
 "fs-right": ("1920x1080", "120.00", "(virtual-3D:14)"),
 "hdmi-sbs-half": ("1920x1080", "60.00", "(3D-SBS)"),
 "hdmi-tab": ("1920x1080", "60.00", "(3D-TaB)"),
 "hdmi-sbs-full": ("1920x1080", "60.00", "(3D-SBS-full)"),
 "hdmi-fp": ("1920x1080", "24.00", "(3D-FP)"),
}
for tag, key in want.items():
    print(tag, modes.get(key, ""))
PICK
python3 /tmp/pick.py > /mnt/modes.txt
log "modes: $(grep -c ' [0-9]' /mnt/modes.txt) of $(grep -c . /mnt/modes.txt) found"
LIBGL_ALWAYS_SOFTWARE=1 STILL=1 HOLD_SECONDS=3000 /tmp/egl-stereo-subsurface > /mnt/client-stereo.log 2>&1 &
sleep 6
log "client: $(head -1 /mnt/client-stereo.log)"
grab() { # grab TAG: the output's frame once two grabs a second apart are the same
    t=0
    while [ $t -lt 20 ]; do
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
setmode() { # setmode TAG SWAP(enable|disable)
    id=$(sed -n "s/^$1 //p" /mnt/modes.txt)
    if [ -z "$id" ]; then log "$1: no such mode"; return 1; fi
    kscreen-doctor output.HDMI-A-1.mode.$id output.HDMI-A-1.swapEyes.$2 > /mnt/set-$1-$2.txt 2>&1
    log "$1 swap $2: mode id $id, kscreen-doctor exit $?"
    sleep 3
}
setmode plain disable && grab ref
for tag in plain anaglyph-modern anaglyph-crt twin-sbs-half twin-tab rows-left rows-right columns-left columns-right \
           checkerboard-left checkerboard-right fs-left fs-right hdmi-sbs-half hdmi-tab hdmi-sbs-full hdmi-fp; do
    for sw in disable enable; do
        n=$tag-s0; [ $sw = enable ] && n=$tag-s1
        setmode $tag $sw || continue
        grab $n
        case $tag in
        fs-*)
            /tmp/drm-flipwatch /dev/dri/card0 HDMI-A-1 240 > /mnt/flips-$n.txt 2>&1
            log "$n flips: $(head -1 /mnt/flips-$n.txt); $(grep -c '^seq' /mnt/flips-$n.txt) samples"
            ;;
        esac
    done
done
setmode plain disable && grab back-2d
stopkwin
