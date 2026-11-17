# The stereo boot splash rig

A QEMU guest that starts Plymouth as initramfs-tools does, on a laptop panel and a 3D television made with VKMS, and saves the frame each screen scans out.
Nothing runs on the machine you work on except QEMU; no display is opened.
What it proves and the traps are in [../../references/stereo-boot-splash.md](../../references/stereo-boot-splash.md).

```sh
# the EDIDs: the panel's is made here, the television's is the bench's
python3 make-panel-edid.py edid/panel-1366.bin
cp ../../../../tools/vkms-stereo-bench/edid/kdl-46hx855.bin edid/hx855.bin

# an image with Debian's Plymouth stack and a compiler, once (your Docker socket, your prefix)
docker run --name rig-base debian:testing@sha256:DIGEST sh -c 'apt-get update && apt-get -y --no-install-recommends install \
    plymouth plymouth-label udev kmod busybox cpio gzip xz-utils zstd gcc libc6-dev linux-libc-dev fonts-dejavu-core'
docker commit rig-base rig:1 && docker rm rig-base

# an initramfs per package set: the theme and the Plymouth .debs under test
export RIG_IMAGE=rig:1 RIGOUT=$PWD/out KVER=$(uname -r) PREFIX=rig
./mkrig.sh new sparky-stereo-plymouth_*.deb ./plymouth-debs/
python3 with-init.py out/initrd-new.img out/run-new.img     # the current init (and any PATH=FILE pairs) on top

# one boot: both screens, the television as the main screen in 1080p30 frame packing
./run-case.py runs both-tv out/run-new.img \
    'plymouth.stereo=HDMI-A-1:frame-packing:mode=1920x1080@30000:popped=4.72:sunk=11.8 rig.screens=both rig.drm=0'
# -> runs/both-tv-1-HDMI-A-1.ppm (1920x2205, the right eye from line 1125), runs/both-tv-1-eDP-1.ppm, and the log

# the batches (they expect out/run-SET.img)
./batch.sh runs new; ./batch-late.sh runs new; ./batch-more.sh runs
./compare.py runs/new-tv-tvline-1-HDMI-A-1.ppm runs/new-both-tvline-1-HDMI-A-1.ppm
./check-eye.py runs/new-tv-tvline-1-HDMI-A-1.ppm runs/new-both-tvline-1-eDP-1.ppm 'panel beside a main television'
./verdict.sh runs new old    # all twelve checks of one set against another set's single screens; exit 0 only when all pass
```

`--fw` boots OVMF with a 1024x768 firmware framebuffer and reads it through QMP just before the DRM driver comes (`rig.drm=12 rig.unbindfb=1`).
The guest needs a kernel with VKMS's configfs connector attributes (`type`, `edid`, `edid_enabled`, `status`), configfs and 9p as modules, and KVM.
