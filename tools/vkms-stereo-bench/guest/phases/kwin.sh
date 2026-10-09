# SPDX-License-Identifier: GPL-2.0-or-later
# Stereo KWin on a VKMS device with an HDMI-A connector reading the test EDID (the one with side by side
# (full) with bench.sbs_full=1). KWin runs from a root file
# system shared read only over 9p (tag "root") with Stereo KWin, kscreen-doctor (with Qt's Wayland shell
# integration), Mesa, D-Bus, and gcc with the Wayland and EGL development files for the two test clients.
# Boot a kernel built with kconfig/vkms-stereo-full.fragment, with vkms.create_default_dev=0.
. /phases/lib.sh
edid=stereo-test
cmdline_has bench.sbs_full=1 && edid=stereo-full
mkvkms kwin $edid || echo "STEREO|check|configfs/kwin|FAIL|could not create the device"
mkdir -p /r
if ! mount -t 9p -o trans=virtio,version=9p2000.L,ro,cache=loose root /r; then
    echo "STEREO|check|kwin|FAIL|no root file system shared"
    return 0
fi
mount -t proc proc /r/proc
mount -t sysfs sysfs /r/sys
mount -t devtmpfs devtmpfs /r/dev
mkdir -p /r/dev/pts /r/dev/shm
mount -t devpts devpts /r/dev/pts
mount -t tmpfs tmpfs /r/dev/shm
for d in /r/tmp /r/run /r/root /r/var/tmp; do mount -t tmpfs tmpfs $d; done
mkdir -p /r/tmp/out /r/tmp/src
mount --bind /out /r/tmp/out
cp /src/* /r/tmp/src/
cp /bin/drm-grab /phases/kwin-steps.sh /r/tmp/
chroot /r /bin/sh /tmp/kwin-steps.sh
echo "STEREO|exit|kwin|$?"
umount /r/tmp/out 2>/dev/null
