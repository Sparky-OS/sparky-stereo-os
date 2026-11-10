#!/bin/bash
# The Plymouth guest rig: an initramfs holding Plymouth, a theme, udev and a tiny init (./init), booted by QEMU
# (virtio-vga with stereo on) under a kernel that has virtio-gpu. Nothing of it runs on the machine you work on.
#   mkrig.sh VARIANT THEME_DEB [PLYMOUTH_DEBS_DIR]
#     VARIANT            the initramfs is $RIG/initrd-VARIANT.img
#     THEME_DEB          the splash theme package (a .deb whose files are unpacked into the image)
#     PLYMOUTH_DEBS_DIR  plymouth, libplymouth5 and plymouth-label .debs unpacked over the repository's (the build
#                        under test); without it the repository's published Plymouth stays (the red rig)
# Environment: DOCKER_HOST (your own Docker socket), RIG (output folder), BASE (a Debian testing image with kmod, python3),
# REPO (a flat repository folder with sparky-stereo-repo.asc, mounted read only), KVER (the kernel's version, its modules
# are read from /lib/modules/$KVER), HTTPS_ONLY_APT (the edition's apt helper).
set -euo pipefail
: "${RIG:?}" "${BASE:?}" "${REPO:?}" "${KVER:?}" "${HTTPS_ONLY_APT:?}"
VARIANT=${1:?variant} THEME=$(realpath "${2:?theme deb}") PDEBS=${3:-}
HERE=$(dirname "$(readlink -f "$0")")
mkdir -p "$RIG"
PM=()
[ -n "$PDEBS" ] && PM=(-v "$(realpath "$PDEBS")":/pdebs:ro)
docker run --rm --name "${PREFIX:-rig}-mkrig-$VARIANT" --ulimit core=0 --platform linux/amd64 --user 0 \
	-e OWNER="$(id -u):$(id -g)" -e KVER="$KVER" -e VARIANT="$VARIANT" "${PM[@]}" \
	-v "$RIG":/rig -v "$HERE":/here:ro -v "$THEME":/theme.deb:ro -v "$(readlink -f "$REPO")":/repo:ro \
	-v "/lib/modules/$KVER":"/hm/lib/modules/$KVER":ro \
	-v /etc/ssl/certs/ca-certificates.crt:/run/host-ca.crt:ro -v "$HTTPS_ONLY_APT":/run/https-only-apt.sh:ro \
	"$BASE" bash -c '
set -euo pipefail
sh /run/https-only-apt.sh
export DEBIAN_FRONTEND=noninteractive
cp /repo/sparky-stereo-repo.asc /usr/share/keyrings/
printf "Types: deb\nURIs: file:/repo\nSuites: mashtabba\nComponents: main\nSigned-By: /usr/share/keyrings/sparky-stereo-repo.asc\n" > /etc/apt/sources.list.d/sparky.sources
printf "Package: *\nPin: release o=Sparky Stereo OS\nPin-Priority: 1001\n" > /etc/apt/preferences.d/sparky
apt-get -y update >/dev/null
apt-get -y --no-install-recommends install plymouth plymouth-label kmod busybox xz-utils cpio udev >/dev/null 2>&1
[ -d /pdebs ] && for d in /pdebs/*.deb; do dpkg -x "$d" /; done
dpkg -x /theme.deb /
mkdir -p /lib/modules/$KVER
for m in $(modprobe -d /hm -S $KVER --show-depends virtio_gpu | sed -n "s/^insmod //p"); do
	dest=/lib/modules/$KVER/${m#/hm/lib/modules/$KVER/}; mkdir -p "$(dirname "$dest")"; cp "$m" "$dest"
done
depmod -b / $KVER
install -m 755 /here/init /init
mkdir -p /etc/plymouth
printf "[Daemon]\nTheme=${THEME_NAME:-sparky-stereo-lines}\nShowDelay=0\nDeviceTimeout=8\n" > /etc/plymouth/plymouthd.conf
( cd / && find . -xdev \( -path ./proc -o -path ./sys -o -path ./dev -o -path ./run -o -path ./rig -o -path ./here -o -path ./repo -o -path ./hm -o -path ./pdebs -o -path ./theme.deb -o -path ./var/cache -o -path ./var/lib/apt -o -path ./usr/share/doc -o -path ./usr/share/man -o -path ./usr/share/locale -o -path ./usr/include -o -path ./usr/lib/gcc -o -path ./tmp -o -path ./var/log -o -path ./usr/lib/python3 -o -path ./usr/share/perl -o -path ./usr/share/icons \) -prune -o -print0 | cpio -0 -o -H newc --quiet | gzip -1 > /rig/initrd-$VARIANT.img )
chown $OWNER /rig/initrd-$VARIANT.img
'
ls -la "$RIG/initrd-$VARIANT.img"
