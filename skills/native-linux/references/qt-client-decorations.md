# Qt's own window frame around a stereo window (Wayland)

Qt draws a client-side decoration (CSD) when the compositor offers no server-side one.
A stereo OpenGL window may keep that frame: the frame needs no stereo of its own, it is the same picture in both eyes at screen depth, and only its storage needs care.

## The two routes

- **(a) The frame is drawn twice into the window's own buffer (what the edition ships, patch `stereo3d-wayland-egl-eye-slots`).** A decorated `QWaylandEglWindow` renders its content into a content framebuffer object and blits it, with the frame, into the window surface from a second context. The patch gives that object a colour attachment per eye, makes `QRhiGles2` draw the right eye of the default framebuffer into the second one, and runs the blit from a desktop-GL context that copies each slot into `GL_BACK_LEFT` and `GL_BACK_RIGHT` and draws the frame identically into both. The content keeps each eye at its rendered size and the declaration stays one.
- **(b) The frame stays on the window's 2D surface and the GL content moves to a declared subsurface.** KWin shows the declared surface per eye and copies everything outside it to both. Not built: (a) was smaller in Qt's code and is proven. It would also cover a raw window, see the trap below.

Do not drop the frame for stereo windows (the first patch, `no-csd-stereo-window`, did): a person who runs a stereo program under a compositor without server-side decorations then gets a window without a title bar or buttons.

## Recipe (headless, GPU through CDI, Mesa for the client)

1. Image: the shared proof rig image, its container started with `--device nvidia.com/gpu=0 --group-add <render gid>` (KWin's virtual output opens the NVIDIA render node). The AMD iGPU is never given.
2. KWin without a decoration plugin: `kwinrc` with `[org.kde.kdecoration2]` `NoPlugin=true`, and `QT_WAYLAND_DISABLE_WINDOWDECORATION` unset, so Qt decorates.
3. The client must use Mesa's EGL, the only one with `EGL_EXT_multiview_window`: `__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json __GLX_VENDOR_LIBRARY_NAME=mesa LIBGL_ALWAYS_SOFTWARE=1`.
4. A `QOpenGLWidget` with `QSurfaceFormat::setStereo(true)` clearing red in the left target and green in the right one; capture the window through ScreenShot2 (`stereo=true`, twice the width).
5. Expect: red in the left half, green in the right half, the frame's bounding box the same in both, 0 differing pixels outside the content box. The check script compares the halves outside the content box.

## Traps

- Symptom: `stereo=0` in the client's own log and a mono capture, with the compositor on the NVIDIA card. Cause: glvnd offers NVIDIA's EGL first, which has no multiview window. Fix: the Mesa vendor file variables above. Found by: the client's `context stereo=` line and `stereo=false` in the capture log.
- Symptom: every ScreenShot2 capture is `Cancelled`. Cause: KWin got no render node (no `--device`). Fix: give the container the NVIDIA node and its group. Found by: `Failed to open drm node` in KWin's log.
- Symptom: a raw `QOpenGLWindow` that calls `glDrawBuffer(GL_BACK_LEFT/RIGHT)` itself gets `GL_INVALID_OPERATION` (0x502) and draws nothing, under Qt's own frame only. Cause: with a frame the default framebuffer object is the content FBO, and `glDrawBuffer` with a left/right back-buffer name is invalid on a user FBO. Every RHI user (QOpenGLWidget, Qt Quick, Widgets) is unaffected because the RHI picks the slot. Not fixed; the options: accept it (it breaks only where no server-side frame exists), or draw straight into the surface and copy each eye plus the frame at the swap (needs another change and breaks partial updates of the default framebuffer). Found by: the raw case's `glGetError` after the call.
- A Debian control for the 2D cases is installed by version: Debian testing's qt6-base moves (-5 was gone by 2026-11-07, -7 was current); ask `apt-cache policy` and install each qt6-base binary at that version, removing the edition's pin file first.
