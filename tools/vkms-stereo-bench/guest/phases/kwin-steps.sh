# SPDX-License-Identifier: GPL-2.0-or-later
# Runs in the root's chroot as root. Builds the two test clients, starts KWin on the VKMS card in a D-Bus
# session, then for each 1920x1080 3D mode: sets it with kscreen-doctor, and grabs the scanned-out frame
# with the desktop alone, with a fullscreen 2D client, with the stereo client and with the stereo client
# as a plain 2D one. The frames go to /tmp/out (the run directory); tools/analyze-kwin.py checks them.
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/root XDG_RUNTIME_DIR=/run/user/0 LANG=C.UTF-8 LC_ALL=C.UTF-8 KWIN_DRM_DEVICES=/dev/dri/card0
mkdir -p $XDG_RUNTIME_DIR /tmp/bin && chmod 700 $XDG_RUNTIME_DIR
log() { echo "STEREO|kwin|$*"; }
if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
    exec dbus-run-session -- sh /tmp/kwin-steps.sh
fi

cd /tmp/src
xml=/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml
wayland-scanner client-header $xml xdg-shell-client-protocol.h &&
wayland-scanner private-code $xml xdg-shell-protocol.c &&
gcc -O2 -o /tmp/bin/stereo-subsurface stereo-subsurface.c xdg-shell-protocol.c \
    $(pkg-config --cflags --libs wayland-client wayland-egl egl gl) &&
gcc -O2 -o /tmp/bin/fullscreen-2d fullscreen-2d.c xdg-shell-protocol.c $(pkg-config --cflags --libs wayland-client) ||
    { echo "STEREO|check|kwin/clients|FAIL|could not build the test clients"; exit 1; }
cd /

kwin_wayland --drm --socket=wl-stereo --no-lockscreen --no-global-shortcuts --no-kactivities > /tmp/out/kwin.log 2>&1 &
kp=$!
i=0
while [ $i -lt 120 ] && [ ! -S $XDG_RUNTIME_DIR/wl-stereo ]; do sleep 0.5; i=$((i + 1)); done
log "socket after $i half seconds"
export WAYLAND_DISPLAY=wl-stereo
sleep 4
QT_QPA_PLATFORM=wayland kscreen-doctor -o 2>&1 | sed 's/\x1b\[[0-9;]*m//g' > /tmp/out/kscreen-outputs.txt
output=$(grep -m1 '^Output:' /tmp/out/kscreen-outputs.txt | awk '{print $3}')
log "output ${output:-none}, $(grep -o '(3D-[A-Za-z-]*)' /tmp/out/kscreen-outputs.txt | wc -l) 3D modes listed"

# mode_id "1920x1080@24.00(3D-FP)": the id kscreen-doctor gives that mode
mode_id() {
    tr ' ' '\n' < /tmp/out/kscreen-outputs.txt | grep -F ":$1" | grep -v -F "$1(" | head -1 | cut -d: -f1
}
grab() {
    /tmp/drm-grab /dev/dri/card0 /tmp/out/kwin-$1.ppm > /tmp/out/grab-$1.txt 2>&1
}
# grab_shown TAG: grab until the frame shows something (the client is on screen), 30 tries at most
grab_shown() {
    t=0
    while [ $t -lt 30 ]; do
        sleep 1
        grab $1
        [ "$(sed -n 's/^nonblack //p' /tmp/out/grab-$1.txt)" -gt 0 ] 2>/dev/null && break
        t=$((t + 1))
    done
    log "$1 after $((t + 1)) grabs"
}
# Clients render with Mesa's software path: VKMS has no render node.
shoot() { # shoot TAG MODE
    id=$(mode_id "$2")
    if [ -z "$id" ]; then log "$1: no mode $2"; return; fi
    QT_QPA_PLATFORM=wayland kscreen-doctor output.$output.mode.$id > /tmp/out/kscreen-$1.txt 2>&1
    log "$1: mode $2 (id $id), kscreen-doctor exit $?"
    sleep 4
    grab $1-desktop
    log "$1: $(grep '^mode\|^fb' /tmp/out/grab-$1-desktop.txt | tr '\n' ' ')"
    HOLD_SECONDS=60 /tmp/bin/fullscreen-2d > /tmp/out/client-$1-fullscreen.log 2>&1 &
    cp=$!; sleep 2; grab_shown $1-fullscreen; kill $cp; wait $cp
    LIBGL_ALWAYS_SOFTWARE=1 HOLD_SECONDS=60 /tmp/bin/stereo-subsurface > /tmp/out/client-$1.log 2>&1 &
    cp=$!; sleep 2; grab_shown $1-client; kill $cp; wait $cp
    LIBGL_ALWAYS_SOFTWARE=1 NO_STEREO=1 HOLD_SECONDS=60 /tmp/bin/stereo-subsurface > /tmp/out/client-$1-2d.log 2>&1 &
    cp=$!; sleep 2; grab_shown $1-client2d; kill $cp; wait $cp
    sleep 1
}
shoot fp "1920x1080@24.00(3D-FP)"
shoot tab "1920x1080@60.00(3D-TaB)"
shoot sbs-half "1920x1080@60.00(3D-SBS)"
shoot sbs-full "1920x1080@60.00(3D-SBS-full)"
shoot 2d "1920x1080@60.00"
kill $kp
wait $kp
log "kwin exit $?"
