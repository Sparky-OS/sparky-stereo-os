#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not, as the [crash trap](../../../stereo-proof-rig/SKILL.md#traps-that-fooled-us) explains.
# mkrig.sh VARIANT THEME_DEB_OR_DIR PLYMOUTH_DEBS_DIR (a theme .deb, or a folder of every theme .deb of the set): the rig's initramfs ($RIGOUT/initrd-VARIANT.img), from the image
# $RIG_IMAGE (Debian testing with plymouth, plymouth-label, udev, kmod, busybox, cpio, gcc, libc6-dev, linux-libc-dev,
# fonts-dejavu-core installed: the README says how to make it), with the Plymouth build under test
# (plymouth, libplymouth5, plymouth-label .debs) and the theme unpacked over it, the static crtc-grab, the EDIDs, this
# folder's init, and the kernel's modules for VKMS, configfs and 9p. Nothing of it runs on the machine you work on.
# Environment: DOCKER_HOST, RIGOUT, KVER, RIG_IMAGE, PREFIX (your containers' name prefix).
set -euo pipefail
: "${RIGOUT:?}" "${KVER:?}" "${RIG_IMAGE:?}"
VARIANT=${1:?variant} THEME=$(realpath "${2:?theme deb or folder of theme debs}") PDEBS=$(realpath "${3:?plymouth debs dir}")
[ -d "$THEME" ] || { T=$(mktemp -d); cp "$THEME" "$T/"; THEME=$T; }
HERE=$(dirname "$(readlink -f "$0")")
mkdir -p "$RIGOUT"
docker run --rm --name "${PREFIX:-rig}-mkrig-$VARIANT" --ulimit core=1 --platform linux/amd64 --cpus 2 --network none --user 0 \
	-e OWNER="$(id -u):$(id -g)" -e KVER="$KVER" -e VARIANT="$VARIANT" \
	-v "$RIGOUT":/rig -v "$HERE":/here:ro -v "$THEME":/themes:ro -v "$PDEBS":/pdebs:ro \
	-v "/lib/modules/$KVER":"/hm/lib/modules/$KVER":ro \
	"$RIG_IMAGE" bash -c '
set -euo pipefail
for d in /pdebs/*.deb; do dpkg -x "$d" /; echo "unpacked $(basename "$d")"; done
for d in /themes/*.deb; do dpkg -x "$d" /; echo "unpacked theme $(basename "$d") $(dpkg-deb -f "$d" Version)"; done
mkdir -p /etc/plymouth /edid /usr/local/bin
printf "[Daemon]\nTheme=sparky-stereo-lines\nShowDelay=0\nDeviceTimeout=8\n" > /etc/plymouth/plymouthd.conf
cp /here/edid/*.bin /edid/
gcc -static -O2 -Wall -o /usr/local/bin/crtc-grab /here/crtc-grab.c
rm -rf /lib/modules/$KVER; mkdir -p /lib/modules/$KVER
for mod in vkms configfs 9p 9pnet_virtio; do
	for m in $(modprobe -d /hm -S $KVER --show-depends $mod | sed -n "s/^insmod //p"); do
		dest=/lib/modules/$KVER/${m#/hm/lib/modules/$KVER/}; mkdir -p "$(dirname "$dest")"; cp "$m" "$dest"
	done
done
cp /hm/lib/modules/$KVER/modules.order /hm/lib/modules/$KVER/modules.builtin* /lib/modules/$KVER/ 2>/dev/null || true
depmod -b / $KVER
install -m 755 /here/init /init
( cd / && find . -xdev \( -path ./proc -o -path ./sys -o -path ./dev -o -path ./run -o -path ./rig -o -path ./here -o -path ./hm -o -path ./pdebs -o -path ./themes -o -path ./var/cache -o -path ./var/lib/apt -o -path ./usr/share/doc -o -path ./usr/share/man -o -path ./usr/share/locale -o -path ./usr/include -o -path ./usr/lib/gcc -o -path ./usr/libexec/gcc -o -path ./tmp -o -path ./var/log -o -path "./usr/lib/python3*" -o -path ./usr/share/perl -o -path ./usr/share/icons -o -path "./usr/bin/x86_64-linux-gnu-*" \) -prune -o -print0 | cpio -0 -o -H newc --quiet | gzip -1 > /rig/initrd-$VARIANT.img )
chown $OWNER /rig/initrd-$VARIANT.img
'
ls -la "$RIGOUT/initrd-$VARIANT.img"
