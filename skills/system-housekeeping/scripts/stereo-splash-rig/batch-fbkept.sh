#!/bin/bash
# batch-fbkept.sh OUTDIR SET...: the frame-buffer renderer beside the GPU's screens. The firmware's framebuffer
# (efifb under OVMF) is kept when the VKMS device comes (rig.unbindfb=0), as on a machine whose arriving driver does not
# take it away, so it stays a frame-buffer display while the panel is the main screen: 1920x1080 is larger than the
# panel's eye, 1024x768 smaller. Its picture is QEMU's screendump when the frames are read (TAG-fbend.png); also the
# fw-tvline case again (the late DRM device, no kept framebuffer).
set -uo pipefail
here=$(dirname "$(readlink -f "$0")")
out=$1; shift
: "${KVER:?}" "${RIGOUT:?}"
PANEL='plymouth.stereo=eDP-1:anaglyph-modern:mode=1366x768@60005:popped=3.25:sunk=8.13'
TV='plymouth.stereo=HDMI-A-1:frame-packing:mode=1920x1080@30000:popped=4.72:sunk=11.8'
for set in "$@"; do
	for size in 1920x1080 1024x768; do
		tag=$set-fbkept$size-panelline
		timeout 300 python3 -I "$here/run-case.py" "$out" "$tag" "$RIGOUT/run-$set.img" \
			"$PANEL rig.screens=both rig.drm=12 rig.unbindfb=0" --fw=$size | grep -aE '^(HDMI|eDP)|left eye' | sed "s/^/$tag: /"
	done
	tag=$set-fw-tvline
	timeout 300 python3 -I "$here/run-case.py" "$out" "$tag" "$RIGOUT/run-$set.img" "$TV rig.screens=both rig.drm=12 rig.unbindfb=1" --fw \
		| grep -aE '^(HDMI|eDP)|left eye' | sed "s/^/$tag: /"
done
