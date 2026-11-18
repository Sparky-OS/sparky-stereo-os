# What a boot theme declares and draws

ORDER 715.
A Plymouth theme is a program of the edition like any other: it hands the output the two eyes as separate complete pictures, side by side, left eye first, and the output (Plymouth's renderer) turns them into each screen's format.
A theme that packs, squeezes or stretches its own pair breaks that, and the picture on a real screen is a flat squeezed pair.
The chain that carries the person's depth limits to the theme is in [boot-splash-depth.md](boot-splash-depth.md); which screens show two eyes and which show one is in [the stereo boot splash](../../system-housekeeping/references/stereo-boot-splash.md).

## What a theme must declare and draw

1. **`Stereo=full-side-by-side`** in the `[Plymouth Theme]` group of its `.plymouth` file.
   The edition's Plymouth reads the key when it loads the theme (patch stereo3d-0001, `ply_boot_splash_load`) and then asks each display for a window that holds both eyes.
   A theme without the key is unchanged: a stereo output gives its one picture to both eyes, a screen that is not converted shows that picture once.
   So a theme that is plainly 2D (Debian's own, `sparkyos`, `sparky-lines`) needs nothing and must not declare the key.
2. **`Window.GetStereo ()`** is true when the window holds both eyes.
   Then each eye is the size of the main screen's eye (`Window.GetWidth () / 2`), the left eye in the left half, and every element is drawn once per eye from one animation clock.
   When it is false the window is one picture and the theme draws it once, with no parallax, exactly like its 2D look.
   Never `Image.Scale` an eye to half the window's width, never lay the pair out in one picture: that is what the output does.
3. **Depth from the person's limits.**
   `Window.GetStereoPoppedLimit ()` and `Window.GetStereoSunkLimit ()` are pixels of a view 1920 wide; the theme scales them by the eye's width over 1920, rounds to whole pixels, and places three levels inside them: the background on the screen, the base (the swirl and its orbits) at half the popped limit, the logo at the popped limit.
   A moving item (the electrons) stays between the popped limit in front and the sunk limit behind.
   No constant depth in a theme: an earlier splash that popped its logo 9 px against a limit of 4 had a constant.
   With both limits at 0 everything is on the screen.
   Right minus left, in pixels, of a thing at depth `d`: `-int(d * eye_width / 1920 + 0.5)` (crossed, in front of the screen, is negative).
4. **Lay out again at every display hotplug** (`Plymouth.SetDisplayHotplugFunction`), and keep the layout while `Window.GetWidth ()` is 0 (the gap between the firmware's framebuffer and the GPU's screens): with no display the limits are null and the script stops at every frame.
5. **Text lives on the screen plane in both eyes**: messages, the password prompt with its bullets, the fsck progress.
6. **The package depends on the Plymouth that gives these calls** (`plymouth (>= 26.134.222-1+stereo3d4)` for the full set): on a Plymouth without them the script stops with an error, which is the failure the person must be told about, not a theme that quietly draws something else.

The edition's reference is `sparky-stereo-lines` (sparky-stereo-plymouth): its generator builds the stereo script from the 2D one, and the same drawing code serves `sparkyos-stereo`, with the pictures of `sparkyos`.

## The symptom of a theme that packs its own pair

- **Symptom:** a screen shows two copies of the splash side by side, each squeezed to half the width, on every screen, in anaglyph or not; the picture is the same in both eyes (no red and cyan apart); the television in frame packing shows the same squeezed pair in both eyes.
  **Cause:** the theme's script draws its own half side by side pair (a squeeze constant, `Image.Scale (width / 2, height)`, a constant depth) and its `.plymouth` file has no `Stereo=` key, so Plymouth gives the window to it as one flat picture.
  **Found by:** `plymouth.debug=file:PATH` (or `stream:PATH`) on the kernel line.
  A stereo theme's log has `the theme draws both eyes side by side` (`set_head_stereo_input`); the theme that packs its own pair has no such line.
  The line `key file does not have entry for key 'Stereo'` is in the log of every theme without the key, a healthy 2D theme included, so it is a hint, never the proof: the proof is the missing `draws both eyes` line for a theme that is meant to be stereo, and the script's `grep -n "Scale\|SQUEEZE\|DEPTH"`.
  **Measured (ORDER 715, rig below):** the published `sparkyos-stereo` on a panel as the left eye and as the right eye, and as anaglyph: two wordmarks along the bottom, 0 px between the eyes, 11.2 % of the pixels different from one eye of the real stereo theme; the frame-packing frame: the same squeezed pair in both halves, 0 px apart.
- **Symptom:** the package's theme is not the artwork's current one (the older drawing is installed although the artwork repository's main branch has the new one).
  **Cause:** the recipe read the artwork from a work tree, whatever branch it was left on (`sparkyos-plymouth` 9~20261102 was built from a checkout of an older branch).
  **Fix:** a recipe that takes an outside source names its commit and the hash of the tree it reads, takes the files from the object store (`git archive COMMIT`), and stops on any other.
  **Found by:** unpacking the published package and comparing its theme folder with `git archive main plymouth` of the artwork repository (`diff -r`).

## Which theme a machine boots with

1. `/etc/plymouth/plymouthd.conf`, `Theme=` (a chosen theme: `plymouth-set-default-theme NAME`, KDE's Boot Splash page);
2. else the distribution's `/usr/share/plymouth/plymouthd.defaults` (the edition's names `sparky-stereo-lines`; Plymouth's own file is diverted to `plymouthd.defaults.debian`);
3. else the `default.plymouth` alternative.
`plymouth-set-default-theme` prints the one in `plymouthd.conf`, or the default when the file names none; the log of a real start says `System configured theme file is ...` (the first) or `Distribution default theme file is ...` (the second) and `Loading boot splash theme '...'` for the one it loaded.
The edition's packages treat a theme that a package set itself (sparky-blue, the one in `/var/lib/sparkyos-plymouth/theme`) as an automatic default and move it to the edition's; a theme a person chose stays.
On the upgrade of `sparkyos-plymouth`, measured in a container with the published tree as one apt source: a person's `Theme=sparkyos-stereo` (or `sparkyos`) stays, an automatic `sparkyos-stereo` goes to `sparky-stereo-lines` through sparky-stereo-plymouth's trigger, exactly as it does when the published package is reinstalled; do not change that rule inside a theme package.

## Proving a theme in a guest

The rig is the one of ORDER 639 (`scripts/stereo-splash-rig/`, [the stereo boot splash](../../system-housekeeping/references/stereo-boot-splash.md)): QEMU with KVM under your own user, no display, the published kernel and its `vkms` module, a VKMS device made through configfs with a laptop panel (`eDP-1`, 1366x768) and a television (`HDMI-A-1`, 1080p with HDMI 3D modes), Plymouth started as the initramfs starts it, the frame every CRTC scans out saved through a 9p share.
What ORDER 715 added:

1. `rig.theme=NAME` on the kernel line makes the init write `plymouthd.conf`, so one image holds every theme of a set and each case names its theme.
2. **The eyes as two full pictures:** `plymouth.stereo=eDP-1:left:...` and `...:right:...` give the left and the right eye of the same window as separate frames; `anaglyph-modern` gives both in one frame (red is the left eye, green and blue the right); `frame-packing` on the television gives both eyes in one frame, rows 0-1079 and 1125-2204.
3. **Measure on RGB arrays, never RGBA bounding boxes, and say the shift in pixels.**
   Sprites are placed at whole pixels, so a shift is an integer; match the wordmark (the bottom fifth) and the swirl (the upper two thirds) of one eye against the other over horizontal shifts of -24 to +24.
4. **Trap, symptom first:** every shift measured as 0 although the pictures plainly differ by a few pixels.
   **Cause:** the background grain is identical in both eyes and fills most of any region, so a mean over the whole region is lowest at shift 0.
   **Fix:** compare only the foreground (the luminance minus its horizontal grey opening, 31 px wide) where either eye holds a structure over 25 levels.
   **Found by:** printing the error for each shift of one crop: the minimum was at -3 with the right numbers, the whole-region mean at 0.
5. Predict each shift from the limits before reading the frames (the formula above) and write the checks as predictions: at the eye widths 1366 and 1920 the levels were -3 and -1 px at popped 4 (panel), -4 and -2 (television), -6 and -3 at popped 8, 0 at popped 0, and -2 and -1 at the 3.25 a laptop's boot wrote.
6. Controls that must stay green in every run: the edition's own `sparky-stereo-lines` on the same screens, and the 2D theme on every layout (a theme without the key gives one picture to both eyes).
7. A screen the splash does not convert shows the main screen's left eye, the eye's own edge continued where the screen is larger; the frame-buffer renderer too: its pictures are read from `/dev/fb0` at the visible mode and from QEMU's `screendump` of the firmware's framebuffer.

## Reading the panel of a real machine

The main session's measured method (2026-11-18, on a laptop that took the new splash packages; not run in this lane): the picture a screen shows during a start is what its CRTC scans out, read without setting a mode and without taking the DRM master.

1. As root, with libdrm: `drmModeGetCrtc` for the CRTC of the connector, `drmModeGetFB` (or `DRM_IOCTL_MODE_GETFB2`) for the framebuffer it scans out, then `DRM_IOCTL_MODE_MAP_DUMB` on its handle and a **read-only** `mmap` of the returned offset.
   `DRM_IOCTL_MODE_MAP_DUMB` is documented for dumb buffers (`include/uapi/drm/drm_mode.h`: "set up for mmap of a dumb scanout buffer"; a dumb buffer is linear single-plane RGB), which is what Plymouth's DRM renderer and the firmware framebuffer use.
   Reading the handle of a framebuffer another process owns needs `CAP_SYS_ADMIN`.
   The rig's `crtc-grab.c` does the same in the guest and is the run-through of the idea.
2. Run it at fixed seconds from a **one-time systemd unit** (`DefaultDependencies=no`, `After=systemd-remount-fs.service`, `WantedBy=sysinit.target`), so the reads are early and as many as needed (seven captures over 23 seconds, all equal, were enough to call a splash stable).
3. Put `plymouth.debug=file:PATH` on the kernel line to get the splash's own log beside the pictures.
4. **Trap:** `ffmpeg -f kmsgrab` reads only the pixel formats it knows and refused KWin's `AR30` (30-bit) framebuffer; the libdrm reader reads the bytes and the format code and converts them itself.
5. **Trap:** a framebuffer with a format modifier (tiled, compressed) is not linear: the mapped bytes are not a picture.
   The reader reports the format and modifier and stops there.
   KWin's own scanout buffers can be of that kind; Plymouth's dumb buffers are not.

## Packaging a theme (the successor of a published package)

- Build it as `sparky-stereo-plymouth` is built: the package sealed by `lean.standalone`, its source package rebuilt (`repo/rebuild-script-source.py`), `check-debs` writing the complete build record.
  **Trap:** the rebuild stops with `dpkg-checkbuilddeps: error: unmet build dependencies: build-essential:native`.
  **Cause:** the build image has `dpkg-dev` but not `build-essential`.
  **Fix:** `build-essential` (and `debhelper`, `fakeroot`) in the image.
- Compare the successor with the published package file by file (`dpkg-deb -x` both, hash and mode of every file) and explain each difference; the 2D theme's files must be identical.
- Prove the upgrade with apt's own words: a container with the published tree and a flat folder of the successor and the Plymouth it needs as two `file:` sources (`Trusted: yes`), the published set installed first, then `apt-get -s install` (the `Inst` lines and `0 to remove`), then the real one, and the configured theme read before and after.
  **Trap:** `E: Unable to satisfy dependencies` for `plymouth-themes` at the first install.
  **Cause:** `plymouth-themes` needs `fonts-cantarell`, which the edition's tree does not carry; the container needs Debian's source (https only) too, with the edition's Plymouth kept above Debian's by a pin.
  **Trap:** the plan shows the older `plymouth-themes` held back with a conflict.
  **Cause:** the new folder lacked `plymouth-themes` of the new Plymouth, and every Plymouth binary is versioned with `(= version)`; put the whole set in the folder.

## Credits

The theme's script is `lines.script` of the Lines Plymouth theme of Debian 8 "Jessie" (artwork by Juliette Taka Belin, scripting with Aurélien Couderc; Alberto Milone and Canonical for the script), made from the script plugin example of Charlie Brej, edited by Daniel Ramos for Sparky; Plymouth is the work of Ray Strode and its contributors; ORDER 639's rig is the method this proof follows.
