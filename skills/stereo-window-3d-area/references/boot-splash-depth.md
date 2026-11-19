# The boot splash at the person's depth

ORDER 481.
The boot splash follows the depth limits of the main screen's saved choice, the way every other surface that shows depth does: the person's limits, built on the display, never numbers of its own.
What a theme itself must declare and draw (`Stereo=`, `Window.GetStereo ()`, no constants): [boot-splash-theme-contract.md](boot-splash-theme-contract.md) (ORDER 715).
Which screens show two eyes, which show one, the restart splash and the rig with a panel beside a television: [the stereo boot splash](../../system-housekeeping/references/stereo-boot-splash.md) (ORDER 639).
The rule (Daniel, 2026-11-05): "read the depth config by, and in this order of importance: 1 - User choice (but based on 2); 2 - Current display".
The splash had levels fixed at the desktop's default limits, so a person who lowered PoppedLimit still saw the default depth at boot.

## The chain, in four places

1. **Stereo KWin** keeps the limits in `kwinrc`, group `[StereoDepth]`, keys `SunkLimit` (default 10) and `PoppedLimit` (default 4), pixels of a view 1920 wide, one pair for the person, not one per output (`kwin.kcfg`).
   Per output KWin multiplies them by the display's factor: `stereo_policy_display_depth(kind, width_mm, height_mm, 100, 0, 0)` of libstereo-policy, divided by the reference 10 and 4, with the kind read from the output's mode flags (an anaglyph twin: anaglyph; any other virtual twin: headset; else a framed screen) and the size from the EDID (the first detailed timing whose image size has the mode's aspect within 0.1, else the basic size in centimetres; no size: factor 1).
2. **sparky-stereo-boot** (0.1.9) does the same sum for the main output when it exports the saved choice, and ends each stereo output of `plymouth.stereo=` with `:popped=PIXELS:sunk=PIXELS`.
   The root service reads the connecting account's own `kwinrc` (the peer's uid is checked, `O_NOFOLLOW`, owner checked), with `/etc/xdg/kwinrc` under it as KConfig does; the session's path unit also watches `~/.config/kwinrc`.
3. **Plymouth** (+stereo3d3, patch stereo3d-0003) parses `popped=` and `sunk=` per entry, and the script plugin has `Window.GetStereoPoppedLimit ()` and `Window.GetStereoSunkLimit ()`.
   An entry without them gets 4 and 10 (the display default of the reference monitor) and the renderer says so once per output; a value that is no limit is said and the default stands.
4. **The theme** (sparky-stereo-plymouth 20261119) places its levels from the limits: the base is one step, 1.135 times the popped limit (4.54 px at 1920 and the default limits), the logo two steps (9.08 px), the nearest electron the base plus the popped limit, the farthest electron 0.6 of the sunk limit behind the base. These are the levels before ORDER 472; 20261108 to 20261117 had cut them to half the popped limit and the popped limit.
   At 4 and 10 these are the levels of the previous version (2, 4, 4 px), so nothing is raised.

No silent fallbacks: no limits saved is said in the journal and by `sparky-stereo-boot status` (the display's default); an unreadable value or file is kept by the problems engine (`splash-depth`), a libstereo-policy that cannot answer too (`splash-depth-display`).

## Proving it: the guest rig

`scripts/plymouth-rig/` builds a QEMU guest that runs Plymouth as the boot starts it and captures both eyes.

1. `mkrig.sh VARIANT THEME_DEB [PLYMOUTH_DEBS_DIR]`: an initramfs from a Debian container (plymouth, plymouth-label, udev, kmod, busybox from the edition's repository), the theme `.deb` unpacked over it, the Plymouth build under test unpacked over the repository's, the GPU driver's modules for the kernel you will boot.
   Variants: the red rig keeps the published Plymouth and the previous theme, the green one has the new builds.
2. `run-case.py OUTDIR TAG INITRD 'KERNEL ARGS'`: `qemu-system-x86_64` with KVM under your own user, `virtio-vga,xres=1920,yres=1080,stereo=on`, the host's kernel with `rdinit=/init`, no display; waits for the guest's `SPLASH-UP`, then reads the screen through QMP `screendump` twice and the console from a file. `plymouth.debug=stream:/run/ply.log` is on the kernel line, so the trace and the errors land in a file the init prints.
3. The kernel line comes from the tool that makes it: run the previous and the new sparky-stereo-boot in a fake root (`export-file FILE USER [KWINRC]`, `SPARKY_STEREO_ROOT`, the virtio screen's EDID fixture) with the person's `kwinrc`, and boot the guest with what it prints. A line typed by hand proves Plymouth only.
4. `measure.py PNG`: with `plymouth.stereo=Virtual-1:frame-packing:mode=1920x1080@60000` the capture is 1920x2205, the left eye at line 0 and the right eye at line 1125; the wordmark is the logo level and the swirl the base level; the right eye's region is matched against the left eye's, a thing popped by d px is d px to the right in the left eye, so the match is minus d.

Prediction, written out before the run (20261119, not run in ORDER 750): the splash's whole disparity is the level times the display factor rounded to a pixel (logo = 2 * 1.135 * popped, base = 1.135 * popped); the virtio screen is 487 x 274 mm, factor 0.9659.

| saved | line | logo | base |
| --- | --- | --- | --- |
| PoppedLimit 2, SunkLimit 5, previous boot and Plymouth (red) | no popped= | 9 px | 5 px |
| the same, new boot and Plymouth (green) | popped=1.93:sunk=4.83 | 4 px | 2 px |
| PoppedLimit 8, SunkLimit 20 | popped=7.73 | 18 px | 9 px |
| nothing | popped=3.86 | 9 px | 4 px |
| PoppedLimit 0 | popped=0 | 0 px | 0 px |

## Traps

- **Symptom:** the guest boots, plymouthd runs, the capture is the text console with the trace, no splash. **Cause:** Plymouth only uses a DRM device that udev has initialised ("found device ... card0", "it's not initialized"), and a bare initramfs has no udev. **Fix:** start `systemd-udevd`, `udevadm trigger --action=add` and `udevadm settle` before `plymouthd`. **Found by:** the guest's `plymouth.debug` trace on the screen.
- **Symptom:** the init mounts nothing ("mounting proc on /proc failed: No such file or directory"), then the kernel panics ("Attempted to kill init"). **Cause:** the cpio was written with `find -prune` on /proc, /sys, /dev, /run, so the directories are not in the image. **Fix:** `mkdir -p` them first in the init.
- **Symptom:** with `--debug` plymouthd's trace is on the screen, `--debug-file` and `--tty` change nothing, and Plymouth's own error lines are not in any file. **Cause:** plymouthd reads its debug target from the kernel line: `plymouth.debug=stream:FILE` sends the trace and the errors to FILE, the default is the console. **Fix:** put that on the kernel line.
- **Symptom:** the capture is a text mode screen of 1920x1080, not 1920x2205. **Cause:** the guest never set the 3D mode (udev, above), or the kernel line names a connector the guest does not have (the virtio screen is `Virtual-1`).
- **Symptom:** a build of Plymouth with `build-dh-lean.sh` stops in meson: "generate-version.sh failed". **Cause:** the script takes the version from the source directory's name (`plymouth-26.134.222`), and the builder unpacks it as `lean-source`. **Fix:** `REAL_DIR=plymouth-26.134.222`, and the authored tree must be in a folder of another name (`plymouth-src`): the same name as REAL_DIR makes the builder move its tree into the authored one.
- **Symptom:** the splash's depth is the default whatever the person saved. **Cause:** the boot package before 0.1.9 never read `kwinrc`, so `plymouth.stereo=` carried no limits; Plymouth +stereo3d2 and the theme before 20261109 ignore them if they were there. All three must be new.
- **A person's limit and the splash's rounding:** below a limit of about 1 px at 1920 the base rounds to 0 and the levels collapse into the screen; the splash's levels are the theme's own (step 1.135 times the popped limit, logo twice that, 4.54 and 9.08 px at 1920 and the default limits, as before ORDER 472), so the test of "levels stay apart" only applies from a limit of 2 px at the eye's width. ORDER 472 had cut them to 2 and 4 px because the picture "looked huge" on a notebook; Daniel explained on 2026-11-18 that it was an upscaled anaglyph before any compositor, so the cut rested on a misreading and ORDER 750 restored the levels.
- **Symptom:** the build repository's `tests/supply-chain/test-wiring.sh` fails with "dch without --date" or "sparky_provenance_init is not before docker run". **Cause:** a recipe that writes a changelog must be dated by its commit, not the clock, and a recipe whose gate runs in a container must hand it the host's facts. **Fix:** require `SOURCE_DATE_EPOCH` (`reproducible.py epoch RECIPE_DIR`), `dch --date "$SOURCE_DATE_RFC2822"` on every call, `normalize-tree` last; source `build-provenance.sh`, call `sparky_provenance_init`, and run `lean.standalone` and `lean.release check-debs` in one `docker run` with `"${SPARKY_PROV_ARGS[@]}"`. Two runs of the source step then give the same .dsc and .debian.tar.xz bytes.
