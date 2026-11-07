# SPDX-License-Identifier: GPL-2.0-or-later
# ORDER 116: Stereo KWin on one VKMS HDMI-A connector that reads an EDID (stereo.edid=NAME), the eye-tagged client
# on it, and steps.sh (guest/eyeorder) setting every 3D mode with the output's eye swap off and on.
edid=stereo-full-120
scenario=list
for a in $(cat /proc/cmdline); do
    case "$a" in stereo.edid=*) edid=${a#stereo.edid=} ;; stereo.scenario=*) scenario=${a#stereo.scenario=} ;; esac
done
echo "STEREO|eyeorder|edid $edid scenario $scenario"
d=/sys/kernel/config/vkms/eo
mkdir $d || echo "STEREO|check|configfs|FAIL|"
mkdir $d/planes/primary0 $d/planes/cursor0 $d/crtcs/crtc0 $d/encoders/encoder0 $d/connectors/hdmi0
echo 1 > $d/planes/primary0/type
echo 2 > $d/planes/cursor0/type
ln -s $d/crtcs/crtc0 $d/planes/primary0/possible_crtcs/crtc0
ln -s $d/crtcs/crtc0 $d/planes/cursor0/possible_crtcs/crtc0
ln -s $d/crtcs/crtc0 $d/encoders/encoder0/possible_crtcs/crtc0
echo 11 > $d/connectors/hdmi0/type
ln -s $d/encoders/encoder0 $d/connectors/hdmi0/possible_encoders/encoder0
cat /data/$edid.bin > $d/connectors/hdmi0/edid
echo 1 > $d/connectors/hdmi0/edid_enabled
echo 1 > $d/enabled
ls -l /dev/dri | sed 's/^/STEREO|info|dri|/'
mkdir -p /k
mount -t 9p -o trans=virtio,version=9p2000.L,ro,cache=loose kwinroot /k || echo "STEREO|check|kwin-root|FAIL|no 9p root"
mount -t proc proc /k/proc
mount -t sysfs sysfs /k/sys
mount -t devtmpfs devtmpfs /k/dev
mkdir -p /k/dev/pts /k/dev/shm
mount -t devpts devpts /k/dev/pts
mount -t tmpfs tmpfs /k/dev/shm
for x in /k/tmp /k/run /k/root /k/var/tmp /k/home/tester; do mount -t tmpfs tmpfs $x; done
mount -t 9p -o trans=virtio,version=9p2000.L out /k/mnt || echo "STEREO|info|out|no evidence share"
cp /eyeorder/*.sh /k/tmp/
cp /bin/drm-grab /bin/drm-flipwatch /bin/fullscreen-2d /bin/egl-stereo-subsurface /k/tmp/
echo "$scenario" > /k/tmp/scenario
chroot /k /bin/sh /tmp/session.sh
echo "STEREO|exit|eyeorder|$?"
sync
umount /k/mnt 2>/dev/null
