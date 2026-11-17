# The stereo boot splash

ORDER 639.
The boot splash (Plymouth) shows the main screen as the person set it in the display settings, from the start to the login screen and again at a restart or a shutdown.
Daniel's rule (2026-11-17): "if it's saved mode is 2D, then it should display only one eye".
A screen the splash does not turn into its 3D format shows ONE eye, never the two pictures side by side.
The depth limits of the splash are in [boot-splash-depth.md](../../stereo-window-3d-area/references/boot-splash-depth.md).

## How the choice reaches Plymouth

1. **Stereo KWin** saves each output's mode in `~/.config/kwinoutputconfig.json`; the mode's flags carry its 3D layout, and the setup's priorities say which screen is the main one.
2. **sparky-stereo-boot** reads it whenever it changes (the session's path unit, the root socket) and writes GRUB's environment block: `sparky_stereo_boot=plymouth.stereo=CONNECTOR:LAYOUT:mode=WxH@mHz[:preferred][:swap]:popped=P:sunk=S [video=...]`, the main screen's entry first (a stereo pair writes its two panels).
   It also writes `/var/lib/sparky-stereo-boot/main-output.json` with the same `kernelArguments`.
   `video=CONNECTOR:WxH@Hz` is added when the saved base mode is not the screen's preferred one, so the console keeps it.
3. **GRUB** puts `${sparky_stereo_boot}` on the kernel line; Plymouth reads `plymouth.stereo=` from `/proc/cmdline`.
4. **At a restart or a shutdown** Plymouth's units (`plymouth-reboot`, `-poweroff`, `-halt`, `-kexec`) would read `/proc/cmdline` too, the choice the boot STARTED with.
   sparky-stereo-boot 0.1.12 starts plymouthd there through `sparky-stereo-boot plymouth-shutdown MODE`, which hands it the `plymouth.stereo=` of `main-output.json` with plymouthd's own `--kernel-command-line=`, and says in the journal when it differs from the start's.

## Who draws what

| Renderer | When | Two eyes |
| --- | --- | --- |
| `drm.so` | a DRM device udev has initialised (amdgpu, i915, nouveau, NVIDIA's DRM) | yes: frame packing, side by side full and half, top and bottom (the 3D mode itself), anaglyph, rows, columns, checkerboard, sequential, pairs on 2D modes |
| `frame-buffer.so` | `/dev/fbN` with no DRM device behind it, only after Plymouth's `DeviceTimeout` (8 s) | no: shows the left eye |
| simpledrm | skipped on a stereo boot (the edition's kernel has none: `CONFIG_DRM_SIMPLEDRM` unset, efifb is used) | no |
| text, details | no `splash` on the kernel line, or a serial console | no picture |

- A screen named in `plymouth.stereo=` with a layout it can show is converted; every other screen of a stereo boot shows the left eye and Plymouth says so once in its log (`HDMI-A-1 is not named in plymouth.stereo=, it shows the left eye`, `/dev/fb0 cannot show the two eyes of the stereo boot splash, it shows the left eye`).
- **The mode** of a named screen is the first one in the screen's own list with the saved size, the saved rate (computed as KWin computes it: `(clock * 10^6 / htotal + vtotal / 2) / vtotal`, doubled when interlaced) and the saved 3D structure; that is the mode KWin keeps, so the boot and the desktop set the same timing.
  A saved mode the screen does not list keeps the screen's own mode and the left eye, said once; no other 3D mode is chosen in its place (KWin never picks a 3D mode by itself either).
  The list is the kernel's, built from the EDID: HDMI 1.4a makes a few 3D formats mandatory for a sink with `3D_present` (1080p24 and 720p50/60 frame packing, 1080i side by side half, 720p and 1080p24 top and bottom); anything else, such as 1080p30 frame packing, is there only when the EDID lists it (`3D_Structure_ALL`/`3D_MASK` or a `3D_Structure_X` entry).
- **The picture** (Plymouth +stereo3d4): the script plugin keeps one window for every screen. On a stereo boot with a stereo theme (`Stereo=full-side-by-side`) it holds both eyes, each the size of the main screen's eye; a screen that shows both eyes takes each half from its own eye of the window, a screen that shows one eye the middle of the left eye; a screen larger than the eye continues the eye's own edge beyond it (each pixel the nearest pixel of the eye, `ply_pixel_buffer_fill_with_edges_of_area`), so it shows no frame of another colour and never a part of the other eye, and a smaller one shows the eye's middle. The eye is never scaled.
  The theme lays itself out again at each display hotplug (`Plymouth.SetDisplayHotplugFunction`), so a screen that comes later (the GPU's driver after the firmware's framebuffer, a television plugged in) never keeps an older screen's layout.

## The order of a start (initramfs-tools)

`init-top/udev` runs `udevadm trigger` and `udevadm settle`; Plymouth's `init-premount/plymouth` starts plymouthd and `plymouth --show-splash` after that.
So the splash is not drawn while the GPU's modules are still being probed: what the screen shows then is GRUB's last picture kept with `gfxpayload=keep`, or the firmware's.
When the DRM driver comes after Plymouth's 8 s timeout, the splash starts on the firmware's framebuffer (the frame-buffer renderer) and the DRM screens are added later: this is the order the theme's re-layout exists for.
A boot image of 200 MB or more that is mostly "uncompressed" is initramfs-tools' own design since 0.146 (Benjamin Drung, 81fd41f): `.ko.xz` modules and `.zst` firmware go into a plain cpio segment ahead of the compressed one; it is not a fault of the splash.

## Proving it without a 3D television: the rig

`scripts/stereo-splash-rig/` boots QEMU (KVM, no display) with an initramfs holding Plymouth as the boot starts it, a VKMS device made through configfs with a laptop panel (`eDP-1`, 1366x768, made by `make-panel-edid.py`) and a television (`HDMI-A-1`, the Sony KDL-46HX855's EDID from `tools/vkms-stereo-bench/edid/kdl-46hx855.bin`), and saves the frame every CRTC scans out to a 9p share (`crtc-grab.c`, adapted from the bench's `drm-grab`).
See its README for the commands.

1. Build the image once per package set: `mkrig.sh SET THEME.deb DEBS_DIR` (the Plymouth, libplymouth5 and plymouth-label `.deb` files under test unpacked over Debian's).
2. Change only the guest's init or a few files without a rebuild: `with-init.py BASE.img OUT.img [PATH=FILE ...]` appends a cpio.
3. `run-case.py OUT TAG IMAGE 'KERNEL ARGS' [--fw]`: `rig.screens=both|panel|tv`, `rig.drm=N` (the DRM driver N seconds late; with `--fw` OVMF gives the guest a 1024x768 firmware framebuffer, `rig.unbindfb=1` takes it away when the driver comes, as amdgpu does), `rig.tvlate=N` (the television plugged in N seconds after the splash), `rig.mode=reboot`.
4. `compare.py ALONE.ppm FRAME.ppm`: a main screen must show what it shows when it is the only screen; `check-eye.py EYE.ppm FRAME.ppm`: a screen that is not converted must show the main screen's left eye at its middle, and around it the eye's own edge continued, pixel for pixel (the left eye of a frame-packing frame is rows 0 to 1079). `fb0-png.py` turns the guest's `/dev/fb0` into a picture, so a frame-buffer renderer's screen is measured the same way.
5. `verdict.sh RUNS SET REF` runs all twelve checks of a set and exits 0 only when every one passes (ORDER 639: 1 of 12, exit 1, on the published and the October sets; 12 of 12, exit 0, on the new packages).
6. The batches: `batch.sh` (each screen alone, then both, for the panel-main and the television-main line), `batch-late.sh` (the firmware framebuffer first, the television later), `batch-more.sh` (the 2D control, a mode the screen does not list, the restart splash), `batch-edge.sh` (those two, the panel's eye alone and a run past the device timeout), `batch-fbkept.sh` (the firmware framebuffer kept beside the GPU's screens, `rig.unbindfb=0`, at 1920x1080 and 1024x768: the frame-buffer renderer on a screen larger and smaller than the eye; `run-case.py --fw` saves it again as `TAG-fbend.png` when the frames are read).

A screen that shows one eye and is larger than the eye continues the eye's edge (ORDER 639's review): the teal frame of the first +stereo3d4 differed from the eye's edge by 143 levels on the television beside the panel, in the late-television case, past the device timeout and on a kept 1920x1080 firmware framebuffer; the final build differs by 0 in each, the smaller framebuffer still shows the eye's middle, and the 2D control is unchanged.
During the frame-buffer phase itself the framebuffer is the only display, so the eye is its size and there is no border.

Measured on ORDER 639 (published Plymouth +stereo3d3 with theme 20261109, the October +stereo3d1 with 20261016, and +stereo3d4 with 20261117): with both screens connected the panel's anaglyph differed from the panel alone in 19.5 % of its pixels on both older sets and in 0.0 % on the new one; every screen that was not converted showed one eye only on the new set; a 2D boot differed between the published and the new build by no more than two runs of the same build differ (the electrons move).

## Traps

- **Symptom:** a television beside the main panel shows the panel's picture small, in a frame of another colour (the theme's background gradient). **Cause:** a screen larger than the window's eye was filled with the window's background beyond the eye, as upstream does for one-picture themes. **Fix:** on a stereo window the eye's edge is continued beyond it (Plymouth +stereo3d4). **Found by:** review of the picture, then `check-eye.py` comparing every border pixel with the nearest pixel of the eye in the same capture.

- **Symptom:** a laptop panel in anaglyph shows two copies of the splash side by side, red and cyan, about 554 px apart, only when a television is connected; or a television in 2D shows the left picture with part of the right one beside it. **Cause:** before +stereo3d4 the script plugin centred each screen as one block in a window as wide as the widest screen, so a narrower screen's two halves were not the window's two eyes; and the theme laid itself out once. **Fix:** Plymouth +stereo3d4 and theme 20261117. **Found by:** the rig with two screens of different widths against each screen alone; the code in `script-lib-sprite.c` (`update_displays`, `draw_area`).
- **Symptom:** the television falls to 2D before a restart. **Cause:** the shutdown units read the start's `plymouth.stereo=`, and Plymouth gives a screen it is not told about its preferred mode. **Fix:** sparky-stereo-boot 0.1.12 (`plymouth-shutdown`). **Found by:** the rig in `--mode=reboot` with the start's and the saved line; `get_output_info` takes `get_preferred_mode` first.
- **Symptom:** in the guest plymouthd exits at once, its log says "could not create pseudo-terminal". **Cause:** `--attach-to-session` needs `/dev/pts`. **Fix:** mount devpts in the init, as the real initramfs does.
- **Symptom:** the guest shows Plymouth's text splash. **Cause:** no `splash` on the kernel line, or a console= Plymouth counts as serial: in its shutdown modes it takes tty63 for itself, so `console=tty1` is "another console". **Fix:** `quiet splash`; `console=tty1` for a boot, no `console=` at all for a restart (the kernel's default, as on a laptop).
- **Symptom:** a file appended to the guest's initramfs is not there. **Cause:** the kernel reads a following archive only at an aligned offset, and a gzip image ends anywhere. **Fix:** pad to 512 bytes before it (`with-init.py` does).
- **Symptom:** after 8 s the guest's log shows a frame-buffer renderer on `/dev/fb0` although VKMS is the only device. **Cause:** a configfs VKMS device has no `ID_PATH`, so Plymouth does not tie its fbdev emulation to the DRM device. On real hardware (amdgpu's fbdev has a PCI path) this does not happen; count it in cases that run past the timeout.
- **Symptom:** `/dev/fb0` read in the guest shows the splash in its top-left corner with black beyond it. **Cause:** DRM's fbdev emulation sizes its visible mode to the smallest screen and its buffer to the largest (kernel `include/drm/drm_fb_helper.h`, struct drm_fb_helper_surface_size: "the fbdev width/height is sized to the minimum width/height of all the displays"), and Plymouth's frame-buffer renderer draws the visible size (its log: `initializing 1366x768 head`). **Fix:** read the visible mode (`/sys/class/graphics/fb0/modes`), as `fb0-png.py` does. **Found by:** Plymouth's log against the dump's size.
- **Symptom:** Plymouth's log says `Could not initialize heads` right after the VKMS device appears, every connector "Using controller 0", and the screens stay off. **Cause:** a configfs VKMS device is announced before its connectors have controllers; Plymouth queries once and waits for another event, which usually comes within milliseconds and sometimes not at all. **Fix:** run the case again; it is the rig's, not the splash's (the stage shows the same first failure). **Found by:** comparing the log of a failed run with a passing one at the device's arrival.
- **Symptom:** the script stops at every frame with `Cannot negate non number objects` while no screen is lit (between the firmware framebuffer's removal and the GPU's screens). **Cause:** a theme that lays itself out at every hotplug (`Plymouth.SetDisplayHotplugFunction`) runs once more when the last display goes; with no display `Window.GetStereoPoppedLimit ()` is null. **Fix:** keep the layout while `Window.GetWidth ()` is 0 (sparky-stereo-plymouth 20261117). **Found by:** counting `Execution error` in every run's log: the published theme has none.
- **Symptom:** a QMP screendump of the firmware framebuffer is sheared. **Cause:** a 1366-wide mode on QEMU's VGA. **Fix:** 1024x768, the firmware mode of a two-GPU AMD laptop with a television connected.
- **Symptom:** a Plymouth build from a `git archive` copy fails in meson ("text.plymouth does not exist", or "generate-version.sh failed"). **Cause:** `git archive` leaves out files upstream's `.gitignore` lists, and without git the version comes from the folder's name. **Fix:** copy with `tar --exclude=.git` into a folder named `plymouth-26.134.222`.
- **Symptom:** `lc1: build record NOT complete, unrecorded: buildinfo` for a hand-assembled package (the theme, sparky-stereo-boot). **Cause:** `lean.standalone` assembles the `.deb` directly. **Fix:** `repo/rebuild-script-source.py` between `lean.standalone` and `check-debs`, in a build image with build-essential and debhelper.
