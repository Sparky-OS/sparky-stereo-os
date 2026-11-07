# Checking the eye flip on every 3D output mode, and reconciling an old lane's open points

Written by ORDER 116 (2026-11-07) against Stereo KWin 6.7.4-2+stereo3d46.

## Recipe: the flip on every mode of one output

1. A guest, never the host: the kernel of the VKMS bench (HDMI 3D modes listed), a small initramfs with BusyBox and the grab tools, the compositor's root exported from its proof-rig image and shared read only over 9p, QEMU with KVM, no network, no display.
2. One VKMS connector (configfs) that reads an EDID listing the HDMI 3D structures and one 1920x1080 timing at 120 Hz (frame sequential twins are offered from 100 Hz).
3. Start KWin on the DRM device (`KWIN_DRM_DEVICES=/dev/dri/card0`) once, stop it, and edit `~/.config/kwinoutputconfig.json`: `anaglyph` and `otherStereoFormats` to true on the output. Start it again: the twins are listed. There is no command line for the two toggles; the page or the protocol request `set_stereo_formats` sets them.
4. `kscreen-doctor -o` names a twin only as `(virtual-3D:N)`, N the value of libkscreen's `Mode::Stereo3D` (5 and 6 anaglyph modern and CRT, 7 to 12 rows, columns and checkerboard left then right first, 13 and 14 frame sequential, 1 and 2 side by side and top and bottom). Pick the mode id in the guest with Python from size, rate and those tags, and set the mode and the swap in one atomic command: `kscreen-doctor output.HDMI-A-1.mode.ID output.HDMI-A-1.swapEyes.enable`.
5. A client with an eye-tagged declared subsurface (left view red, right view green, still), a 2D reference frame first. Grab the scanned-out frame twice a second apart until both are equal.
6. Model every packing from the reference frame (L) and the same frame with the 3D area green (R): anaglyph with KWin's Dubois sets and gamma 2.2, rows, columns and checkerboard by line, column or both parity, half packings with each eye halved, side by side full and frame sequential as left half then right half, frame packing at lines 0 and 1125 of 2205. With the swap on the model is built from (R, L).
7. Each check carries its negative control: the other swap's model must match none of the pixels where the eyes differ. A right eye first twin with the swap off must equal the left eye first mode with the swap on, pixel for pixel.

Result on +stereo3d46 (VKMS, software GL): all 16 packings pass with the swap off and on, every pixel within the model (exact except the half side by side, off by 1 on 32 filtered pixels), the other swap's model failing on every pixel where the eyes differ; the right eye first twins of rows, columns and checkerboard are pixel-identical to the left eye first modes with the swap on; a 2D mode shows the left view, and the right view with the swap on. The scripts are in `tools/vkms-stereo-bench/eyeorder`.

## Traps

- Symptom: a correct frame-sequential right eye first frame fails a model that exchanges the halves. Cause: the eye order of frame sequential is in time, not in the frame: the packed frame is the same (left eye in the left half) and the scheduler starts on the right half. Fix: model the packed frame the same for both orders, and check the order by the plane's SRC_X over the vblanks. Found by: 12800 failing pixels, exactly the two 6400-pixel eye areas.
- Symptom: SRC_X changes only 17 to 25 times in 240 vblanks at 120 Hz and KWin logs "wrong-eye slots after 1644 missed refreshes". Cause: software GL in a 4-CPU guest renders about one frame in five refreshes; the alternation is there (both halves seen) but not strict. Fix: do not call a guest run a strict per-refresh proof; use the group-38 DisplayPort bench for pacing and the guest for content.
- Symptom: `kscreen-doctor -o` lists twins that cannot be told apart. Cause: only the layout number is printed. Fix: the table in the recipe, in the guest script.
- Symptom: `docker run -v /var/tmp/x:/repo` stops with "mkdir ...: file exists". Cause: the path is a symlink. Fix: `readlink -f` first.
- Symptom: `dpkg-source -x` of a staged KWin source fails on `kwin_6.7.4.orig.tar.xz.asc`. Cause: the signature must sit beside the orig. Fix: copy it too.
- Symptom: a build script's `$TARGETS` is unbound inside the container. Cause: the script was written with a quoted heredoc. Fix: pass it with `-e`.

## Reconciling an old lane's open points

For each point: search the published source's `debian/changelog` and `debian/patches` for the function, the later lanes' reports for the test, and the recorded design for the question. Say shipped (package and patch, plus the evidence), superseded (the design line quoted), or open. Frame sequential alternation was open in a report of 2026-10-10 and shipped by patches s36-0003, s39-0002 and s39-0004; the right eye first half packings were never an open point once the design said the eye order lives in the output's swap.
