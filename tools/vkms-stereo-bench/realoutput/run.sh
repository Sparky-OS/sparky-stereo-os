#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# run.sh NAME CASE.sh [ROOT]: one disposable guest (KVM, no network, no display, no card); VKMS exists only inside it.
# BENCH is the bench folder (README.md); the case script is sourced in the guest session by steps.sh, and the run's
# folder is the guest's /mnt. EXTRA names a folder whose files are copied into the run's folder first (clients,
# the buffer recorder).
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
B=${BENCH:?the bench folder}
NAME=$1; CASE=$2; ROOT=${3:-$B/root}
OUT=$B/runs/$NAME
mkdir -p "$OUT"
[ -z "$(ls -A "$OUT")" ] || { echo "run folder $OUT is not empty" >&2; exit 2; }
cp "$CASE" "$OUT/case.sh"
if [ -n "${EXTRA:-}" ]; then cp "$EXTRA"/* "$OUT/"; fi
T=$(mktemp -d "$B/tmp.XXXXXX")
cp -a "$B/initramfs/." "$T/"
mkdir -p "$T/realoutput"
cp "$HERE/realoutput.sh" "$T/phases/"
cp "$HERE/session.sh" "$HERE/steps.sh" "$T/realoutput/"
cp "$B"/edid/*.bin "$T/data/"
cp "$B/bin/drm-grab" "$B/bin/drm-planelog" "$T/bin/"
python3 "$B/mkcpio.py" "$T" "$OUT/init.cpio.gz"
find "$T" -depth -delete
timeout "${VM_TIMEOUT:-900}" qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp 4 -m 6G -no-reboot -nodefaults \
    -kernel "$B/vm/bzImage-full" -initrd "$OUT/init.cpio.gz" \
    -append "console=ttyS0 panic=-1 loglevel=4 vkms.create_default_dev=0 stereo.phase=realoutput" \
    -virtfs "local,path=$ROOT,mount_tag=kwinroot,security_model=none,readonly=on,id=kwinroot" \
    -virtfs "local,path=$OUT,mount_tag=out,security_model=none,id=out" \
    -vga none -display none -serial "file:$OUT/console.log" > "$OUT/qemu.log" 2>&1 || echo "qemu exit $?"
grep -a "STEREO|" "$OUT/console.log" | grep -v "STEREO|info" | tail -40
