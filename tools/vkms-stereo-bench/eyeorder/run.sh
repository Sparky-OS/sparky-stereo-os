#!/bin/sh
# run.sh NAME SCENARIO [EDID]: one disposable guest (KVM, no network, no display, no GPU); VKMS exists only inside it.
set -eu
B=$(cd "$(dirname "$0")" && pwd)
NAME=$1; SCEN=$2; EDID=${3:-stereo-full-120}
OUT=$B/runs/$NAME
rm -rf "$OUT"; mkdir -p "$OUT"
sh "$B/mkinit.sh" "$B/vm/eyeorder.cpio.gz"
docker rm -f eyeorder-vm >/dev/null 2>&1 || true
docker run --rm --name eyeorder-vm --network none --cpus 4 --memory 8g --ulimit core=0 --user "$(id -u):$(id -g)" \
    --device /dev/kvm --group-add "$(getent group kvm | cut -d: -f3)" -v "$B:$B" -v "$B/root:$B/root:ro" \
    ${QEMU_IMAGE:?an image with qemu-system-x86_64} \
    sh -c "timeout ${VM_TIMEOUT:-1500} qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp 4 -m 6G -no-reboot -nodefaults \
      -kernel $B/vm/bzImage-full -initrd $B/vm/eyeorder.cpio.gz \
      -append 'console=ttyS0 panic=-1 loglevel=4 vkms.create_default_dev=0 stereo.phase=eyeorder stereo.scenario=$SCEN stereo.edid=$EDID' \
      -virtfs local,path=$B/root,mount_tag=kwinroot,security_model=none,readonly=on,id=kwinroot \
      -virtfs local,path=$OUT,mount_tag=out,security_model=none,id=out \
      -vga none -display none -serial stdio" > "$OUT/console.log" 2> "$OUT/qemu.log" || true
grep -a "STEREO|" "$OUT/console.log" | grep -v "STEREO|info" | tail -40
