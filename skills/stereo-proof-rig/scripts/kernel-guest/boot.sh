#!/bin/bash
# Created by Daniel Ramos (Capitain Jack) 2026/11/18
# Copyright 2026 under the GNU GPL3 License
# boot.sh DISK PORT: the guest of mkroot.sh on the HOST'S OWN KERNEL and initrd (the edition's, with its modules in the image), KVM, user networking with ssh on 127.0.0.1:PORT,
# the serial console as a socket (VMDIR/ser-PORT.sock) and a log (VMDIR/serial-PORT.log), the monitor at VMDIR/mon-PORT.sock. DISK is a qcow2 overlay (never the base).
# No -nographic: nothing here touches the host's display, input or devices. VMDIR defaults to this folder; KERNEL to the running kernel's.
D=${1:?disk overlay}; P=${2:-2222}; V=${VMDIR:-$(cd "$(dirname "$0")" && pwd)}; K=${KERNEL:-$(uname -r)}
exec qemu-system-x86_64 -enable-kvm -cpu host -smp ${SMP:-4} -m ${MEM:-6144} -kernel /boot/vmlinuz-$K -initrd /boot/initrd.img-$K \
 -append "root=/dev/vda rw console=ttyS0 net.ifnames=0 systemd.show_status=0 quiet" -drive file=$D,if=virtio,format=qcow2 \
 -nic user,hostfwd=tcp:127.0.0.1:$P-:22 -device virtio-gpu-pci -display none -chardev socket,id=s0,path=$V/ser-$P.sock,server=on,wait=off,logfile=$V/serial-$P.log -serial chardev:s0 \
 -monitor unix:$V/mon-$P.sock,server,nowait -pidfile $V/pid-$P
