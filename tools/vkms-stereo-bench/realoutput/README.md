# realoutput: the frame a real output gets, beside every buffer the program committed

Tested guest scripts, analysers and the two-layer Vulkan client of [real-output-readback.md](../../../skills/stereo-proof-rig/references/real-output-readback.md).

Layout they expect, in one folder `$BENCH`: `bin/` (`drm-grab` and `drm-planelog` from `../src`, built static), `edid/` (an EDID listing the HDMI 3D structures), `vm/bzImage-full` (the bench kernel), `initramfs/` (an unpacked BusyBox initramfs), `root/` (the compositor's root, exported from its proof-rig image, with `kscreen-doctor`, Python 3 and the program under test), `mkcpio.py` (`../tools`).

`BENCH=... EXTRA=folder ./run.sh NAME cases/vk2layer.sh` boots one guest with KVM, no network and no display; `EXTRA` holds what the case needs in the guest's `/mnt` (`vk2layer`, built for the root, and `wlrec.so` from `skills/stereo-proof-rig/scripts/wlrec.c`).
`cases/program.sh` runs any program of the root (`PROGRAM`, `APPENV`, `APPWAIT`, set in a case file that sources it).
Afterwards, on the host: `python3 halves.py $BENCH/runs/NAME/app.ppm` for the output's frame and `python3 halves_raw.py $BENCH/runs/NAME/wl` for every committed buffer in order.
A side by side (full) frame whose halves differ in 0 pixels under a stereo scene is one eye twice; the last committed buffer says whether the program or the compositor made it.
