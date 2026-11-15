#!/bin/bash
# SPDX-License-Identifier: MIT
# One capture of the qdiscs window in a fresh Stereo KWin session, inside a container that has a render node for
# KWin (kwin_wayland --virtual cannot be captured without one) and the edition's Qt, Qt Quick, Mesa and KWin.
# usage: case.sh OUTDIR
# environment: BACKEND=vulkan|opengl, ICD=lvp|radeon|nvidia (the Vulkan driver the client is given; lvp also makes
# its OpenGL software), STEREO=1|0 (the output in its side-by-side 3D mode, or plain 2D), W H (the virtual output),
# KSCALE (a fractional scale), WARM (seconds before the capture), CLIENT_ENV (more variables for the client, space
# separated: QDISCS_FLAT=1, QDISCS_LIFECYCLE=1, QDISCS_TOGGLE=1, QDISCS_OFF=1, QDISCS_FLICK=1, QDISCS_FRAMELESS=1,
# QDISCS_WIDTH=941,
# DISABLE_LAYER_MESA_STEREO=1), APP (the qdiscs binary), CAPTURE (stereo-proof-rig's scripts/capture.py),
# KEEPWIRE=1 keeps the whole protocol log, CSD=1 starts KWin without a decoration plugin so Qt draws its own frame.
# Leaves in OUTDIR: shot.png (both eyes side by side in a 3D mode), client.out (the STATE line), wire.txt (the
# stereo requests the client sent), qt.log (what Qt said, the device included), kwin.log.
set -u
ulimit -c 0
out=$1
export XDG_RUNTIME_DIR=/tmp/rt; mkdir -p $XDG_RUNTIME_DIR; chmod 700 $XDG_RUNTIME_DIR
export HOME=/tmp/home XDG_CONFIG_HOME=/tmp/home/.config XDG_DATA_HOME=/tmp/home/.local/share XDG_CACHE_HOME=/tmp/home/.cache
mkdir -p $XDG_CONFIG_HOME $XDG_DATA_HOME $XDG_CACHE_HOME
export LANG=C.UTF-8 QT_QPA_PLATFORM=wayland
W=${W:-1920}; H=${H:-1080}
printf '[KDE]\nCursorBlinkRate=0\nAnimationDurationFactor=0\n' > $XDG_CONFIG_HOME/kdeglobals
: > $XDG_CONFIG_HOME/kwinrc
[ "${CSD:-0}" = 1 ] && printf '[org.kde.kdecoration2]\nNoPlugin=true\n' >> $XDG_CONFIG_HOME/kwinrc
if [ "${STEREO:-1}" = 1 ]; then
  export KWIN_VIRTUAL_STEREO_MODES=1
  printf '[StereoDepth]\nSunkLimit=10\nPoppedLimit=4\nElementLimit=%s\n' "${ELEMENT_LIMIT:-1}" >> $XDG_CONFIG_HOME/kwinrc
fi
cat > /tmp/session.sh <<'S'
out=$1
KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 \
  kwin_wayland --virtual --socket=sub --width $W --height $H > $out/kwin.log 2>&1 &
kwin=$!
for i in $(seq 100); do [ -S $XDG_RUNTIME_DIR/sub ] && break; sleep 0.1; done
[ -S $XDG_RUNTIME_DIR/sub ] || { echo "kwin did not start"; tail -5 $out/kwin.log; exit 2; }
sleep 1
kd() { WAYLAND_DISPLAY=sub QT_QPA_PLATFORM=wayland kscreen-doctor "$@"; }
outname=$(kd -o 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | awk '/^Output:/{print $3; exit}')
if [ "${STEREO:-1}" = 1 ]; then
  mode=$(kd -o 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -o '[0-9]*:[^ ]*' | grep -i -m1 '3D-SBS' | cut -d: -f1)
  echo "stereo mode $mode on $outname" > $out/stereo-mode.txt
  kd output.$outname.mode.$mode >> $out/stereo-mode.txt 2>&1
  sleep 1
fi
if [ -n "${KSCALE:-}" ]; then
  kd output.$outname.scale.$KSCALE > $out/scale.txt 2>&1
  sleep 1
fi
kd -o 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -i 'scale\|Geometry\|\*' > $out/output.txt
IFS=' ' read -r -a CE <<< "${CLIENT_ENV:-}"
env WAYLAND_DISPLAY=sub WAYLAND_DEBUG=client QSG_INFO=1 QSG_RHI_BACKEND=${BACKEND:-vulkan} "${CE[@]}" ${APP:-qdiscs} > $out/client.out 2> $out/client.err &
cpid=$!
sleep ${WARM:-9}
python3 ${CAPTURE:-capture.py} $out/shot.png > $out/capture.json 2> $out/capture.err || cat $out/capture.err
kill -0 $cpid 2>/dev/null && echo alive > $out/client.alive || echo gone > $out/client.alive
kill $cpid 2>/dev/null; sleep 0.5; kill -9 $cpid 2>/dev/null
kill $kwin 2>/dev/null; wait $kwin 2>/dev/null
# what the client said about stereo on the wire, and what Qt said; the rest of the protocol log is dropped
grep -n -E "kde_stereo|set_destination" $out/client.err | head -400 > $out/wire.txt
grep -v -E "^\[[0-9:. ]+\] " $out/client.err | head -200 > $out/qt.log
[ "${KEEPWIRE:-0}" = 1 ] || rm -f $out/client.err
exit 0
S
case ${ICD:-} in
  lvp)    export VK_DRIVER_FILES=/usr/share/vulkan/icd.d/lvp_icd.json
          CLIENT_ENV="LIBGL_ALWAYS_SOFTWARE=1 __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json ${CLIENT_ENV:-}" ;;
  radeon) export VK_DRIVER_FILES=/usr/share/vulkan/icd.d/radeon_icd.json ;;
  nvidia) export VK_DRIVER_FILES=$(ls /etc/vulkan/icd.d/nvidia_icd.json /usr/share/vulkan/icd.d/nvidia_icd.json 2>/dev/null | head -1) ;;
esac
export W H CLIENT_ENV
exec dbus-run-session -- bash /tmp/session.sh "$out"
