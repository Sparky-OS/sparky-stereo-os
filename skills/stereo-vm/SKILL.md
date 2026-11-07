---
metadata:
  requires-packages: qemu-system-x86
name: stereo-vm
description: >-
  Virtual machines in stereo: QEMU's own window, virt-viewer, virt-manager and Karton over SPICE, the edition's
  spice-gtk, logical input coordinates in a 3D mode, resize and mode transitions, the controls that must fail, isolated
  guests and negative controls. Load it when a guest's 3D desktop is squeezed or stretched in the viewer, the pointer
  lands off by half, a resize leaves the window wrong, a libvirt monitor socket path is too long, or Debian's spice-gtk
  wins over ours.
---

# A virtual machine in stereo

## Working recipe

1. Record host/guest/viewer versions and the guest logical display size; distinguish it from the packed stereo frame.
2. Exercise eye identity and pointer mapping before/after resize, mode changes and reconnect, then run the unmodified viewer control.
3. Return guest evdev readings and synchronized captures. A correct picture does not prove correct pointer coordinates.

**Check freshness first.**
Written on 2026-10-10.
The guide [A virtual machine with a 3D display](../../docs/stereo-vm.md) says how the VM works; this skill says how to prove a change to it.

## The design every viewer follows

- The viewer's ordinary window is the guest's display at its own size (one view) and takes the input.
- Both views go side by side to a surface of their own on top of it, each at the resolution the guest scans it out at (a top-and-bottom 1080p frame as one 3840x540 buffer), declared once as full side by side; the viewport gives the size a view is shown at, and Stereo KWin resizes once.
- The pointer: the viewer sends its position in the guest's display. With a stereo layout set, the server tells the tablet the display is one view, so the host's tablet mapping stays as upstream has it. Nothing remaps the pointer in QEMU.

## The checks

1. **Colour test:** both views in the right eye, the same frame number in both, one declaration, the window's 2D part identical in both eyes.
1. **Resolution:** the buffer the viewer hands over holds each view sample for sample, for every 3D structure (the [proof rig's copy check](../stereo-proof-rig/SKILL.md#unpacking-is-a-copy)); a view stretched to the size it is shown at is a failure.
2. **Pointer:** the host moves the pointer to four fractions of the view in 2D and in every 3D mode; the guest's own kernel prints what its tablet gets (read the evdev node before any compositor maps it); each report must be the fraction of the range, within 4 %.
3. **Resize:** the same after the window is made smaller and larger.
4. **A mode change while the pointer moves:** the pointer circles around the view's centre while the guest changes mode; every report must stay at the centre of the range. A report at the instant of the switch can be off (the viewer's layout, the server's tablet size and the surface arrive on their own, as for a plain 2D resolution change): count those, allow at most two per transition in the first half second, and none later.
5. **Controls that must fail:** a stock client (Debian's spice-gtk, stock Karton), a QEMU that sends no layout. Say which modes the control fails in: a stock widget over this server points right in the modes whose left view sits at the frame's origin at full size.

## Traps that fooled us

- **`fake-click move`, one process per move, gives a GTK client only pointer enters:** the device comes and goes, and QEMU's GTK display and virt-manager hear no motion. Keep one `fake-click follow` session and write positions to it.
- **A libvirt domain's monitor socket path is limited to 107 bytes:** a long run name fails the start with "UNIX socket path too long"; keep run names short.
- **A repository with the edition's spice-gtk wins over Debian's:** a "stock client" image must pin Debian's version (`=0.42-4+b1`), for the library, the introspection package and virt-manager's.
- **virt-viewer opens at the size of the whole frame** (twice the view in a 3D mode): give the host's virtual output room, and a test that holds the pointer still will find it outside the window after a mode change.
- **WAYLAND_DEBUG prints `wl_pointer#12.enter`, not `@12`:** filters written for the old format match nothing.
- **A resize test must put the window back:** the next steps are measured at its size.
- **`pgrep -f` or `pkill -f` on a pattern in your own command line** matches itself.

## Lessons from the lanes, October to November 2026

From the lanes of 25 October to 6 November 2026; add the next lesson here as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

- Secure Boot enrolment rig in QEMU/OVMF: shim 16.1, GRUB 2.14, kernel signed with the edition key; unsigned and machine-signed modules are rejected until the GRUB entry and MokManager enrol the key, then they load. Rig facts: `mkfs.vfat -F 32 -s 1` for a 256 MiB ESP; /run is noexec; a boot probe must not wait on is-system-running; `virt-fw-vars --add-mok` pre-seeds MokList; `grub-reboot <entry id>` reaches an enrolment entry; send MokManager's key at "Booting in 2-3 seconds", an earlier key reopens OVMF's boot menu; `-cpu max` under TCG for engine binaries. (lane dkms-firstboot-enrol-374)
- Symptom: first KVM check exits 1. Cause: the user lacked the kvm group. Fix: add the kvm group (host gid 105) to the container user. Also Docker's attached output stream dropped later output in some runs: capture to a file and read that. (lane vram-boost-default-263a)

## How the guest's stereo layout reaches SPICE, route by route

The guest tells QEMU its layout (virtio-gpu `SET_SCANOUT_STEREO`, stored on the console by `qemu_console_set_stereo()`); the SPICE display in `ui/spice-display.c` reads it with `qemu_spice_update_stereo()` and hands it to the server with `spice_qxl_set_stereo()`.
That reader is called from the display callbacks, never from a timer, so a route that does not call it never publishes the layout.

| QEMU display route | Callback | Reads the layout |
| --- | --- | --- |
| CPU surface | `qemu_spice_display_switch()` | first thing, before the surface is swapped |
| GL surface (CPU framebuffer exported as a DMA-BUF) | `spice_gl_switch()` | before `spice_server_gl_scanout()`, and when the console has no surface |
| GL texture | `qemu_spice_gl_scanout_texture()` | before the scanout is handed over |
| GL DMA-BUF (virgl, direct guest buffers) | `qemu_spice_gl_scanout_dmabuf()` | on the callback |
| GL scanout disabled | `qemu_spice_gl_scanout_disable()` | after the disable |

The rule: the layout leads the scanout it describes.
The server's worker queue is first in, first out, so layout, scanout, monitor configuration and the draws that follow reach the client in that order.
The virtio-gpu driver sends the stereo command before the scanout command, so the console already holds the new layout when the callback runs.
A layout change with no scanout or surface change publishes nothing on any route; the guests measured here never send one.

### Proving a route with the actual owner

1. Preload a tiny shim that wraps `spice_qxl_set_stereo`, `spice_qxl_gl_scanout2` and `spice_qxl_gl_draw_async` and prints one line per call to stderr (`dlsym(RTLD_NEXT, ...)`, forward the call).
2. Boot the guest with the QEMU under test and a viewer on the same SPICE socket, with QEMU's `-trace enable=qemu_spice_gl*` and `-trace enable=virtio_gpu_cmd_set_scanout_stereo`.
3. Old red: the unmodified QEMU prints no `PRODUCER` line while the trace shows the guest's layout command and `qemu_spice_gl_surface`, and the viewer's stereo property stays 0.
4. New green: one `PRODUCER` line per layout change, each before the `GLSCANOUT` line of its surface; a dark phase between modes prints a layout 0 line; the viewer reports the layout.
5. Keep the CPU route as a control with the same binary (no `gl=on`): it must stay green.
6. Keep the unmodified binary under another name and run the control against it; never rebuild over it.

### Traps met on this route

- **Symptom:** the viewer shows the guest flat on the GL route, layout never arrives, while the CPU route is stereo. **Cause:** `spice_gl_switch()` published the GL surface and monitor configuration without calling `qemu_spice_update_stereo()`. **Fix:** call it before `spice_server_gl_scanout()` and in the no-surface branch. **Found by:** the call-logging shim printed nothing, and `grep qemu_spice_update_stereo ui/spice-display.c` listed four callers but not the GL surface switch.
- **Symptom:** after the correction the viewer has the layout but no acquisition record (the viewer's acquisition count stays 0, the process exits 42). **Cause:** the layout is only the first condition; the server queues an acquisition record only for a current snapshot, and the GL draw path is separate from the CPU draw path. **Fix:** none in this change; it is the next gate, so a green layout is not a green receipt. **Found by:** the viewer's tick lines show `layout=8` with `acquisition=0`.
- **Symptom:** `ninja` stops with `spice/qxl_dev.h: No such file or directory`. **Cause:** the configure step baked an include path that goes through a symlinked parent of the workspace, and the build container only mounted the real path. **Fix:** mount the workspace a second time at the baked path. **Found by:** the `-I` list in the failing command line.
- **Symptom:** a rebuild compiles all 1,600 objects. **Cause:** the objects were retired after the last build. **Fix:** plan for the full compile (about 50 MB of objects, 4 CPUs) and a disk guard; hash, then retire the objects after the run.
- **Symptom:** QEMU with `gl=on` and an NVIDIA render node (CDI) exits with `eglGetDisplay failed: EGL_SUCCESS`, or boots but prints `Cannot retain GL scanout plane` and the guest never reaches its prompt. **Cause:** Mesa's `libgbm` in the test image looks for the vendor backend in `/usr/lib64/gbm`, while CDI mounts it under `/usr/lib/x86_64-linux-gnu/gbm`. **Fix:** `GBM_BACKEND=nvidia-drm` and `GBM_BACKENDS_PATH=/usr/lib/x86_64-linux-gnu/gbm`, plus the render node's group; do not point `__EGL_VENDOR_LIBRARY_FILENAMES` at `/etc/glvnd` (the file is under `/usr/share/glvnd/egl_vendor.d`). **Found by:** the `MESA-LOADER: failed to open nvidia-drm` line at the top of QEMU's stderr.
- **Symptom:** the same trace shows two `qemu_spice_gl_surface` lines per mode. **Cause:** a disable and a new scanout both reach the callback, the console substitutes a placeholder surface for the missing one; it is not a duplicate. The layout 0 line between modes is that placeholder.

### After the layout: the acquisition record on the GL route

A layout that arrives is not a receipt.
On the GL route the server sends a record (`SPICE_MSG_DISPLAY_ACQUISITION`, route 1) after each GL draw, and the viewer library hands it to the frontend through `spice_display_channel_get_acquisition()`.
To find which stage drops it, instrument both ends once and read the counts:

1. Server: compile a copy of `dcc-send.cpp` and `display-channel.cpp` with a `fprintf` before every `return false`, `return` and `continue` in `queue_acquisition_records()`, `display_channel_input_snapshot_current()` and `display_channel_input_target()`, relink the server library, put it first on `LD_LIBRARY_PATH` of the QEMU container. Expect one `queue valid=1 route=1` line per GL draw.
2. Viewer: build the glib library in a container of the same distribution as the frontend image (same soname), print the checks of `display_handle_acquisition()` and the loop of `get_acquisition()`, and mount it over the image's library (`-v DIR:/lib-over:ro -e LD_LIBRARY_PATH=/lib-over`). Expect `recv ... valid=1`, then `get count=1`.
3. The stage with a count that stops is where the fix belongs. Remove the prints before the commit; the final library is built from the committed tree.

### More traps on this route

- **Symptom:** the viewer has the layout (`layout=8`) and the server queues valid route-1 records, but the frontend's acquisition stays 0 and the gate exits 42. **Cause:** `get_acquisition()` required `c->primary`, and a GL scanout is never a SPICE primary surface; the record was received, validated and stored, then skipped by the lookup. **Fix:** for route 1 accept surface 0 with a live GL scanout (the condition `display_handle_acquisition()` already checks). **Found by:** the client print `get count=1 primary=0`, with the server print `queue valid=1` and the client print `recv valid=1` before it.
- **Symptom:** after that fix GTK passes on the GL route (three receipts, every native pixel equal, OFF retired) but Karton still shows `acquired=0`. **Cause:** Karton's GL renderer retires the presentation whenever it has no texture (`No texture available yet`); with an NVIDIA render node the GLX import fails, and with `QT_XCB_GL_INTEGRATION=xcb_egl` the EGL image is created but `glEGLImageTargetTexture2DOES` raises `GL_INVALID_OPERATION` (0x502). **Fix:** none here; run the Karton GL gate on a Mesa node, or give the renderer an external-texture path for drivers that need it. **Found by:** `QT_LOGGING_RULES=org.kde.karton.debug=true` in the frontend container.
- **Symptom:** Python's `re.sub(pattern, 'fprintf(... \\n ...)', text)` writes a real newline into the C string and the compiler says `missing terminating " character`. **Cause:** `re.sub` interprets escapes in a replacement string. **Fix:** pass a function (`lambda m: ...`).
- **Symptom:** `docker run -v /some/repo:/repo:ro` for a path that no longer exists creates an empty root-owned directory at that path and apt says `does not have a Release file`. **Cause:** the daemon creates missing bind sources. **Fix:** check the path first and mount the current repository.
- **Symptom:** a wrapper shell script exits 127 on `${flag:+VAR=1} command`. **Cause:** an expansion is not an environment assignment. **Fix:** `env VAR=$value command`.

### Karton's GL scanout on NVIDIA and on a slow Mesa node

Keep the GL gate honest on the GPU it runs on: a viewer that only imports Mesa's buffers fails every NVIDIA user.

- **Symptom:** Karton logs `No texture available yet` for every frame, or (Qt GLX) `The GL scanout could not be imported ... modifier 0x300000000e08014 (GLX)`, and the gate exits 42 with `acquired=0`. **Cause:** Karton read the scanout through the deprecated single-plane API, which has no modifier, offset or plane list, so NVIDIA's block-linear buffer was described as linear; Qt's GLX integration cannot import it at all. **Fix:** read `spice_display_channel_get_gl_scanout2()` and build the EGL attribute list as spice-gtk's own EGL path does (every plane with descriptor, pitch, offset, and the two modifier words when the modifier is not `DRM_FORMAT_MOD_INVALID`); on NVIDIA run Qt with `QT_XCB_GL_INTEGRATION=xcb_egl`. **Found by:** Karton's debug category (`QT_LOGGING_RULES=org.kde.karton.debug=true`) and a warning added where the import fails, so the failure is said once per scanout.
- **Symptom:** after the import works the presentation is still retired every frame (`COMPLETION success=0`). **Cause:** the completion check fails a frame on any `glGetError()` after `glFinish()`, and NVIDIA's EGL leaves `GL_INVALID_OPERATION` in the state after every swap. **Fix:** clear the error state on `frameSwapped`, so the check at the end of the frame judges the frame's own rendering. **Found by:** draining and printing `glGetError()` at each `QQuickWindow` signal (`beforeRendering`, `afterRendering`, `frameSwapped`); the error appeared between `afterRendering` and `frameSwapped`.
- **External-only formats are not covered:** a modifier the driver lists as external-only (`eglQueryDmaBufModifiersEXT`) needs `GL_TEXTURE_EXTERNAL_OES` and a `samplerExternalOES` blit; the XRGB8888 scanouts measured here bind to `GL_TEXTURE_2D`, so that path is not written or tested.

Running the gate on a second machine without installing anything on it:

1. Pack only what the run needs: the candidate QEMU, the libraries it loads (`ldd` with the same `LD_LIBRARY_PATH`), the guest disk and kernel, the frontend image (`docker save | zstd | ssh ... podman load`) and the small harness scripts. Keep everything under one directory and give podman a private `--root`/`--runroot` there.
- **Symptom:** `qemu-img: error while loading shared libraries: libz.so.1` from an image made with `podman import`. **Cause:** the files came from an image with merged `/usr` and a linker cache; the import has neither. **Fix:** put the real files under `usr/`, add the `lib`, `lib64`, `bin`, `sbin` symlinks, include `/etc/ld.so.cache`, and `--change 'ENV PATH=...'` on import. Two archives appended with `tar -A` and a path listed twice both fail the import (`duplicates of file paths not supported`).
- **Symptom:** the guest stops after `Reached target graphical.target` and never prints a prompt; the harness waits for it. **Cause:** the TCG guest on the slower host is seven times slower, waits for kernel entropy, and its first login blocks. **Fix:** give the guest `-object rng-random,filename=/dev/urandom,id=rng0 -device virtio-rng-pci,rng=rng0` and `random.trust_cpu=on`; the same boot then reaches the prompt. Scale the harness's wait times too. **Better, measured later:** check `/dev/kvm` first. A user without the `kvm` group can still have an ACL entry on the node; with `-machine q35,accel=kvm -cpu host` and `--device /dev/kvm` the same guest boots in 40 seconds instead of five minutes, the GL route no longer stalls, and the gate runs end to end. The TCG stall was slowness, not a QEMU or SPICE fault.
- **Symptom:** the run is cut at 70 C. **Cause:** a TCG guest plus GL heats this node past the start gate by 10 to 15 C; the start gate is for starting, the emergency stop is the hardware's own limit minus a margin (90 C against a 100 C critical). **Fix:** wait for the start gate before each run, stop only at the margin.
- Rootless podman needs `--userns=keep-id` so the harness's bind-mounted directories stay writable, and the docker-only flags `--group-add`, `--cpus`, `--memory` dropped by a small wrapper named `docker`.
- **Symptom:** after the run the second machine's bench lock is still taken, and the next bench waits on it. **Cause:** the lock was held by `flock -w 600 9 && sleep 7000` started over ssh; the `sleep` keeps the descriptor, outlives the ssh session and is reparented to init. **Fix:** remember the holder's PID when the lock is taken and kill that PID at the end, then check with `flock -n` that the lock is free. **Found by:** `ls -l /proc/PID/fd` on the remaining `sleep`, which pointed at the lock file.

### Karton chooses the working GL path itself, and the Wayland session

- **One default for every driver.** `chooseXcbGlIntegration()` (called by `main()` and by the gate's probe before the `QApplication`) sets `QT_XCB_GL_INTEGRATION=xcb_egl` whenever the person has not set it and the session is xcb, and logs it once. It needs no X connection: it returns first for `QT_QPA_PLATFORM=wayland` (or `offscreen`), and when no platform is named and `WAYLAND_DISPLAY` is set or `DISPLAY` is empty. Measured: through Qt's GLX integration the import fails and through EGL it passes on NVIDIA (RTX 3060) and on Mesa radeonsi (A10), both under Xwayland. Run the gate without the variable (`VM255_NO_GLX_FORCE=1`) so the choice is exercised, and once with `xcb_glx` set by hand: Karton follows it and warns.
- **Native Wayland client, read back from the compositor.** The frontend image lacks Qt's shell plugins (`qt.qpa.wayland: No shell integration named "xdg-shell" found`, exit 134): mount `wayland-shell-integration`, `wayland-decoration-client` and `wayland-graphics-integration-client` from a build container and set `QT_PLUGIN_PATH`, with `QT_QPA_PLATFORM=wayland`. Run the compositor from a published image in its own container (`kwin_wayland --virtual`, the output switched to the anaglyph twin with `kscreen-doctor output.Virtual-0.mode.5`, `WAYLAND_DEBUG=server` into the container log), share the runtime directory with the Karton container, and let the probe wait after each presented pair while the harness takes ScreenShot2's two-eye capture. The check finds the window content by its own pattern, then compares each eye with the guest's formula (the eye is shown at the viewport size, so KWin's one linear scaling is part of the expected value) and requires the swapped-eye negative to fail every pixel. Count `kde_stereo_content_manager_v1#N.create(` and `set_content(3)` in the log: one pair per mode change here.
- **Another compositor build.** To run a staged KWin on the same image, start the throwaway container as root, `dpkg -i` the staged `kwin-common`, `kwin-data`, `kwin-wayland` and `libkwin6`, then `setpriv` to the lane user with the render group; `docker exec` must then use `--user`, or the D-Bus ping fails with the wrong uid and the harness times out waiting for a socket that exists.
- **Symptom:** the guest never reaches its prompt although the station is idle. **Cause:** the host's load average was 50 (other jobs); a TCG guest is as slow as on the A10 and the gate's wait expires. **Fix:** check `/proc/loadavg` before blaming the guest, and give the guest virtio-rng and `random.trust_cpu=on` here too.
- **Symptom:** a Qt file that includes `<X11/Xlib.h>` fails with `qtextstream.h must be included before any header file that defines Status`. **Cause:** Xlib defines `Status`, `Ok` and others. **Fix:** include every Qt header first and Xlib/GLX last, in a separate block.
- **Symptom:** a commit of a behaviour change carries re-wrapped lines and a moved include. **Cause:** `clang-format -i` on a whole file that was never formatted. **Fix:** format changed lines only (`git clang-format`, or `clang-format --lines=A:B`), and check `git diff -w --stat` against `git diff --stat`.
- **Bench lock:** note the holder's PID when taking `flock ... && echo LOCKED $$ && sleep N`, kill that PID and its `sleep` at the end, and confirm with `flock -n`.

### Proving the packaged Karton, and a package carrying the fixes

- **Carry a fix to a published package on its own base.** The package is upstream's snapshot plus its own patches, not the fork's head: unpack the plain source, apply `debian/patches`, and write the new patches against that tree (the fork's file may be a different, larger one). Check that each patch applies to the base with `git apply --check`, give it DEP-3 fields (`Origin: other`, `Forwarded: no`), and look for a fix the base does not need (here the swap-error drain: the packaged renderer had no completion check to fail).
- **Symptom:** the package build stops in `override_dh_builddeb` with `check-link needs --archive-config / --scratch`, then with `bwrap: No permissions to create a new namespace`. **Cause:** the link gate wants a signed archive configuration (`sources.json` and `keyrings/`, its edition entry reading the signed tree mounted at `/pub`) and bubblewrap's user namespaces, which Docker's default profile refuses. **Fix:** pass the configuration (done in the recipe) and run the gate the way the kwin recipes do, with the relaxed container security options; a person has to allow that. Without the gate the .deb is deleted, so build a plain package from the plain source (`dpkg-buildpackage -b` in the same image) only to exercise behaviour, and label it so.
- **Driving the real program.** `karton` asks libvirt for `qemu:///session` and runs `virsh domdisplay NAME`. An `LD_PRELOAD` shim that turns `virConnectOpen` into `test:///default` gives it a running domain without a daemon, a stand-in `virsh` on PATH answers the SPICE address of the guest's UNIX socket, and KWin's fake input (`fake-click`, any client, headless KWin with permission checks off) presses "View VM". The compositor's own capture then shows the window.
- **Detector.** The guest's picture is (x % 256, y % 256, tag) with the tag in blue; count pixels whose blue is a tag and whose red and green are not equal to it. The control (published package) stays below 2,000; the fixed package reaches over a million in both eyes.
- **Symptom:** every window of an xcb Qt program is black in the compositor's capture under Xwayland on NVIDIA once `xcb_egl` is selected, while the pixels read back from the X window are right and the same program on `xcb_glx` is visible. **Cause:** not found; Xwayland's presentation of EGL windows on that driver. **Consequence:** an X-side read-back does not prove what the compositor shows; prove an X11 case by a compositor capture, and treat NVIDIA under Xwayland as open.

