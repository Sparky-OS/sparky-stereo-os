# SPDX-License-Identifier: GPL-2.0-or-later
# Helpers sourced by the bench guest scripts (busybox sh).
# The kernel command line, the initramfs and the hardware must be identical in the two boots of a scenario (x86 hibernation refuses an
# image when the memory map differs), so the per-boot settings come from a tiny control disk (virtio serial "benchctl"), not from the command line.
disk_by_serial() {   # disk_by_serial SERIAL -> name of the virtio disk (vda, vdb, ...)
    for d in /sys/block/vd*; do
        [ "$(cat "$d/serial" 2>/dev/null)" = "$1" ] && { basename "$d"; return; }
    done
}
load_ctl() {         # copy the control disk's first sector (text lines key=value) to /run/ctl.txt
    c=$(disk_by_serial benchctl)
    [ -n "$c" ] && dd if="/dev/$c" bs=512 count=1 2>/dev/null | tr -d '\000' > /run/ctl.txt
}
cmdline_opt() {      # cmdline_opt bench.foo -> value of bench.foo=value from the control disk, else from the kernel command line; empty if absent
    v=$(sed -n "s/^$1=//p" /run/ctl.txt 2>/dev/null | head -n 1)
    if [ -n "$v" ]; then echo "$v"; return; fi
    for w in $(cat /proc/cmdline); do
        case "$w" in "$1="*) echo "${w#*=}"; return;; esac
    done
}
bench_info() {    # bench_info key value...
    k=$1; shift
    echo "BENCH|info|$k|$*"
}
bench_check() {   # bench_check name PASS|FAIL|INFO detail...
    n=$1; r=$2; shift 2
    echo "BENCH|check|$n|$r|$*"
}
bench_dmesg() {   # bench_dmesg label egrep-pattern : print matching kernel log lines (max 12)
    dmesg | grep -E "$2" | tail -n 12 | while IFS= read -r l; do echo "BENCH|log|$1|$l"; done
}
tpm() { /bench/tpmcli "$@"; }
