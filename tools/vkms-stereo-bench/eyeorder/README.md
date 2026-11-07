# eyeorder: the output's eye flip on every 3D mode

Tested guest scripts and analyzer of [references/eye-order-matrix.md](../../../skills/vkms-stereo/references/eye-order-matrix.md).
Layout they expect, in one folder `$BENCH`: `bin/` (drm-grab, drm-flipwatch, fullscreen-2d and egl-stereo-subsurface from `src/`, built static or for the root), `edid/` (an EDID listing the HDMI 3D structures plus 1920x1080 at 120 Hz), `vm/bzImage-full` (the bench kernel), `initramfs/` (an unpacked BusyBox initramfs), `root/` (the compositor's root, exported from its proof-rig image), `mkcpio.py` (tools/).
`eyeorder.sh` goes to `$BENCH/guest/phases/`, `session.sh` and `steps.sh` to `$BENCH/guest/eyeorder/`, and `run.sh`, `mkinit.sh` and `analyze-eyeorder.py` to `$BENCH`; `run.sh NAME matrix` boots the guest (`QEMU_IMAGE` names an image with QEMU, `DOCKER_HOST` your Docker), `analyze-eyeorder.py runs/NAME` prints the checks.
