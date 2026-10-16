# SPDX-License-Identifier: GPL-2.0-or-later
# Runs in the root's chroot as root, when the kernel command line has bench.depth=1: Stereo KWin on a
# VKMS device whose EDID declares every HDMI 1.4a 3D structure (edid/stereo-whole.bin). Two fresh
# sessions, each case with its own frames in /tmp/out; tools/analyze-kwin-depth.py checks them.
#   Session a, the desktop's depth levels as shipped (sunk 10, popped 4): an inactive orange window and
#   the depth client (a window whose noise patch has 8 pixels of parallax) in side by side (full), to
#   measure each one's parallax between the eyes, then in L + depth with each depth source, a viewing
#   distance, the views exchanged (the control of the sign), line alternative with the stereo client,
#   side by side (full) with the blanking kept, and at 720p frame packing and L + depth + graphics +
#   graphics-depth with a popup.
#   Session b, no depth levels: L + depth with flat depth against the 2D mode, which must show the same
#   picture.
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/root XDG_RUNTIME_DIR=/run/user/0 LANG=C.UTF-8 LC_ALL=C.UTF-8 KWIN_DRM_DEVICES=/dev/dri/card0
mkdir -p $XDG_RUNTIME_DIR /tmp/bin $HOME/.config && chmod 700 $XDG_RUNTIME_DIR
log() { echo "STEREO|kwin-depth|$*"; }
if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
    exec dbus-run-session -- sh /tmp/kwin-depth-steps.sh
fi

cd /tmp/src
xml=/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml
stereo=/usr/share/plasma-wayland-protocols/kde-stereo-content-v1.xml
wayland-scanner client-header $xml xdg-shell-client-protocol.h &&
wayland-scanner private-code $xml xdg-shell-protocol.c &&
wayland-scanner client-header $stereo kde-stereo-content-v1-client-protocol.h &&
wayland-scanner private-code $stereo kde-stereo-content-v1-protocol.c &&
gcc -O2 -o /tmp/bin/stereo-subsurface stereo-subsurface.c xdg-shell-protocol.c \
    $(pkg-config --cflags --libs wayland-client wayland-egl egl gl) &&
gcc -O2 -o /tmp/bin/depth-client depth-client.c xdg-shell-protocol.c kde-stereo-content-v1-protocol.c \
    $(pkg-config --cflags --libs wayland-client) ||
    { echo "STEREO|check|kwin-depth/clients|FAIL|could not build the test clients"; exit 1; }
cd /

kp=
start_kwin() { # start_kwin SESSION SUNK POPPED
    printf '[StereoDepth]\nSunkLimit=%s\nPoppedLimit=%s\n' "$2" "$3" > $HOME/.config/kwinrc
    rm -f $HOME/.config/kwinoutputconfig.json
    kwin_wayland --drm --socket=wl-depth --no-lockscreen --no-global-shortcuts --no-kactivities > /tmp/out/kwin-depth-$1.log 2>&1 &
    kp=$!
    i=0
    while [ $i -lt 120 ] && [ ! -S $XDG_RUNTIME_DIR/wl-depth ]; do sleep 0.5; i=$((i + 1)); done
    export WAYLAND_DISPLAY=wl-depth
    sleep 4
    QT_QPA_PLATFORM=wayland kscreen-doctor -o 2>&1 | sed 's/\x1b\[[0-9;]*m//g' > /tmp/out/kscreen-depth-$1.txt
    output=$(grep -m1 '^Output:' /tmp/out/kscreen-depth-$1.txt | awk '{print $3}')
    log "session $1: socket after $i half seconds, output ${output:-none}"
}
stop_kwin() {
    kill $kp
    wait $kp
    log "kwin exit $?"
    rm -f $XDG_RUNTIME_DIR/wl-depth $XDG_RUNTIME_DIR/wl-depth.lock
}
listing=
mode_id() {
    tr ' ' '\n' < $listing | grep -F ":$1" | grep -v -F "$1(" | head -1 | cut -d: -f1
}
doctor() {
    QT_QPA_PLATFORM=wayland kscreen-doctor "$@" > /tmp/out/doctor.txt 2>&1
    log "kscreen-doctor $* exit $?"
    sleep 4
}
set_mode() { # set_mode MODE
    id=$(mode_id "$1")
    if [ -z "$id" ]; then log "no mode $1"; return 1; fi
    doctor output.$output.mode.$id
}
grab() {
    /tmp/drm-grab /dev/dri/card0 /tmp/out/depth-$1.ppm > /tmp/out/depth-grab-$1.txt 2>&1
    log "$1: $(grep '^mode\|^fb\|^connector' /tmp/out/depth-grab-$1.txt | tr '\n' ' ')"
}
# grab_shown TAG: until the frame shows something besides black, 30 tries at most
grab_shown() {
    t=0
    while [ $t -lt 30 ]; do
        sleep 1
        grab $1
        [ "$(sed -n 's/^nonblack //p' /tmp/out/depth-grab-$1.txt)" -gt 0 ] 2>/dev/null && break
        t=$((t + 1))
    done
}
clients=
client() { # client ENV...: a depth-client with these settings, kept until the session's clients end
    env HOLD_SECONDS=600 "$@" /tmp/bin/depth-client >> /tmp/out/client-depth.log 2>&1 &
    clients="$clients $!"
    sleep 3
}
end_clients() {
    for c in $clients; do kill $c; wait $c; done
    clients=
}

start_kwin a 10 4
listing=/tmp/out/kscreen-depth-a.txt
log "3D modes listed: $(grep -o '(3D-[A-Za-z+-]*)' $listing | sort | uniq -c | tr '\n' ' ')"
# the orange window first, so that the depth client is active and the orange one sinks
client NO_STEREO=1 COLOR=ff8000
client PARALLAX=8
set_mode "1920x1080@60.00(3D-SBS-full)" && grab_shown a-sbsfull
set_mode "1920x1080@50.00(3D-L+depth)" && sleep 4 && grab_shown a-ldepth
doctor output.$output.stereoDepth.desktop && grab a-ldepth-desktop
doctor output.$output.stereoDepth.flat && grab a-ldepth-flat
doctor output.$output.stereoDepth.desktopAndContent output.$output.viewingDistance.250 && sleep 4 && grab a-ldepth-250
end_clients
client NO_STEREO=1 COLOR=ff8000
client PARALLAX=-8
sleep 4
grab a-ldepth-swapped
end_clients
LIBGL_ALWAYS_SOFTWARE=1 HOLD_SECONDS=60 /tmp/bin/stereo-subsurface > /tmp/out/client-depth-subsurface.log 2>&1 &
cp=$!
set_mode "1920x1080@60.00(3D-line-alt)" && grab_shown a-linealt
kill $cp; wait $cp
client NO_STEREO=1 COLOR=ff8000
client PARALLAX=8
set_mode "1920x1080@60.00(3D-SBS-full)" && doctor output.$output.sideBySideFullTiming.blankingKept && grab_shown a-sbsfull-kept
doctor output.$output.sideBySideFullTiming.wholeLineDoubled
end_clients
client PARALLAX=8 POPUP=1
set_mode "1280x720@60.00(3D-FP)" && grab_shown a-fp720
set_mode "1280x720@60.00(3D-L+depth+gfx)" && sleep 4 && grab_shown a-ldgg
end_clients
stop_kwin

start_kwin b 0 0
listing=/tmp/out/kscreen-depth-b.txt
client NO_STEREO=1 COLOR=ff8000
client PARALLAX=8
set_mode "1920x1080@50.00(3D-L+depth)" && doctor output.$output.stereoDepth.flat && grab_shown b-ldepth-flat
set_mode "1920x1080@50.00" && grab_shown b-2d
end_clients
stop_kwin
