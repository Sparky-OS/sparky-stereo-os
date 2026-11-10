# The boot splash at the person's depth

ORDER 481.
The boot splash follows the depth limits of the main screen's saved choice, the way every other surface that shows depth does: the person's limits, built on the display, never numbers of its own.
The rule (Daniel, 2026-11-05): "read the depth config by, and in this order of importance: 1 - User choice (but based on 2); 2 - Current display".
The splash had levels fixed at the desktop's default limits, so a person who lowered PoppedLimit still saw the default depth at boot.

## The chain, in four places

1. **Stereo KWin** keeps the limits in `kwinrc`, group `[StereoDepth]`, keys `SunkLimit` (default 10) and `PoppedLimit` (default 4), pixels of a view 1920 wide, one pair for the person, not one per output (`kwin.kcfg`).
   Per output KWin multiplies them by the display's factor: `stereo_policy_display_depth(kind, width_mm, height_mm, 100, 0, 0)` of libstereo-policy, divided by the reference 10 and 4, with the kind read from the output's mode flags (an anaglyph twin: anaglyph; any other virtual twin: headset; else a framed screen) and the size from the EDID (the first detailed timing whose image size has the mode's aspect within 0.1, else the basic size in centimetres; no size: factor 1).
2. **sparky-stereo-boot** (0.1.9) does the same sum for the main output when it exports the saved choice, and ends each stereo output of `plymouth.stereo=` with `:popped=PIXELS:sunk=PIXELS`.
   The root service reads the connecting account's own `kwinrc` (the peer's uid is checked, `O_NOFOLLOW`, owner checked), with `/etc/xdg/kwinrc` under it as KConfig does; the session's path unit also watches `~/.config/kwinrc`.
3. **Plymouth** (+stereo3d3, patch stereo3d-0003) parses `popped=` and `sunk=` per entry, and the script plugin has `Window.GetStereoPoppedLimit ()` and `Window.GetStereoSunkLimit ()`.
   An entry without them gets 4 and 10 (the display default of the reference monitor) and the renderer says so once per output; a value that is no limit is said and the default stands.
4. **The theme** (sparky-stereo-plymouth 20261109) places its levels inside the limits: the base is half the popped limit, the logo and the nearest electron the popped limit, the farthest electron 0.6 of the sunk limit from the base.
   At 4 and 10 these are the levels of the previous version (2, 4, 4 px), so nothing is raised.

No silent fallbacks: no limits saved is said in the journal and by `sparky-stereo-boot status` (the display's default); an unreadable value or file is kept by the problems engine (`splash-depth`), a libstereo-policy that cannot answer too (`splash-depth-display`).

## Proving it: the guest rig

`scripts/plymouth-rig/` builds a QEMU guest that runs Plymouth as the boot starts it and captures both eyes.

1. `mkrig.sh VARIANT THEME_DEB [PLYMOUTH_DEBS_DIR]`: an initramfs from a Debian container (plymouth, plymouth-label, udev, kmod, busybox from the edition's repository), the theme `.deb` unpacked over it, the Plymouth build under test unpacked over the repository's, the GPU driver's modules for the kernel you will boot.
   Variants: the red rig keeps the published Plymouth and the previous theme, the green one has the new builds.
2. `run-case.py OUTDIR TAG INITRD 'KERNEL ARGS'`: `qemu-system-x86_64` with KVM under your own user, `virtio-vga,xres=1920,yres=1080,stereo=on`, the host's kernel with `rdinit=/init`, no display; waits for the guest's `SPLASH-UP`, then reads the screen through QMP `screendump` twice and the console from a file. `plymouth.debug=stream:/run/ply.log` is on the kernel line, so the trace and the errors land in a file the init prints.
3. The kernel line comes from the tool that makes it: run the previous and the new sparky-stereo-boot in a fake root (`export-file FILE USER [KWINRC]`, `SPARKY_STEREO_ROOT`, the virtio screen's EDID fixture) with the person's `kwinrc`, and boot the guest with what it prints. A line typed by hand proves Plymouth only.
4. `measure.py PNG`: with `plymouth.stereo=Virtual-1:frame-packing:mode=1920x1080@60000` the capture is 1920x2205, the left eye at line 0 and the right eye at line 1125; the wordmark is the logo level and the swirl the base level; the right eye's region is matched against the left eye's, a thing popped by d px is d px to the right in the left eye, so the match is minus d.

Prediction, written out before the run: the splash's whole disparity is the limit times the display factor rounded to a pixel (logo = popped, base = half of it); the virtio screen is 487 x 274 mm, factor 0.9659.

| saved | line | logo | base |
| --- | --- | --- | --- |
| PoppedLimit 2, SunkLimit 5, previous boot and Plymouth (red) | no popped= | 4 px | 2 px |
| the same, new boot and Plymouth (green) | popped=1.93:sunk=4.83 | 2 px | 1 px |
| PoppedLimit 8, SunkLimit 20 | popped=7.73 | 8 px | 4 px |
| nothing | popped=3.86 | 4 px | 2 px |
| PoppedLimit 0 | popped=0 | 0 px | 0 px |

## Traps

- **Symptom:** the guest boots, plymouthd runs, the capture is the text console with the trace, no splash. **Cause:** Plymouth only uses a DRM device that udev has initialised ("found device ... card0", "it's not initialized"), and a bare initramfs has no udev. **Fix:** start `systemd-udevd`, `udevadm trigger --action=add` and `udevadm settle` before `plymouthd`. **Found by:** the guest's `plymouth.debug` trace on the screen.
- **Symptom:** the init mounts nothing ("mounting proc on /proc failed: No such file or directory"), then the kernel panics ("Attempted to kill init"). **Cause:** the cpio was written with `find -prune` on /proc, /sys, /dev, /run, so the directories are not in the image. **Fix:** `mkdir -p` them first in the init.
- **Symptom:** with `--debug` plymouthd's trace is on the screen, `--debug-file` and `--tty` change nothing, and Plymouth's own error lines are not in any file. **Cause:** plymouthd reads its debug target from the kernel line: `plymouth.debug=stream:FILE` sends the trace and the errors to FILE, the default is the console. **Fix:** put that on the kernel line.
- **Symptom:** the capture is a text mode screen of 1920x1080, not 1920x2205. **Cause:** the guest never set the 3D mode (udev, above), or the kernel line names a connector the guest does not have (the virtio screen is `Virtual-1`).
- **Symptom:** a build of Plymouth with `build-dh-lean.sh` stops in meson: "generate-version.sh failed". **Cause:** the script takes the version from the source directory's name (`plymouth-26.134.222`), and the builder unpacks it as `lean-source`. **Fix:** `REAL_DIR=plymouth-26.134.222`, and the authored tree must be in a folder of another name (`plymouth-src`): the same name as REAL_DIR makes the builder move its tree into the authored one.
- **Symptom:** the splash's depth is the default whatever the person saved. **Cause:** the boot package before 0.1.9 never read `kwinrc`, so `plymouth.stereo=` carried no limits; Plymouth +stereo3d2 and the theme before 20261109 ignore them if they were there. All three must be new.
- **A person's limit and the splash's rounding:** below a limit of about 1 px at 1920 the base rounds to 0 and the levels collapse into the screen; the splash never pops past the limit, which is the rule, so the test of "levels stay apart" only applies from a limit of 2 px at the eye's width.
