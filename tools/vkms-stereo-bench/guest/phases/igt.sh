# SPDX-License-Identifier: GPL-2.0-or-later
# IGT's kms_3d on a VKMS device with an HDMI-A connector reading an EDID (kms_3d forces its own 3D EDID
# through debugfs). IGT runs from a root file system shared read only over 9p (tag "root"), in a chroot.
# Boot with vkms.create_default_dev=0 so the configfs device is the only card.
. /phases/lib.sh
mkvkms igt stereo-test || echo "STEREO|check|configfs/igt|FAIL|could not create the device"
mkdir -p /r
if ! mount -t 9p -o trans=virtio,version=9p2000.L,ro root /r; then
    echo "STEREO|check|kms_3d|FAIL|no root file system shared"
    return 0
fi
mount -t proc proc /r/proc
mount -t sysfs sysfs /r/sys
mount -t debugfs debugfs /r/sys/kernel/debug
mount -t devtmpfs devtmpfs /r/dev
mount -t tmpfs tmpfs /r/tmp
# IGT leaves vkms out of DRIVER_ANY; IGT_FORCE_DRIVER selects it
chroot /r /usr/bin/env IGT_FORCE_DRIVER=vkms /usr/local/bin/kms_3d 2>&1
rc=$?
if [ $rc = 0 ]; then
    echo "STEREO|check|kms_3d|PASS|subtest basic"
else
    echo "STEREO|check|kms_3d|FAIL|exit $rc"
fi
