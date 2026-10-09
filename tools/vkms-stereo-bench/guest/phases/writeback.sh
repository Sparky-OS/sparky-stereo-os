# SPDX-License-Identifier: GPL-2.0-or-later
# stereo-wb-test on configfs devices whose HDMI-A connector reads an EDID, and on the module's default device
# (no EDID) as the 2D control. bench.sbs_full=1 adds a device whose EDID also declares side by side (full).
. /phases/lib.sh
devices="stereo-test kdl-46hx855"
cmdline_has bench.sbs_full=1 && devices="$devices stereo-full"
for dev in $devices; do
    mkvkms $dev $dev overlay writeback || echo "STEREO|check|configfs/$dev|FAIL|could not create the device"
done
for dev in $devices vkms; do
    card=$(card_of $dev)
    echo "STEREO|info|card|$dev $card"
    if [ "$dev" = vkms ]; then
        stereo-wb-test "$card" --name "$dev" --out /out
    else
        stereo-wb-test "$card" --name "$dev" --expect "/data/$dev.expect" --out /out
    fi
    echo "STEREO|exit|$dev|$?"
done
