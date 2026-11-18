#!/bin/bash
# mkroot.sh: inside the rig image (a Plasma rig with KF6 and plasma-workspace, as root, with /vm the output folder, /hostmods the host kernel's /lib/modules/KERNEL read only,
# /vm/id_ed25519.pub the key allowed to log in, and the apt helper and CA mounted as in the other rigs): the guest's system, then an ext4 image of it (/vm/root.img, 6 GB sparse)
# that boot.sh starts on the host's kernel. Afterwards: qemu-img create -f qcow2 -b root.img -F raw base.qcow2 (the base), and an overlay per run.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
sh /run/https-only-apt.sh >/dev/null 2>&1
apt-get -y -qq update
apt-get -y -qq --no-install-recommends install systemd-sysv udev dbus dbus-daemon upower polkitd openssh-server kmod iproute2 procps sudo python3 e2fsprogs xz-utils psmisc less powerdevil kinfocenter umockdev libwayland-dev libwayland-bin >/dev/null
# the headset packages' own dependencies come at the proof; the user of the session
id rig >/dev/null 2>&1 || useradd -m -u 1001 -s /bin/bash rig
mkdir -p /root/.ssh; cp /vm/id_ed25519.pub /root/.ssh/authorized_keys; chmod 700 /root/.ssh; chmod 600 /root/.ssh/authorized_keys
mkdir -p /home/rig/.ssh; cp /vm/id_ed25519.pub /home/rig/.ssh/authorized_keys; chown -R rig:rig /home/rig/.ssh; chmod 700 /home/rig/.ssh
printf 'PermitRootLogin prohibit-password\nPasswordAuthentication no\nUseDNS no\n' >/etc/ssh/sshd_config.d/vm.conf
echo gr108vm >/etc/hostname
cp /vm/vm-net.service /etc/systemd/system/vm-net.service   # the first network device whatever its name (ens3, eth0), the address QEMU's user networking gives (10.0.2.15)
systemctl enable vm-net.service ssh.service >/dev/null 2>&1 || ln -sf /etc/systemd/system/vm-net.service /etc/systemd/system/multi-user.target.wants/vm-net.service
printf '/dev/vda / ext4 rw 0 1\n' >/etc/fstab
# kernel modules of the booted kernel (copied from the host, read only there)
mkdir -p /lib/modules; cp -a /hostmods/. /lib/modules/7.3.4-stereo3d18
systemctl mask systemd-firstboot.service getty@tty1.service >/dev/null 2>&1 || true
passwd -d root >/dev/null
# the image
R=/vm/rootfs; mkdir -p $R
tar -C / --one-file-system --exclude=./vm --exclude=./hostmods --exclude=./proc --exclude=./sys --exclude=./dev --exclude=./run/host-ca.crt --exclude=./run/https-only-apt.sh -cf - . | tar -C $R -xpf -
mkdir -p $R/proc $R/sys $R/dev $R/run $R/tmp
mke2fs -q -t ext4 -d $R -L gr108vm /vm/root.img 6G
echo image-done
