# A stereo X11 window when Xwayland has no glamor

Learned on ORDER 560 (November 2026), on Stereo KWin +stereo3d54, Mesa +stereo3d21 and Xwayland 24.1.13 +stereo3d4 and +stereo3d5.
Load it with [native-linux](../SKILL.md) when an X11 program's stereo window is not a pair on a machine or a virtual machine without 3D acceleration, or with `XWAYLAND_NO_GLAMOR=1`.
The result first: from Xwayland `2:24.1.13-1+stereo3d5` such a window is a pair without glamor too, a top-level and a child window alike, and with glamor nothing changes; a Vulkan program's own top-level window is a pair there from Mesa `+stereo3d25` ([below](#a-vulkan-pair-without-dri3-the-layer-and-lavapipe)); from `2:24.1.15-1+stereo3d2` a pair that cannot be flipped is kept as well, and where it cannot be kept Mesa shows one flat picture and tells the person ([below](#when-the-pair-cannot-be-flipped)).

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
| The declared window partly covered by a child window of its own | not a pair, glamor on or off | not a pair, glamor on or off; a pair from `2:24.1.15-1+stereo3d2` ([below](#when-the-pair-cannot-be-flipped)) |

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
  **Fix:** from Mesa +stereo3d22 the screen takes the software renderer and the person is told ([below](#the-session-that-sets-zink-for-every-program-with-xwayland-without-glamor)); on an older Mesa, in a test, leave the driver to Mesa (or `LIBGL_ALWAYS_SOFTWARE=1`) with `__GLX_VENDOR_LIBRARY_NAME=mesa`; with glamor on, zink as usual ([nvidia-opengl.md](nvidia-opengl.md)).
  **How found:** the client's own messages, equal on the old and the new Xwayland.
- **Symptom:** a preloaded shim crashes the GL program at its first swap.
  **Cause:** libglvnd loads the vendor's GL library privately, so `dlsym(RTLD_NEXT, ...)` finds no `XShmPutImage` or `xcb_present_pixmap` and the shim calls a null pointer.
  **Fix:** look the real function up in its own library (`dlopen("libXext.so.6")`, `libxcb-present.so.0`) when `RTLD_NEXT` finds nothing, and stop with a message when that fails too.
- **Symptom:** installing development packages into a rig image that holds a staged, newer Mesa stops with `Packages were downgraded and -y was used without --allow-downgrades`.
  **Cause:** the published repository is pinned at 1001 and holds the older Mesa.
  **Fix:** a pin file that sorts before the edition's (`00-cohort-mesa`: `Package: src:mesa:any`, `Pin: version <the staged version>`, `Pin-Priority: 1100`) and a flat local source with the staged packages.
- **Symptom:** a closed program's picture differs from itself by some tens of pixels between two runs of one build on a card.
  **Fix:** capture the old build twice before comparing it with the new one; on the software renderer the same picture was equal pixel for pixel, also across two cards.

## When the pair cannot be flipped

Learned on ORDER 561 (November 2026), on Stereo KWin +stereo3d54, Xwayland `2:24.1.15-1+stereo3d1` and Mesa `26.1.6-1+stereo3d21`, fixed in Xwayland `2:24.1.15-1+stereo3d2` and Mesa `26.1.6-1+stereo3d22`.
The X server can flip a presented pixmap only where it could flip any window's: not when a child window of the stereo window clips it (a tool bar, a button or a status field that a toolkit puts over its 3D area), not when the present has an offset or an update region, not for a frame made for the size the window had before a resize.
Such a present was copied into the one eye wide window, which keeps the left eye, and Stereo KWin, told that the window holds two eyes, showed half of the left view to each eye, with glamor and without, and nothing told the person.

**What is a pair now (Xwayland patch 0013).**
A copy into a window that holds two eyes keeps both: the window's pixmap becomes twice the window wide (what it showed goes to both halves), the left eye is copied as for any window, the right eye goes to the same place in the right half, clipped as the left eye is, and what the child windows draw is copied to the right half before the pixmap goes to the compositor, because it is 2D.
A frame of another size is cut or left short in both eyes alike, as a copy does to any window.
The present completes as a flip: for a window that declares two eyes, `PresentCompleteNotify` says flip when both eyes reached the window's surface and copy when only the left one did.
A window that stops declaring two eyes gets a buffer one window wide at once.

**What is told (Mesa patch 0038).**
Where the pair still cannot be kept (an X server without patch 0013, a declared window smaller than its surface that no compositor redirected, no memory for the wider pixmap), Mesa's GLX reads the completion, on DRI3 and on the software path:

- two presents in a row of the window's own size that complete as copies take the declaration back: `_KDE_NET_WM_STEREO_CONTENT` and its version are deleted, the window leaves its owner's `_KDE_NET_WM_STEREO_CONTENT_CHILDREN`, and from the next frame the left view alone is presented at the window's size, while the program goes on drawing both;
- one copy is not enough: the first present of a window often completes as a copy with nothing copied, because the window manager unmaps and maps the window while it takes it (measured on both Xwayland versions);
- a swap waits for its own completion until one pair was flipped, and whenever the program's last swap is more than a tenth of a second old, and after a first copy it presents the same pair once more, so a program that draws one frame is taken back in that swap;
- the person is told through `sparky-stereo-problems`: package `libglx-mesa0`, key `stereo-pair:PROGRAM` (the process name), message `LOCAL2` with the program's name and Mesa's own words last, in the ten languages; the record's English text is used where the catalog is missing;
- while flat, three flips in a row of the left view bring the declaration back, and the next pair that is flipped ends the problem; when the pair is copied at once after two such returns, nothing more is tried at that size;
- `LIBGL_DEBUG=verbose` prints every completion until a pair is flipped (`stereo pair: window 0x... 800x600: a 1600x600 buffer was copied (both eyes)`).

**Recipe: tell which of the two you are looking at.**
[`scripts/glx-covered.c`](../scripts/glx-covered.c) is the GLX twin of `x11-present-pair COVER=1`: a quad buffer window with a 60x60 child over it, which can appear, go and be painted at chosen swaps, and which prints the window's declaration at the swaps named in `REPORT`.
[`scripts/check-pair-flat-split.py`](../scripts/check-pair-flat-split.py) reads a capture as PAIR (two eyes, the child at the same place in both), FLAT (the left view whole, one correct picture) or SPLIT (the wrong picture).

1. One fresh session per case, the client covered from its first swap, captured: SPLIT with `declared 3` to the end is the fault; PAIR is patch 0013 at work; FLAT with `declared 0` is Mesa's take-back, and then `sparky-stereo-problems list` has the record.
2. `x11-present-pair COVER=1` prints `completed as flip` on a server with patch 0013 and `completed as copy` without it; `X_OFF`, `Y_OFF` and `SRC_W` give the offset and the frame of another size.
3. The cover that comes and goes: `COVER_AT=40` and `UNCOVER_AT=40` with `REPORT=39,41,45,50`; on a server without the patch the declaration goes within two swaps of the cover and returns three flips after it left.
4. The still program: `STILL_AT=2`; on a server without the patch the one frame must end FLAT, not SPLIT.
5. In Xwayland's own suite the test reads the window's pixmap as a compositor's window manager can (`CompositeNameWindowPixmap` of the redirected window, then `GetImage`): twice the window wide, red at the left, blue at the right, the child's colour in both.

Measured from the installed packages (Stereo KWin +stereo3d54, one fresh session per row, an AMD card and an RTX 3060, glamor on and off in every row):

| Case | Xwayland +stereo3d5, Mesa +stereo3d21 | Xwayland 24.1.15 +stereo3d2, Mesa +stereo3d22 | Mesa +stereo3d22 on the +stereo3d5 server |
|---|---|---|---|
| Covered from the first swap (Present client and GLX twin) | split, 8 of 8, nothing told | a pair, the child in both eyes, 8 of 8, nothing told | flat and told, 4 of 4 |
| Cover appears at swap 40 | not run | a pair, 4 of 4 | flat and told, 4 of 4 |
| Cover goes at swap 40 | not run | a pair, 4 of 4 | flat for 40 swaps, three flips of the left view, then a pair; the problem ended, 4 of 4 |
| A program that draws one frame, covered | not run | a pair, 4 of 4 | flat and told inside its one swap (two copies of both eyes), 4 of 4 |
| Offset 40,30; a frame 700 wide for an 800 wide window | not run | a pair, 8 of 8 | not run |
| The child painted by the server, the program still or drawing | not run | the new colour in both eyes, 8 of 8 | not run |
| Declaration deleted at present 50 | not run | one flat picture, 8 of 8 | not run |
| Uncovered | a pair | a pair, never told | a pair, never told (one first copy, then flips) |

An animating stereo program swaps as fast as before: with the default interval 59.9 against 59.6 swaps a second on radeonsi and 59.8 against 59.9 on zink over the RTX 3060; with interval 0, 2565 against 2646 and 1006 against 1084; on the software renderer without glamor 176 against 199 (older stack first; [`scripts/glx-fps.c`](../scripts/glx-fps.c), 600 swaps of an 800x600 quad buffer window).
The wait of a swap for its own completion therefore costs an animating program nothing that these rows can show.

### Traps of this part

- **Symptom:** the suite's test never sees a second buffer attached for a covered window, though the present completed.
  **Cause:** no compositor maps a surface there (a rootless Xwayland under a headless Weston with no window manager), so no frame callback comes and Xwayland posts damage once; flips commit by themselves, copies do not.
  **Fix:** read the window's pixmap through Composite instead of the Wayland requests.
  **How found:** `WAYLAND_DEBUG=client` on Xwayland showed `create_buffer` for both sizes and one `attach`.
- **Symptom:** every stereo program is taken back to flat at its first frame and returns three frames later.
  **Cause:** the rule "one copied present is certain" met the frame the server drops while the window manager takes the window; it completes as a copy.
  **Fix:** two in a row, and the same pair presented once more in a swap that waited.
  **How found:** `LIBGL_DEBUG=verbose` in the uncovered control row.
- **Symptom:** after a take-back the left view never flips and the declaration never returns (DRI3), or completions are never matched (software path).
  **Cause:** the loader's `set_drawable_size` hook left the buffer two views wide; and the software path read completions after sending the next present, so the serial it waited for was already the next one.
  **Fix:** the hook sets the width for the flat state too; completions are read before the next present, with the size of the present they belong to.
  **How found:** the debug line showed `a 1600x600 buffer was copied (left view alone)`.
- **Symptom:** `lc-successor.py --in-place --overlay` stops with `the new source differs beyond its changelog and toolkit: ['debian/lang']`.
  **Cause:** the overlay brought a new folder and only its files were allowed.
  **Fix:** the tool allows the folders of overlaid files.
- **Symptom:** a library in a `Multi-Arch: same` package must tell the person and the engine exists for one architecture.
  **Fix:** the catalogs and the dependency go into the amd64 package only (a file that one architecture alone ships is no conflict), the library opens the engine's private library at run time and never links it, and a process that cannot load it (a 32-bit program) runs `sparky-stereo-problems keep` with the same arguments; when neither is there the log says that the person cannot be told. See [a library that tells the person](../../system-housekeeping/references/problems-from-a-library.md).

## The session that sets zink for every program, with Xwayland without glamor

On a machine whose desktop runs on NVIDIA's driver the session sets `MESA_LOADER_DRIVER_OVERRIDE=zink` for every program ([nvidia-opengl.md](nvidia-opengl.md)).
When Xwayland then runs without glamor (it could not start its acceleration, or `XWAYLAND_NO_GLAMOR=1`) there is no DRI3, and Mesa up to +stereo3d21 ended GLX with `DRI3 not available`: every OpenGL program of the session got no configuration and stopped, with no word to the person.
From Mesa +stereo3d22 such a screen takes the software renderer, as with any other driver on that server, a quad buffer window included, and the person is told (`libglx-mesa0`, key `zink-without-dri3`, message `LOCAL4`, severity degraded); the next program that finds zink with DRI3 ends the problem.
The row: the session's four variables on the card through CDI, `XWAYLAND_NO_GLAMOR=1` in KWin's environment, the renderer string (`llvmpipe`), and `sparky-stereo-problems list`.

## A declared child covered by a child of its own

Learned on ORDER 561b, on Xwayland 24.1.15 +stereo3d2 with Stereo KWin +stereo3d54 and Mesa +stereo3d22.
This is different from a sibling covering the declared child: the cover draws into the declared child's backing pixmap and must appear at the same place in both views.

### Recipe

1. Run `x11-present-pair` in the fresh-session rig with `CHILD=1 COVER=1 FRAMES=100 HOLD_S=20` and capture after its last present.
   Check with `check-pair-flat-split.py --child grey`: both eyes must contain the 60 by 60 cover, 30 pixels from their left edge.
2. Add `COVER_PAINT_AT=50`, capture after present 50, and require `--child yellow`.
   The moving white markers must still occupy the same place in both views.
3. Run on each card with glamor on and with `XWAYLAND_NO_GLAMOR=1` in Xwayland's environment.
   Without glamor the client draws in software even when KWin uses the card.
4. In Xwayland's own suite, run `meson test -C BUILD --print-errorlogs 'stereo pair without glamor' 'stereo child cover with buffer recycling'`.
   The second test consumes buffers and answers frame callbacks on role-less surfaces so the backing buffers actually rotate; the assertions read Xwayland's pixmap through Composite and GetImage.
   It checks an initial grey cover, a repainted yellow cover, both before and after delayed redirection, and a remap without another present.
5. Keep the original top-level covered, offset, wrong-size, repaint, undeclare and uncovered rows as controls.

### Symptom, cause, fix, and how the cause was found

**Symptom:** both views and the moving markers are correct, but the cover has zero pixels in either eye, even after repainting.
A check that reads only the two background colours passes this fault.

**Cause:** `xwl_window_set_window_pixmap()` queues `xwl_window_update_child_surface()` when a backing buffer changes as well as when the child first receives its surface.
The work procedure restored the raw Present snapshot on every such change.
That replaced the composed picture, including the cover's paint, with the client's pair.
The snapshot saved before delayed redirection also lacked the cover already painted into the newly redirected window.

**Fix in Xwayland +stereo3d3:** mark restoration pending when an independent child surface is created and consume that mark once.
When restoring, copy `winSize - clipList` from the current window pixmap into the same place in both halves of the saved pair before replacing the pixmap.
Normal buffer recycling keeps the composed picture; a new surface after a remap still restores the last pair.
Nothing is resized.

**How found:** an instrumented server showed that the cover and stereo child shared the same backing pixmap and the stereo child's clipping excluded the cover correctly.
It then logged 70 snapshot restores during 70 presents.
Gating restoration on damage registration fixed repainting but lost the last pair after a remap; the explicit per-surface mark passes that control.
The buffer-recycling suite fails all four cover cases on +stereo3d2 and passes on +stereo3d3, including delayed redirection and remapping without another present.
A headless Weston alone leaves the test's role-less surfaces unmapped and does not exercise repeated backing-buffer recycling.

Measured again from the apt-installed Xwayland +stereo3d3 and Mesa +stereo3d23 packages, one fresh session per case:

| Declared child case | AMD, glamor | AMD, shared memory | NVIDIA, glamor | NVIDIA, shared memory |
|---|---|---|---|---|
| Initial grey cover | 3,600 pixels per eye | 3,600 per eye | 3,600 per eye | 3,600 per eye |
| Yellow repaint at present 50 | 3,600 pixels per eye | 3,600 per eye | 3,600 per eye | 3,600 per eye |

The cover's bounding box and the moving marker's position match between views in all eight rows.
The same repaint has zero yellow pixels in each view on +stereo3d2, on both cards with glamor on and off.
The 44 top-level controls of ORDER 561 all retain their expected results: pairs while declared and a whole flat view after undeclaring.
Without glamor OpenGL runs on the software renderer; with glamor the GLX clients identify radeonsi on AMD and zink on the NVIDIA card.

The final installed packages repeat all 52 child and top-level rows with the same results; the source-only runs are kept separately.


## EGL X11 and the Vulkan stereo layer

Measured on ORDER 561b from the apt-installed Mesa +stereo3d23 and Xwayland +stereo3d3 packages; the older-server control uses the retained +stereo3d5 binary.
The installed checks repeat 40 EGL transition rows, ten packed Vulkan transition rows, four injected requests per API, two exact one-frame Vulkan requests, and four Vulkan Xlib rows.
Record the actual loaded libraries and their hashes; a prototype package version can be identical to the final version.
The state transition rule is now one `u_stereo_pair` helper for GLX, EGL and the packed Vulkan layer: two copied pairs withdraw the declaration, three consecutive single-view flips allow a retry, and a successful pair clears the problem.
A first copy alone is not a failure.
Each library keeps its messages under its own package (`libglx-mesa0`, `libegl-mesa0`, `mesa-vulkan-layer-stereo`), with the same ten translations and the shared engine transport.

### Recipe

Run the following from the `native-linux` skill folder inside a fresh isolated proof-rig session, never on the person's display.
The EGL client needs EGL, OpenGL and X11 development files; the Vulkan client needs the Vulkan, XCB and X11 development files and the matching installed stereo layer.
The injection helper also needs the XCB Present development header.

```sh
cc -O1 -Wall -o /tmp/egl-covered scripts/egl-x11-covered.c -lEGL -lGL -lX11
cc -O1 -Wall -o /tmp/vk-covered scripts/vk-x11-covered.c -lvulkan -lxcb -lX11
cc -shared -fPIC -Wall -o /tmp/present-inject.so scripts/x11-present-inject.c -lxcb -ldl
```

1. With a window 800 by 600, draw 70 frames and hold the last (`FRAMES=70 HOLD_S=30`).
   The EGL client has a plain child cover by default; `COVER_AT=-1` removes it.
   For Vulkan use `TOPLEVEL=1` for the copied-present test and `UNCOVERED=1` for its uncovered control.
   Record the renderer or Vulkan physical-device name; `VK_VENDOR=0x10de` explicitly selects NVIDIA.
2. Capture both views and run `check-pair-flat-split.py --child grey` for a cover, `--child yellow` after `CHILD_PAINT_AT=50`, or `--child none` when uncovered.
   A complete pair has red only in the left view, blue only in the right, centred green rectangles, equal 40-pixel moving markers and the 60 by 60 cover at the same place in both views.
3. Repeat on the older server.
   A covered pair becomes one complete left view and a kept problem in the library's package.
   `UNCOVER_AT=40` must restore the pair and end that problem; `STILL_AT=2` checks a program that draws only once.
   With EGL, `READBACK_GLFIRST=1` also checks that the first left and right GL buffers really contain red and blue before the swap.
4. For offset and wrong-size controls, preload the helper into the uncovered client and set `X_OFF=40` or `SRC_W=700`.
   Require `inject Present` in stderr, which proves a request was changed.
   The helper modifies the packed request and leaves the single-view probe unchanged.
   Use the classifier's `--loose` for these deliberately shifted or cropped frames; compare both eye positions and marker widths, not a centred-green prediction for an ordinary frame.
5. In the Vulkan case repeat with `XLIB=1`; XCB and Xlib use the same completion rule.
   Check the loaded layer in the process's maps, not just a package version or an advertised array-layer count.

| Route | New Xwayland, covered | Older server, covered | Older server after uncovering |
|---|---|---|---|
| EGL DRI3, radeonsi | Pair, cover in both views | Left view, told | Pair, problem ended |
| EGL DRI3, zink on NVIDIA | Pair, cover in both views | Left view, told | Pair, problem ended |
| EGL software, with either card in the rig | Pair, cover in both views | Left view, told | Pair, problem ended |
| Vulkan layer, NVIDIA with DRI3, XCB and Xlib | Pair, cover in both views | Left view, told | Pair, problem ended |
| NVIDIA one-layer Vulkan WSI without DRI3 | No working pair in the baseline | No copied-present completion to check | Refused up to +stereo3d24; a pair from +stereo3d25 ([below](#a-vulkan-pair-without-dri3-the-layer-and-lavapipe)) |

The new-server pair and older-server left-view checks include one-frame programs.
The request-injected offset and wrong-size rows pass for EGL DRI3 and the NVIDIA layer; the baseline layer on the older server splits those same changed requests.
A native Mesa WSI that already exposes two array layers bypasses the packed layer; the AMD DRI3 pair is a separate positive control, not evidence for a copied-present check in native WSI.

For a multiarch installation, repeat the library's command route with real 32-bit clients, not an environment variable on a 64-bit executable.
Build these same EGL and GLX probes with `cc -m32` and matching development libraries; verify `ELF32` with `readelf -h`.
In an isolated Xvfb session use `ANNOUNCE_STEREO=5 COVER_AT=-1 READBACK=1 REPORT=1`, one EGL frame and eight GLX frames.
Both must withdraw the declaration, read red/green/red across the complete left view and keep a problem under their own package.
Trace `execve` to confirm the engine command when its private ELF64 library cannot load into the client.
This passed from the matching +stereo3d23 amd64/i386 packages; the container has no system journal, so the engine record and command were checked, not journal or notification delivery.

### Traps found by these clients

- **A package verifier rejects architecture-specific HR paths despite matching content hashes.**
  Cause: Lean Code deliberately places the authored-text archive below `usr/share/dpkg-stereo/hr/PACKAGE/amd64/` or `i386/`.
  Fix: compare every common file, then match the corresponding architecture-labeled HR paths and compare their mode and archive bytes too; retain each architecture's LC record under its own name.
  How found: the first comparison stopped on equal-named content hashes under the two directories. The counterpart check found all three HR archives byte-identical; all 626 common files in the 25 package pairs matched. The existing amd64-only gfxstream ICD was checked against the earlier package rather than silently exempted.

- **EGL reports an 800-pixel view, but the moving marker is 80 pixels wide and each view is clipped.**
  Cause: the DRI3 EGL size hook updated the EGL query width but left the loader's packed buffer only one window wide.
  Fix: retain the logical EGL width and allocate two view widths in the DRI3 loader, as GLX does.
  How found: the queried 800 by 600 extent against the captured marker and green rectangle; the software route was a complete pair and exposed the difference.
- **EGL receives copied completions but never withdraws its declaration.**
  Cause: the DRI3 surface's common drawable XID was unset, so the completion handler queried geometry of XID zero.
  Fix: initialize that drawable alongside the loader drawable.
  How found: no transition despite a split capture; tracing the callback's geometry query found the missing XID.
- **The first EGL software left view is black, with no OpenGL error; selecting the right draw buffer loses it.**
  Cause: before stereo was active the eager two-view width helper halved the left view, then first activation resized and discarded it.
  Fix: activate software stereo on demand as GLX does, keeping the view width unchanged while the first right buffer is added.
  How found: `READBACK_GLFIRST=1` returned black then blue before the first swap; after the fix it returns red then blue, and the one-frame package test changes from red to green.
- **EGL software stays flat after uncovering, while GLX restores the pair.**
  Cause: an 800-pixel single view arrived in a padded 832-pixel software buffer; the actual Present pixmap retained the padding and could never flip.
  Fix: clip the pixmap to the logical single-view width while flat, not merely to two view widths.
  How found: logging the transfer width and stride next to the completion mode; an exact 800-pixel pixmap gets three flips and recovers.
- **A Vulkan wrong-size request is told as flat but still shows blue pixels.**
  Cause: the one-layer downstream buffer still held the right view after withdrawing the declaration.
  Fix: while flat put only left-view pixels in both halves of that downstream buffer.
  How found: the injected request copied the right view's leading pixels into the ordinary window; the same probe has no blue after the fix.


- **A one-frame Vulkan wrong-size present withdraws its declaration but still contains right-view pixels.**
  Cause: the ordinary X window already contains the copied mixture, so copying that window cannot recover its left view; repacking the next application frame does nothing for a program that stops drawing.
  Fix: before `QueuePresent` returns, copy the retained left shadow image into a window-sized mono Present pixmap, without resizing it. Repeat this transfer only while flat. Keep the native swapchain handles and both shadow views.
  How found: `FRAMES=1 SRC_W=700` through the wire injector left 58,400 blue pixels. The fixed view has exactly 358,400 red, 120,000 green and 1,600 white pixels, zero blue, and one 40 by 40 marker in an 800 by 600 window.
  Prefer cached host memory for that transfer, and copy the uploaded pixels into the final pixmap before presenting; confirm three mono flips and recovery after uncovering. Honor the requested alpha mode on ARGB visuals: opaque stays opaque and post-multiplied colours are premultiplied for X11. Test alpha modes and 8-bit, 10-bit and half-float channel packing separately; the captured runtime row used an 8-bit X11 visual.


## A Vulkan pair without DRI3 (the layer and lavapipe)

Learned on ORDER 623 (November 2026), on Stereo KWin +stereo3d54, Xwayland 24.1.15 +stereo3d3 and Mesa `26.1.6-1+stereo3d24` and `+stereo3d25`.
The result first: from Mesa `+stereo3d25` a Vulkan program that asks for two image layers in its own X11 window gets its pair on an X server without DRI3, through the Vulkan stereo layer on NVIDIA's driver and through Mesa's own presentation on lavapipe.
Up to `+stereo3d24` the layer refused the swapchain (`VK_ERROR_FEATURE_NOT_PRESENT`, the program ended) and lavapipe's first present returned `VK_ERROR_OUT_OF_DATE_KHR` (the program ended), and nothing told the person.
radv cannot present on such a server at all ("No DRI3 support detected - required for presentation"), one layer or two: not a stereo loss, unchanged.

### What the drivers do without DRI3 (measured)

| Driver | How the picture reaches the window | A swapchain of another size than the window | The window resized after the swapchain was made |
| --- | --- | --- | --- |
| NVIDIA's (615.71.09) | one core `PutImage` of the whole swapchain image into the window per present, a `GetGeometry` each present; no MIT-SHM, no Present, so no completion to read | accepted, every present `VK_SUCCESS`; the window keeps what fits | `VK_ERROR_OUT_OF_DATE_KHR` at the first present after the change |
| lavapipe (Mesa's `x11_present_to_x11_sw`; MIT-SHM is used only with DRI3) | `PutImage` of the swapchain image into the window | `VK_ERROR_OUT_OF_DATE_KHR` at every present: the extent is compared with the window | the same |
| radv | none | | |

So a picture of both views is whole only in a window two views wide.
A declaration of version 4 keeps the window one view wide (the route of the DRI3 path, where a pixmap twice as wide is presented and flipped), so neither driver could carry a pair there.

### The route as built (Mesa patch 0041)

- Stereo KWin makes a top-level window it manages, declared full side by side without `_KDE_NET_WM_STEREO_CONTENT_VERSION` 4 (version 3, the default), twice as wide, and sends the program a synthetic `ConfigureNotify` of one view (KWin's `testStereoContentDeclarationOneEyeWide`: 100 wide becomes 200).
- Without DRI3 the layer and Mesa's X11 presentation declare the window that way and make the driver's swapchain of both views once the X server reports the window two views wide: "With Xcb, minImageExtent, maxImageExtent, and currentExtent must always equal the window size" (Vulkan, `VK_KHR_xcb_surface`).
  They wait only for a mapped window, at most `MESA_STEREO_DOUBLING_WAIT_MS` (1000 by default, 0 for not at all), polling the geometry every 10 ms, as the gl-stereo layer waits (`GL_STEREO_DOUBLING_WAIT_MS`).
- The program keeps working in one view's size: the surface's extents are halved while the window is two views wide, the size the compositor's synthetic `ConfigureNotify` gives.
- A doubling that comes later (KWin busy, or a window not mapped yet) is legal. Measured with KWin held still (SIGSTOP) from 0.4 to 4 s after the program started: the layer's swapchain of both views is made at the doubled width after the one-second wait anyway; NVIDIA's `PutImage` shows the left view while the window is one view wide and the whole pair once it is two, with every present `VK_SUCCESS` (NVIDIA answers out of date only when the window changes away from the extent); lavapipe's software path is out of date at each present until the window is two views wide, so a program that makes its swapchain again on `VK_ERROR_OUT_OF_DATE_KHR` (as programs must) gets the pair once KWin catches up (three remakes in that row). A resize by the person makes the swapchain out of date, as for any X11 window.
- A swapchain of one view after a pair withdraws the declaration, waits for the window to be one view wide again, then is made at that size: vk-views' two, one, two, one never sees `VK_ERROR_OUT_OF_DATE_KHR`.
- A child window, an override-redirect window, or any window under a compositor that announces less than 3, is not made wider. There the layer offers `maxImageArrayLayers` 1 (the driver's), and a program that asks for two anyway is refused with `VK_ERROR_FEATURE_NOT_PRESENT` and the person is told: package `mesa-vulkan-layer-stereo`, key `one-view:vulkan:DEVICE` (the device's name with every character outside letters, digits and `_@+-.` made `_`), message `LOCAL4` with the program, the device and Mesa's own words (title `LOCAL3`), in the ten languages; a pair of that device shown later, on any route, ends it. lavapipe offers one layer there too and has no message of its own.
- The helpers are `src/util/u_x11_stereo_doubled.h` (has DRI3, why a window is not doubled, declare for doubling, the wait), shared by `stereo_layer.c` and `wsi_common_x11.c`; the problem transport gained `u_stereo_problem_keep_args()` for a message of three or four arguments.
- Credits, from Mesa's own records: lavapipe's software presentation is Dave Airlie's ("vulkan/wsi: add sw support", 8004fa9c, 2020) and its out-of-date answer to a resize Hans-Kristian Arntzen's (merge request 28413, 2024); the route was planned by lane 583 from lane 573's findings.
- No Present completion exists on this route, so the copied-pair rule (`u_stereo_pair`, patches 0038 and 0039) does not run there; the window's own pixmap holds both halves and Xwayland +stereo3d5 hands it over whole.

### Recipe: the rows as scripts

All rows run in the fresh-session rig of [stereo-proof-rig](../../stereo-proof-rig/SKILL.md) with `XWAYLAND_NO_GLAMOR=1` in KWin's environment and the output in its side-by-side 3D mode; a development build of `libVkLayer_MESA_stereo.so` and `libvulkan_lvp.so` is mounted over the installed ones to prove a change before a package build (the two targets of a Mesa tree configured with `-Dvulkan-drivers=swrast -Dgallium-drivers=llvmpipe -Dvulkan-layers=stereo -Dglx=disabled -Degl=disabled -Dgbm=disabled`, about ten minutes at six processors from cold, seconds after a change).

1. **What the driver sends:** [`scripts/vk-extent-probe.c`](../scripts/vk-extent-probe.c) under `xtrace -n -d $DISPLAY -D :9 -o trace.txt --` (Debian's `xtrace`), with `EXT_W=1600` on an 800 wide window and with `RESIZE_AT=30 RESIZE_W=1600`; count the requests with `grep -o 'Request([0-9]*): [A-Za-z]*' trace.txt | sort | uniq -c`.
2. **The pair and the sequence:** [`vk-views`](../../stereo-proof-rig/scripts/vk-views/README.md) with `X11=1 PHASES="2:4,1:4,2:4,1:0"`, `OLD=1` and `OLD=0`, captures at 3, 7, 11 and 15 s: `PAIR FLAT PAIR FLAT`, declarations `3 0 3 0`, the program alive at the end.
3. **The geometry and every frame:** [`scripts/vk-x11-covered.c`](../scripts/vk-x11-covered.c) with `TOPLEVEL=1 UNCOVERED=1` (and `XLIB=1`), captures at 3, 4, 5 and 6 s, read by [`scripts/pair-geometry.py`](../scripts/pair-geometry.py): each eye one 800x600 window at the same place, red left and blue right with no colour of the other view, the green rectangle centred, the 40 px marker at the same place in both eyes and at another place in each capture.
4. **Told, then ended:** [`seq-x11.sh`](../../stereo-proof-rig/scripts/vk-views/seq-x11.sh) with `NOGLAMOR=1 SEQ="vk-extent-probe|CHILD=1 LAYERS=2;vk-x11-covered|TOPLEVEL=1 UNCOVERED=1;vk-extent-probe|CHILD=1 LAYERS=2"` and `LANGS="pt_BR de ja"`: the problem kept, gone, kept again; a second refusal by the same program leaves it at generation 1.
5. **A late doubling:** the probe with `LAYERS=2 RECREATE=1` (both views, the swapchain made again on `VK_ERROR_OUT_OF_DATE_KHR`) while KWin is held still from 0.4 to 4 s after the program starts (`kill -STOP` and `kill -CONT` of the compositor's process in the session), captures at 6 and 8 s: a pair on NVIDIA and on lavapipe.
6. **What must not change:** lane 573's vk-views rows with glamor on radv, NVIDIA and lavapipe, Wayland and X11, both orders, compared pixel for pixel between the old and the new build; a one-layer vk-views without DRI3 the same; vkcube resized twice from outside ([`scripts/x11-resize.c`](../scripts/x11-resize.c) `"Vkcube X11" 900 700`, then `500 400`) with and without DRI3, its window drawn at the new size and the same in both eyes; radv without DRI3 as before.

### Traps

- **Symptom:** NVIDIA's rows on Wayland end at once with `vkCreateInstance ... failed: -9` while its X11 rows pass.
  **Cause:** the client's EGL vendor list named Mesa's only; NVIDIA's Vulkan driver does not start without its own EGL vendor (on X11 it starts through GLX).
  **Fix:** give NVIDIA's client its own EGL vendor (`__EGL_VENDOR_LIBRARY_FILENAMES` with `10_nvidia.json`).
  **How found:** the same rows by protocol: X11 passed, Wayland failed at instance creation, and this skill's rig page already said it.
- **Symptom:** `check-pair-flat-split.py --child none` says SPLIT for a correct top-level pair.
  **Cause:** KWin's title bar icon has grey pixels, which the classifier counts as a child window.
  **Fix:** for a top-level, check the window against a prediction (`pair-geometry.py`); look at one capture before trusting any label.
- **Symptom:** a refusal row never refuses: the client asserts `maxImageArrayLayers == 2` and stops before asking.
  **Cause:** where the layer cannot give two it now offers one, and `vk-x11-covered` asserts on the capability.
  **Fix:** `vk-extent-probe CHILD=1 LAYERS=2` asks for two whatever the capability says, as a program that asks anyway does.
- **Symptom:** a resizer that looks for vkcube's window by `WM_NAME` finds nothing, and the resize rows pass without resizing anything.
  **Cause:** vkcube names its window only through `_NET_WM_NAME` (UTF8_STRING), and the name is `Vkcube X11`, not `vkcube`.
  **Fix:** read `_NET_WM_NAME` too, use the name `xwininfo -root -tree` prints, and print the window's size after each resize, so a row that did nothing says so.
- **Symptom (the old note):** "lavapipe returns `VK_ERROR_OUT_OF_DATE_KHR` once Stereo KWin doubles the declared window".
  **Cause, measured:** lavapipe's first present is already out of date: its extent is two views wide and a version-4 window stays one view wide, and the software path compares the two at every present.
  **How found:** reading `x11_present_to_x11_sw()` and the red row's first present.
- **Symptom (the old refusal's reason):** "the one-layer WSI's packed buffer is clipped to the left view".
  **Cause, measured:** the clip is the window's width: NVIDIA's `PutImage` carries the whole image, and the window was one view wide because the declaration kept it so.
  **Fix:** the window's width (version 3), not a refusal.
- **Symptom:** `apt-get update` in an image made from an older rig stops at `sqv ... Missing key A401FF99368FA1F98152DE755C808C2B65558117` for deb-multimedia.
  **Cause:** the image's keyring predates deb-multimedia's current signing key.
  **Fix:** set that source aside for a step that needs nothing from it, or install the current `deb-multimedia-keyring`; never sign with a key you did not check.

## What this does not cover

- The covered declared child is fixed and repeated from the installed packages [above](#a-declared-child-covered-by-a-child-of-its-own). Native WSI that bypasses the packed layer has only the positive controls described above; its copied-present recovery is not qualified here.
- A declared window that a compositor did not redirect and that is smaller than its surface (a stereo child the window does not list) is still copied into its parent's picture: it shows the left view, flat, and Mesa says so ([above](#when-the-pair-cannot-be-flipped)).
- **The next Xwayland base.** Upstream's stable branch after 24.1.13 (24.1.14 and 24.1.15) adds a check to `xwl_present_check_flip()` that the flip pixmap has the size of the window's pixmap ("xwayland/present: Only flip if the window pixmap dimensions match", Michel Dänzer). A window that holds two eyes has a pixmap one eye wide before its first flip, so patch 0005's exception must cover that check too when the package moves base, or the pair is copied again, with glamor as well; the suite's test (0012) and the glamor control of step 1 show it. The extended check is carried by `2:24.1.15-1+stereo3d1+lc1` (ORDER 562); both height checks remain, and an unrelated backing width is rejected.
- Each present of both eyes makes a new shared memory pool of that size (a new pixmap per swap is Mesa's software path); Xwayland's open files and memory stayed level over a fast run (11 to 12 files, about 75 MB), and 600 presents of a 1600x600 pair back to back took 10.0 s, the output's 60 a second, as with glamor.
- When Mesa takes a declaration back or brings it back, the compositor learns it from the X property and gets the new buffer through Wayland, in no fixed order: one frame between the two can show the old buffer under the new declaration.
