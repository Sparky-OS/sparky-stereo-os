# A stereo X11 window when Xwayland has no glamor

Learned on ORDER 560 (November 2026), on Stereo KWin +stereo3d54, Mesa +stereo3d21 and Xwayland 24.1.13 +stereo3d4 and +stereo3d5.
Load it with [native-linux](../SKILL.md) when an X11 program's stereo window is not a pair on a machine or a virtual machine without 3D acceleration, or with `XWAYLAND_NO_GLAMOR=1`.
The result first: from Xwayland `2:24.1.13-1+stereo3d5` such a window is a pair without glamor too, a top-level and a child window alike, and with glamor nothing changes.

## What happens without glamor

- Xwayland without glamor (no card, or `XWAYLAND_NO_GLAMOR=1`) has no DRI3, so every GL program draws on Mesa's software renderer, whatever card the machine has; `xdpyinfo -queryExtensions` lists `Present` and no `DRI3`.
- For a stereo window from declaration version 4, Mesa's software path puts both eyes into a pixmap twice the window's width and presents it with the Present extension; the X window stays one eye wide.
- Xwayland must flip that pixmap to the window's surface whole. A pixmap can be flipped only if it has a `wl_buffer`.
- On the shared memory backend a program's pixmap gets shared memory and a `wl_buffer` only when its size is a top-level window's (`xwl_shm_create_pixmap()`, `dimensions_match_toplevel_window()`), so the pixmap of both eyes was a plain pixmap: `xwl_present_check_flip()` refused it and Present copied it into the window, which keeps the left eye.
- Stereo KWin, told that the window holds two eyes, then showed the left half of the left eye to one eye and its right half to the other.
  A stereo child window with its own surface kept a buffer of both eyes, but every present was copied into its left half: the right eye never changed.

## Recipe: which layer loses the pair

One fresh Stereo KWin session per reading (`kwin_wayland --virtual --xwayland`, a render node for KWin), the same client in each.
Use [`scripts/glx-back-both-eyes.c`](../scripts/glx-back-both-eyes.c) (a GLX quad buffer window, left eye red, right eye blue) and [`scripts/x11-present-pair.c`](../scripts/x11-present-pair.c) (the same hand-over without OpenGL, with a white square that moves 16 pixels at every present).

1. **The control and the red.** The client with glamor, then with `XWAYLAND_NO_GLAMOR=1` in KWin's environment; capture both eyes with ScreenShot2 and read them with [`scripts/check-pair-eyes.py`](../scripts/check-pair-eyes.py).
   A pair: red left, blue right, the green rectangle centred in both, the white square at the same place in both.
   The fault: both eyes red, the green rectangle on the right of one eye and on the left of the other.
2. **The declaration.** `x11_props.py` ([stereo-proof-rig](../../stereo-proof-rig/SKILL.md)) must show `_KDE_NET_WM_STEREO_CONTENT` 3 and `_KDE_NET_WM_STEREO_CONTENT_VERSION` 4 on the window that draws, and `xwininfo` its width unchanged (one eye).
   Equal in both runs, so the compositor was told the same thing.
3. **What the GL library hands the X server.** Preload [`scripts/x11-swap-requests-shim.c`](../scripts/x11-swap-requests-shim.c) into the client: it prints the pixmap created at the swap, the image put into it and the present.
   Measured in both runs: `XCreatePixmap 1600x600`, `XShmPutImage 1600x600`, `xcb_present_pixmap` to the 800 wide window. Mesa hands over both eyes whole, so the loss is after it.
4. **What Xwayland attaches.** Put a wrapper named `Xwayland` first in KWin's `PATH` (KWin starts the first one it finds) that sets `WAYLAND_DEBUG=client` and sends the server's messages to a file, then count the buffers by size:
   `grep -E 'create_buffer|create_immed|damage' FILE | sed -E 's/^\[[^]]*\]//; s/#[0-9]+//g' | sort | uniq -c`.
   With glamor: `zwp_linux_buffer_params_v1.create_immed(..., 1600, 600, ...)`, one per frame. Without glamor before the fix: only `wl_shm_pool.create_buffer(..., 800, 600, ...)`. The buffer of both eyes never left Xwayland.
5. **How the present completed.** `x11-present-pair` selects `PresentCompleteNotify` and prints `completed as flip` or `completed as copy`: flip with glamor, copy without it before the fix. That names the function: the flip check.
6. **The frame of a real output, with no card at all.** A KWin without any render node composes with QPainter and ScreenShot2 is cancelled, so the true case is read in a guest on a VKMS output ([real-output-readback.md](../../stereo-proof-rig/references/real-output-readback.md)): the scanned-out side by side (full) frame goes through `check-pair-eyes.py` as it is.
   The control in the same guest is the older `Xwayland` binary, brought in the evidence share and put first in `PATH`.

## The fix (Xwayland patches 0010 to 0012, +stereo3d5)

- **0010, `hw/xwayland/xwayland-shm.c`:** a pixmap twice the width, and of the height, of a window that holds two eyes (`xwl_present_window_holds_two_eyes()`: the declaration and version 4 on the window) gets shared memory and a `wl_buffer` too. The window is a top-level or a child of one, so the window tree is walked; it is walked only once a program has declared version 4 (the atom exists), so a desktop without a stereo program pays nothing.
- **0011, `hw/xwayland/xwayland-present.c`:** a flip's damage is the window's, one eye wide. For a pixmap of both eyes the same place in the right eye is damaged too.
- **0012, the test** in the source's own `xwayland` suite: `test/scripts/xwayland-stereo-pair.sh` starts a headless weston and Xwayland with `XWAYLAND_NO_GLAMOR=1` and `WAYLAND_DEBUG=client`, runs `test/stereo-present-pair.c` for a top-level and for a child, and wants the present flipped, a `create_buffer` of 1600x600 and `damage_buffer(800, 0, 800, 600)`; an undeclared window is the control and must be copied.
  It fails on the published series, still fails on the damage rows with 0010 alone, and passes with both; 17 seconds.
  The package build runs it: read `stereo pair without glamor OK` in the build log.

Measured from the installed packages, published against new, on an AMD card and on an RTX 3060 (the software-drawn rows give the same pixels on both):

| Case | +stereo3d4 | +stereo3d5 |
|---|---|---|
| GLX quad buffer client, glamor off | both eyes show the left eye's halves | a pair |
| The same in a guest with no card, scanned-out frame | not a pair | a pair, 360,000 pixels differ between the halves |
| A closed CAD program's quad buffer mode, glamor off | no block matches between the eyes | 381 blocks, the nearest at −70.6 px, the median −27.2, vertical 0 |
| The same, glamor on (radeonsi, zink on NVIDIA) | 381 blocks, the same numbers | the same numbers |
| Declared child window, moving content, glamor off | right eye frozen | the same frame in both eyes |
| Six plain 2D X11 programs, glamor on and off (`xmessage`, `glxgears` with a fixed clock, a GTK 4 program, a Qt Quick scene, the Present client without a declaration, the CAD program with stereo off) | each equal to itself across two runs | 0 differing pixels against +stereo3d4 in all twelve rows |
| The declared window partly covered by a child window of its own | not a pair, glamor on or off | not a pair, glamor on or off (below) |

## Traps

- **Symptom:** after the first half of the fix the eyes have the right colours, but the right eye shows an old frame (the moving square at 36 px in one eye and 564 in the other).
  **Cause:** the flip damaged `damage_buffer(0, 0, 800, 600)` only, and a compositor reads only the damaged part of a `wl_shm` buffer; a dmabuf is read whole, which is why glamor never showed it.
  **Fix:** 0011.
  **How found:** the white square of `x11-present-pair`, then the damage lines in Xwayland's `WAYLAND_DEBUG` log.
- **Symptom:** a still test picture passes while the program's moving picture is wrong in one eye (the child-window row of `x11-child` passed on the faulty build).
  **Cause:** red in one eye and blue in the other says each eye got its view once, not that it gets every frame.
  **Fix:** something that moves at the same place in both eyes, read in both.
  **How found:** the same row with `x11-present-pair CHILD=1`.
- **Symptom:** ScreenShot2 answers `Screenshot got cancelled` in a session without any card.
  **Cause:** KWin without a render node composes with QPainter, and the capture needs its OpenGL backend.
  **Fix:** for the rig, a card for KWin and `XWAYLAND_NO_GLAMOR=1` (the same Xwayland path); for the true case, the guest of step 6.
- **Symptom:** an X client on a rootless Xwayland started by hand under weston never gets its `PresentCompleteNotify`, and Xwayland creates no surface.
  **Cause:** a rootless Xwayland gives a top-level a surface only once a window manager has redirected it (Composite, manual), and no window manager runs there.
  **Fix:** the test stands in for it: `WM=1` makes `x11-present-pair` redirect the root's children, and the declared child, as a compositor does.
  **How found:** the process list in the container (the client waiting) and a `WAYLAND_DEBUG` log that ended after the registry.
- **Symptom:** the package build stops in `dh_auto_test` with `sh: 1: /usr/bin/xkbcomp: not found` and `Failed to activate virtual core keyboard`.
  **Cause:** a test that starts an X server needs `x11-xkb-utils` and `xkb-data`, which a build container does not have.
  **Fix:** both in `Build-Depends` with `<!nocheck>`, beside weston and the xcb development packages the test links.
  With `libxcb1-dev` present, upstream's own `sync` test is defined too and needs the same two packages.
  **How found:** the test section of the build log.
- **Symptom:** on an NVIDIA card with glamor off, a GLX client says `DRI3 not available` and gets no configuration, or the program says `Could not initialize GLX`.
  **Cause:** Mesa's zink was forced (`MESA_LOADER_DRIVER_OVERRIDE=zink`) and zink presents through DRI3, which Xwayland without glamor does not have.
  **Fix:** in a test, leave the driver to Mesa (or `LIBGL_ALWAYS_SOFTWARE=1`) with `__GLX_VENDOR_LIBRARY_NAME=mesa`; with glamor on, zink as usual ([nvidia-opengl.md](nvidia-opengl.md)).
  **How found:** the client's own messages, equal on the old and the new Xwayland.
- **Symptom:** a preloaded shim crashes the GL program at its first swap.
  **Cause:** libglvnd loads the vendor's GL library privately, so `dlsym(RTLD_NEXT, ...)` finds no `XShmPutImage` or `xcb_present_pixmap` and the shim calls a null pointer.
  **Fix:** look the real function up in its own library (`dlopen("libXext.so.6")`, `libxcb-present.so.0`) when `RTLD_NEXT` finds nothing, and stop with a message when that fails too.
- **Symptom:** installing development packages into a rig image that holds a staged, newer Mesa stops with `Packages were downgraded and -y was used without --allow-downgrades`.
  **Cause:** the published repository is pinned at 1001 and holds the older Mesa.
  **Fix:** a pin file that sorts before the edition's (`00-cohort-mesa`: `Package: src:mesa:any`, `Pin: version <the staged version>`, `Pin-Priority: 1100`) and a flat local source with the staged packages.
- **Symptom:** a closed program's picture differs from itself by some tens of pixels between two runs of one build on a card.
  **Fix:** capture the old build twice before comparing it with the new one; on the software renderer the same picture was equal pixel for pixel, also across two cards.

## What this does not cover

- **A present that cannot be flipped is still copied, with glamor and without.** A declared window partly covered by a child window of its own (`x11-present-pair COVER=1`: a 60x60 plain child) completes every present as a copy, and the capture is not a pair on +stereo3d4 and on +stereo3d5, on both backends: the copy keeps the left eye and the compositor shows its halves. The same holds for a present with an offset, and for the frames of a resize whose pixmap does not match the window yet (the GLX client came back to a pair after a resize, a hide and a show). A program whose 3D area has child windows over it belongs on the child-window route (the 3D area declared as a child of a 2D window); the copy case itself is open work: the program's GL library can see it (`PresentCompleteNotify` says copy) and must then take the declaration back and say so, never leave a split picture.
- **The next Xwayland base.** Upstream's stable branch after 24.1.13 (24.1.14 and 24.1.15) adds a check to `xwl_present_check_flip()` that the flip pixmap has the size of the window's pixmap ("xwayland/present: Only flip if the window pixmap dimensions match", Michel Dänzer). A window that holds two eyes has a pixmap one eye wide before its first flip, so patch 0005's exception must cover that check too when the package moves base, or the pair is copied again, with glamor as well; the suite's test (0012) and the glamor control of step 1 show it. The extended check is carried by `2:24.1.15-1+stereo3d1+lc1` (ORDER 562); both height checks remain, and an unrelated backing width is rejected.
- Each present of both eyes makes a new shared memory pool of that size (a new pixmap per swap is Mesa's software path); Xwayland's open files and memory stayed level over a fast run (11 to 12 files, about 75 MB), and 600 presents of a 1600x600 pair back to back took 10.0 s, the output's 60 a second, as with glamor.
- zink on NVIDIA with glamor off (above): the program has no GLX at all, on the old and the new package alike.
