# SPDX-License-Identifier: GPL-2.0-or-later
# Helpers for the phases: a configfs VKMS device and the card node of a device.

# mkvkms NAME EDID [overlay] [writeback]: a VKMS device with a primary and a cursor plane (and an
# overlay plane), one CRTC (with a writeback connector), one encoder and an HDMI-A connector that reads
# /data/EDID.bin through the "edid" and "edid_enabled" attributes.
mkvkms() {
    d=/sys/kernel/config/vkms/$1
    mkdir $d || return 1
    mkdir $d/planes/primary $d/planes/cursor $d/crtcs/crtc0 $d/encoders/encoder0 $d/connectors/hdmi0 || return 1
    echo 1 > $d/planes/primary/type
    echo 2 > $d/planes/cursor/type
    planes="primary cursor"
    case " $* " in *" overlay "*)
        mkdir $d/planes/overlay && echo 0 > $d/planes/overlay/type && planes="$planes overlay" ;;
    esac
    case " $* " in *" writeback "*) echo 1 > $d/crtcs/crtc0/writeback ;; esac
    for p in $planes; do ln -s $d/crtcs/crtc0 $d/planes/$p/possible_crtcs/crtc0; done
    ln -s $d/crtcs/crtc0 $d/encoders/encoder0/possible_crtcs/crtc0
    echo 11 > $d/connectors/hdmi0/type
    cat /data/$2.bin > $d/connectors/hdmi0/edid
    echo 1 > $d/connectors/hdmi0/edid_enabled
    ln -s $d/encoders/encoder0 $d/connectors/hdmi0/possible_encoders/encoder0
    echo 1 > $d/enabled
}

# card_of NAME: /dev/dri/cardN of the VKMS device NAME (the configfs directory, or "vkms" for the default one)
card_of() {
    for c in /sys/class/drm/card*; do
        case "${c##*/}" in *-*) continue ;; esac
        [ "$(basename "$(readlink -f "$c/device")")" = "$1" ] && echo "/dev/dri/${c##*/}"
    done
}

cmdline_has() {
    case " $(cat /proc/cmdline) " in *" $1 "*) return 0 ;; esac
    return 1
}
