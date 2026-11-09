# X11 children: what X shows, what the scene must cut, and the rows that prove each route

Learned in ORDER 160, milestone 1 (November 2026), on the installed packages of release r1107a: KWin +stereo3d46, Xwayland +stereo3d4, Mesa +stereo3d17, Qt +stereo3d15, gl-stereo 0.4.2, libstereo-declare 1.8.0.

## The rule behind it

X draws a child clipped to its window and to the windows between, and a mapped sibling stacked over it hides it.
A declared child is redirected (Composite, manual), so Xwayland gives it a surface whose buffer is whole.
Stereo KWin draws that surface per eye at the child's place; unless the scene cuts it the way X would, the part of the child outside its window shows, and so does the child under a sibling.
The window's own surface, drawn below, already holds the siblings' pixels (X composites the non-redirected windows into it), so cutting the child's item is enough: the sibling shows through the hole.

## The rows (scripts/x11-child)

`x11child.c` is a 2D X window (400x300, grey) with a GLX stereo child (left eye red, right eye blue); `x11egl.c` does the same with an EGL two-view window surface (`EGL_EXT_multiview_window`); `x11vk.c` with the Mesa stereo layer and a two-layer swapchain.
`run.sh MODE EVDIR` starts a fresh Stereo KWin (`--virtual --xwayland`), runs the client, captures both eyes with ScreenShot2, reads the declarations from the X tree, and `child_clip_analyze.py` measures:

| Mode | What it sets up | Row that must pass |
|---|---|---|
| `plain` | the child fully inside the window | each eye shows its colour over the whole place; the child is listed in the window's `_KDE_NET_WM_STEREO_CONTENT_CHILDREN` (control) |
| `overflow` | the child 150 px wider and 100 px taller than the room it has | no child pixel outside the window's rectangle, in either eye |
| `sibling` | a plain X window mapped after the child, over part of it | the sibling's green is visible over the child in both eyes |
| `mono-sibling` | the same with a mono GLX child | the 2D control: the sibling stays visible (capture one output wide) |
| `egl-plain`, `vk-plain` | the EGL and Vulkan routes | declared, listed, two outputs wide |
| `gls` | gl-stereo's `LD_PRELOAD` layer over NVIDIA's own OpenGL (`GLXV=nvidia`, `GL_STEREO=1`) | declared, listed, two outputs wide |

Results on r1107a (each FAIL is a missing part, each PASS a control):

- GLX `plain`: PASS in every row (stereo capture 2048x640, 100 percent of the place in each eye, listed).
- GLX `overflow`: FAIL, 45000 child pixels per eye outside the window.
- GLX `sibling`: FAIL, green 0.000 over the child in both eyes, while `mono-sibling` shows green 1.000.
- EGL `egl-plain`, Vulkan `vk-plain` and `gls` on Mesa +17: declared (`_KDE_NET_WM_STEREO_CONTENT` 3 on the child) but not listed in the window, capture one output wide (`stereo` false), the packed buffer squeezed into the child.
  Only Mesa's GLX lists a child (`src/glx`, patches 0017 to 0019); the EGL X11 platform and the Vulkan WSI declare the window and never write `_KDE_NET_WM_STEREO_CONTENT_CHILDREN`; gl-stereo calls `stereo_declare_x11_format()` on the window it finds.

## KWin +stereo3d53: the scene cuts the child as X does (ORDER 160)

The change is `X11StereoChild::visible` and `SurfaceItemXwaylandChild::shape()`, and it is the smaller form of the draft that lane 160 left.
`visible` is in the X11 window's coordinates: the window's area, cut to the inner area of each window between the child and the window, less the bounding region of every viewable `InputOutput` window stacked above the child in its parent, or above a window between in that window's parent (`xcb_query_tree` lists bottom to top; declared children are skipped, the scene orders those).
The item's shape is cut to `visible.translated(-position())`, in the item's own coordinates, so one cut serves a child at its own size, scaled by `CHILD_PLACE`, or shown at one view's size (`ONE_VIEW_SIZE`), and a child that fits its window with nothing over it is unchanged.

### Why the cut is made on the item and not in the child's native pixels

A first form put the cut into the child's native shape (`shape` in native X pixels, which `shapeForSourceBox()` maps to the place).
It breaks the route of ORDER 265b: a program that cannot size the toolkit's child draws on a window of its own that is twice a view wide, so in native pixels the second view lies outside the parent, and a window clip kills the right eye.
X would clip that window too, but KWin shows a declared child's whole native buffer at the place the program declared; what has to be cut is what the person sees, so the cut is made in display coordinates (the window's own coordinates), where the covering window really is.
The autotests run in `normal` and `scaled2x` (`testStereoChildWindowClip`) and the shape of the item is compared in its own coordinates.

### What notices a covering window (SubstructureNotify)

A sibling that appears, moves, is restacked or goes away is announced to its parent only if the parent's `SubstructureNotify` is selected.
`watch()` selects it on each window between the child and the X11 window and adds it, with `|`, to the X11 window's own event mask (read with `xcb_get_window_attributes`: `your_event_mask` is this client's mask); `unwatch()` removes only that bit.
`Workspace::workspaceEvent()` looks at those events first (`findSubstructureParent()`: the `parent` of a CreateNotify, the `event` of the others when it differs from `window`) and hands them to `X11StereoChildren::handleSubstructureEvent()`; the events a child or a window between sends about itself keep their old route, and the same event arriving through its parent is dropped there, so nothing is computed twice.
A covering window's shape change is a `ShapeNotify` on that window, selected with `xcb_shape_select_input` and routed by `owns()`, which therefore also accepts the covering windows (`X11StereoChild::coverers`).
The area follows the X11 window's size through `bufferGeometryChanged`.

### Rows (scripts/x11-child)

| Mode | What it sets up | Row that must pass |
|---|---|---|
| `late-sibling` | the sibling is mapped 2 s after the child was listed | the sibling's green shows over the child in both eyes |
| `shaped-sibling` | the sibling is a frame (SHAPE bounding with a hole) | the frame's bars stay green and the child shows through the hole |
| `raised` | the sibling is mapped, then the child is raised over it | the child shows whole (control: nothing covers it) |
| `pointer` | `sibling`, then `fakeinput` moves the pointer over five places | each place reaches the X window under it: the X server decides, so the row guards that the cut changes nothing |

`overflow`, `sibling`, `late-sibling` and `shaped-sibling` FAIL on KWin +stereo3d52 and PASS on +stereo3d53; `plain`, `mono-sibling`, `raised` and `pointer` PASS on both (controls).
Autotests: `testStereoChildWindowClip` and `testStereoChildWindowClipAncestor` in `testX11Window`; with the call to `updateVisible()` replaced by a `return` they fail with `visible` empty.

### Running and proving the autotests

1. A build image from the published source package: `dpkg-source -x` the .dsc, `apt-get build-dep` it, and add `ninja-build xauth xvfb xwayland dbus libei-dev libeis-dev breeze mesa-utils x11-utils`; commit it as an image.
2. The source mount must be writable (KDE's git hooks write while cmake configures); configure once with `cmake -G Ninja -DBUILD_TESTING=ON ...`, then `ninja testX11Window` (the CMake `NAME`).
   About 1165 steps for a first build, an hour under load; after editing one `.cpp` a few minutes; after editing `workspace.h` or another widely included header, hundreds of objects.
3. Run as uid 1000: `setpriv --reuid=1000 --regid=1000 --clear-groups env QT_QPA_PLATFORM=offscreen EGL_PLATFORM=surfaceless XDG_RUNTIME_DIR=... dbus-run-session -- bin/testX11Window`.
   The depth tests (`testStereoDepthStack`, `Popups`, `Pinned`, `PinnedStack`, `Notifications`, `Motion`, `Wallpaper`) skip without a GPU: give the container a render node (`--device /dev/dri/renderD128 --group-add GID`) and use `--groups=GID` instead of `--clear-groups`.
4. Two reds, one per layer: replace the call to `updateVisible()` by a `return` (the `visible` comparisons fail with an empty region), and, separately, make `shapeForSourceBox()` return the uncut shape (the quad coverage of both eyes is the whole child). A test that reads `shape()` alone stays green with the second one, because the painter does not call `shape()`.

### Traps (symptom, cause, fix, how it was found)

- **The autotest is green and the rig rows are still red (child outside its window, sibling hidden).**
  Cause: the cut was made in `SurfaceItemXwaylandChild::shape()`, which the autotest compared; the eyes' quads are built from `shapeForSourceBox()`, so the painter never saw it.
  Fix: cut in `shapeForSourceBox()`, and assert the quad coverage of both eyes (`eyeQuads(StereoEye::Left)` and `Right`), as `testStereoChildShape` does.
  Found by the rows on the installed package, then `grep -n shapeForSourceBox src/scene`: the base class calls it per eye. Run the real rows on the first package, not only the autotests.
- **A client of the X11 window's own events gets `UnmapNotify` for a child and releases the window.**
  Cause: once `SubstructureNotify` is selected on the X11 window, `X11Window::windowEvent()` receives the events about its children with `event` equal to its own window, and `unmapNotifyEvent()` assumes `UnmapNotify` is about the client.
  Fix: take the events whose `event` differs from `window` in `Workspace::workspaceEvent()` before `findClient()`, never in `windowEvent()`.
  Found by reading `windowEvent()`'s switch before adding the mask.
- **The cut is correct in the rig and a program's packed child loses its right view.**
  Cause: the cut was in native pixels (see above). Fix: cut in display coordinates. Found by reading the memory line about ORDER 265b before choosing where to cut, and by the `scaled2x` row of the autotest.
- **`ninja: error: unknown target 'x11_window_test'`.** Cause: the target is the CMake `NAME` (`testX11Window`), not the source file. Fix: `ninja -t targets all | grep -i x11window`.
- **`docker run` of the build image says `pull access denied` right after the prep step printed `prep done`.** Cause: the prep script prints before `docker commit` ends. Fix: wait for `docker image inspect` before the first run.
- **`${GPU:---clear-groups}` runs a command called `1`, every test exits 127.** Cause: `${VAR:-word}` expands to `$VAR` when it is set. Fix: keep the argument in a variable of its own (`GROUPSARG=--clear-groups; [ -n "$GPU" ] && GROUPSARG=--groups=125`).
- **`ScreenShot2.Error.Cancelled: Screenshot got cancelled (36)` in the rig's capture.** Cause: the container has no render node, so the virtual KWin has no compositor to screenshot (`kwin.log` says `Failed to open drm node` and `Configured compositor not supported by Platform`). Fix: `--device nvidia.com/gpu=0 --group-add 125`, or the AMD node, as for the other rows.
- **Two rows loops write into one evidence folder.** Cause: `docker kill` of the container does not stop the `for` loop around it (a backgrounded loop started the next row at once); the second loop then ran the same rows beside the first. Fix: stop a loop by its PID, and give every loop its own `TAG`.
- **The XCB error `BadWindow ... SHAPE, minor code 6` in the autotest log is not new.** Cause: `unwatch()` of a child whose window is already destroyed (`xcb_shape_select_input` unchecked); the +stereo3d52 log of `testX11Window` has five of them. The new calls on covering windows are checked and discarded.

## Mesa +stereo3d19: EGL and Vulkan list their child

One header, `src/util/u_x11_stereo_child.h`, holds the X side: the owning window (the window below the root on the way up, as GLX takes it), a server grab around the read and write of `_KDE_NET_WM_STEREO_CONTENT_CHILDREN`, windows that are gone dropped when a child is added, the child kept while its window lives, and `_KDE_NET_WM_STEREO_CONTENT_VERSION`.
EGL's X11 platform writes VERSION 4 before the declaration (compositor version 4 or later), keeps the window one eye wide (`dri_drawable->stereo_window_one_eye`; the software path puts the packed image into a pixmap and presents it) and lists the child (version 5 or later).
The Vulkan stereo layer and the window system integration's stereo swapchain list the child; the layer writes VERSION 4 first and halves the surface width only for version 3.
EGL takes zink through DRI3 while the compositor announces stereo (kopper has no second view; GLX has done so since patch 0029).
Rows from the packages: see the hand-back of ORDER 160 milestone 2; the commands are `scripts/x11-child/run.sh egl-plain|vk-plain|plain` and `remap-inner.sh` with `KIND=egl`.

### A dev build of Mesa for the rows (minutes, not an hour)

`meson setup /b/o --prefix=/b/inst -Dgallium-drivers=llvmpipe,softpipe,zink -Dvulkan-drivers=swrast -Dvulkan-layers=stereo -Dllvm=enabled -Dplatforms=x11,wayland -Dglx=dri -Dglvnd=enabled ...` then `ninja -C /b/o install` in the Mesa build image; run a client with `LD_LIBRARY_PATH=/b/inst/lib/x86_64-linux-gnu LIBGL_DRIVERS_PATH=.../dri __EGL_VENDOR_LIBRARY_FILENAMES=/b/inst/share/glvnd/egl_vendor.d/50_mesa.json` (Vulkan: `VK_ADD_IMPLICIT_LAYER_PATH=/b/inst/share/vulkan/implicit_layer.d`, `MESA_VK_STEREO_LAYER=1`) while KWin stays the installed one.
Configure once with `-Dbuild-tests=true` before the recipe build: the layer's passthrough test compiles `stereo_layer.c` with its own include list.

### More traps

- **A recipe build fails an hour in with `util/u_x11_stereo_child.h: No such file or directory` in `stereo-layer-passthrough-test`.** Cause: the dev build had tests off, and the test target in `src/vulkan/stereo-layer/meson.build` has its own `include_directories`. Fix: add `inc_src` there too. Found in the build log (`grep -n FAILED`).
- **The Vulkan rows show red in both eyes on a capture one output wide.** Cause: the client's command pool lacked `RESET_COMMAND_BUFFER_BIT` while it recorded the same buffer every frame (fix the client), and with the child not listed the compositor shows the packed buffer as one picture. With the child listed (Mesa +19) lavapipe and NVIDIA's Vulkan driver both give red and blue.
- **A zink EGL stereo window shows the left view in both eyes on the RTX 3060.** Cause: kopper. Fix: `LIBGL_KOPPER_DISABLE=1`, or Mesa +19, which chooses DRI3 itself.
- **A Qt test binary built from a tree stops at `Could not find the Qt platform plugin "xcb"`.** Cause: `cmake --build --target tst_...` builds no plugin. Fix: build `QXcbIntegrationPlugin` and `QXcbGlxIntegrationPlugin` and set `QT_PLUGIN_PATH`.

## The raw GLX unmap/remap growth

`remap-inner.sh` runs `glx-remap-metrics.c` (from the open-sims lane): a 640x480 GLX stereo window, unmapped and mapped once.
With KWin announcing declaration version 4 or later the widths stay (GLX 640, native 640 on both sides of the remap): the window is one eye wide and the buffer holds both eyes.
Negative control, `CTRL_SUPPORT=3` (the root's `_KDE_NET_WM_STEREO_CONTENT_SUPPORTED` set to 3, the doubling route): native 640 then 1280 before, GLX 1280 and native 2560 after, the growth the lane saw on KWin +stereo3d22.
The EGL reproducer (`egl-remap-metrics.c`, `KIND=egl`) failed the same way on Mesa +17 (surface 640, native 1280 before, 1280 and 2560 after) and holds 640 and 640 with +19. A program that doubles its own window (the gl-stereo layer) still takes the doubling route; try the remap on it before calling the growth closed.

## Traps (symptom, cause, fix, how it was found)

- **The client's declaration is missing and the capture is one output wide, with `glx: failed to create dri3 screen` and `failed to load driver: nvidia-drm` in the client's stderr.**
  Cause: Xwayland's DRI3 device is the NVIDIA card (CDI), and Mesa's GLX cannot use it.
  Fix: `CLIENT_SW=1` (llvmpipe) for the Mesa client; KWin keeps the card.
  Found in `app.err`, then `props.json` showed no `_KDE_NET_WM_STEREO_CONTENT` on any window.
- **`capture.py` stops with `No module named 'gi'`, or `x11_props.py` with `No module named 'Xlib'`.**
  Cause: the proof-rig images carry neither `python3-gi` nor `python3-xlib`; a conda `python3` first in the path hides the system one.
  Fix: install both into a derived image (apt over https, `docker commit`), and call `/usr/bin/python3`.
- **The Vulkan client asserts `maxImageArrayLayers == 1` or `== 2`.**
  Cause: the stereo layer is a separate package (`mesa-vulkan-layer-stereo`), off until `MESA_VK_STEREO_LAYER=1`, and it reads the root's support version; Mesa's own test sets the version itself and would overwrite KWin's.
  Fix: unpack the layer's `.deb`, `VK_ADD_IMPLICIT_LAYER_PATH` to its `implicit_layer.d`, `LD_LIBRARY_PATH` to its library folder, `MESA_VK_STEREO_LAYER=1`, and leave the root property alone.
- **The EGL client gets NVIDIA's EGL and no second view.**
  Cause: CDI adds NVIDIA's vendor file first.
  Fix: `__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json`.
- **A row passes for the right eye on a one-output capture.**
  Cause: a mono capture is compared in both halves.
  Fix: read the first row (`capture is stereo`) first; a FAIL there makes the eye rows meaningless.
- **Sweet Home 3D, CloudCompare, GRASS or KiCad cannot be installed in the rig image.**
  Cause: the edition's libheif1 (+stereo3d2) needs `libaom3 (>= 1:3.15.2)` through `libheif-plugin-aomdec`, which Debian testing does not have; `apt-get -s` lists it as uninstallable.
  Fix: add deb-multimedia (the host's `sparky-stereo-deb-multimedia.sources`, its keyring, the `sparky-stereo-only-ours` pin); then 58 (CloudCompare), 86 (Sweet Home 3D), 100 (GRASS) and 122 (KiCad) packages install in simulation.
  Found with `apt-get -s install --no-install-recommends PROGRAM`.

## How each program creates its GL child (from the lane records of ORDER 142 and the CAD survey; not yet run on this release)

- **KiCad 10**: the 3D viewer is a wxWidgets `wxGLCanvas`, a child X window of the viewer frame (GTK 3 on X11); stereo is the program's own `GL_STEREO` context, our patch draws each eye in its buffer.
- **GRASS 8.5 NVIZ**: wxPython's `GLCanvas`, a child X window, with our two patches (the eye loop in ogsf and the wxGUI draw).
- **CloudCompare 2.13**: `ccGLWindow`, a Qt `QOpenGLWindow` placed in a widget (`QWidget::createWindowContainer`), so a native child; "Generic stereo display" asks the quad buffer.
- **Sweet Home 3D 7.5**: Java 3D's `Canvas3D`, a heavyweight AWT child; `-Dj3d.stereo=REQUIRED` asks for a stereo visual.
All four rely on the child being listed; the first row for each is: start with the stereo option on, read `_KDE_NET_WM_STEREO_CONTENT_CHILDREN` of the top-level, capture, and compare with the same program in 2D.
