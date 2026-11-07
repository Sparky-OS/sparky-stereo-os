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
