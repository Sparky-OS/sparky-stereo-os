# A client rendering on a GPU other than the compositor's (Wayland, dmabuf)

Symptom first: the program dies at start, or on its first frame, with `Wayland protocol error: [destroyed object]: error 7: importing the supplied dmabufs failed` (`zwp_linux_buffer_params_v1`, `invalid_wl_buffer`), and the compositor's own log is quiet.
It happens on a hybrid machine when the program is routed to the discrete GPU (render offload) while the compositor draws on the integrated one.
The same program started on the compositor's GPU works.

## Recipe: reproduce it in containers

1. KWin on one GPU, the client on the other, in two containers that share one `XDG_RUNTIME_DIR` folder (`--virtual --socket=wl-test`).
   One container with both render nodes cannot do it: KWin's EGL picks the first GBM device it finds (the NVIDIA node) and `eglInitialize` fails with `DRI2: gbm device using incorrect/incompatible backend` when Mesa's vendor file is forced.
   Give the KWin container only the AMD node (`--device /dev/dri/renderD128 --group-add render`), the client container the NVIDIA CDI device and the same AMD node.
2. Client environment as the Performance profile sets it: `__GLX_VENDOR_LIBRARY_NAME=nvidia __NV_PRIME_RENDER_OFFLOAD=1 __VK_LAYER_NV_optimus=NVIDIA_only VK_LOADER_DRIVERS_SELECT=*nvidia*`.
   Control: `DRI_PRIME=pci-0000_0b_00_0 __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/50_mesa.json __GLX_VENDOR_LIBRARY_NAME=mesa` (the compositor's GPU).
3. `WAYLAND_DEBUG=client` on the client shows `zwp_linux_buffer_params_v1.add(fd, plane, offset, stride, modifier_hi, modifier_lo)` then `create_immed(...)` before `wl_display.error(nil, 7, "importing the supplied dmabufs failed")`.
   Join the two modifier halves: `0x0300000000e08014` is NVIDIA block linear (vendor byte 0x03); AMD's start with 0x02.

## Cause (how it was found)

The compositor's `zwp_linux_dmabuf_feedback_v1` is right: `main_device` is the AMD node and every tranche lists AMD tiled modifiers, LINEAR (0) and INVALID (implicit).
The client allocated its buffers by exporting an EGLImage from its own GL texture (Gecko `DMABufSurfaceRGBA::CreateExport`, `MOZ_LOG=Dmabuf:5` prints `created ... modifiers 300000000e08014`), so the NVIDIA driver chose its own block-linear modifier, which is not in any tranche.
The protocol says buffers for the main device are importable by the compositor; a modifier of another GPU is not (linux-dmabuf-v1, `zwp_linux_dmabuf_feedback_v1.main_device`, `tranche_formats`).
The client never compared the compositor's `main_device` with its render device (Gecko's handler for it was an empty comment, "We're getting DRM device from GL", still so on mozilla main).

## Fix

Test each buffer's own (fourcc, modifier) against what the compositor advertised, never the GPUs against each other: a Mesa hybrid advertises the discrete GPU's tiling too and must stay zero-copy.
Gecko `DMABufCompositorCanImport` reads the formats and modifiers of the default feedback (an implicit INVALID modifier is left as it was).
A render layer whose buffer fails the test is copied to a `wl_shm` buffer before it is attached (`NativeLayerWaylandRender::CopyToSharedMemoryLocked`); a hardware decoded picture that fails it (NVDEC's NV12 modifier 0x300000000606014) is not promoted to a layer of its own, the compositor-side renderer draws it into a render layer.
Proof of no copy on Mesa: count `wl_shm_pool.create_buffer` in `WAYLAND_DEBUG=client` (3 at start with the compositor on the same GPU, 2022 in 25 s when every frame is copied) and `MOZ_LOG=Dmabuf:5` prints `DMABufCompositorCanImport(): format ... modifier ... -> 0 or 1`.
Cost measured: `glReadPixels` BGRA of a 4K frame takes 4.5 ms median on an RTX 3060 (1080p 1.2 ms), about 7 GB/s.

What does not work, measured with `gbm_bo_create*` and an EGLImage on the NVIDIA node: `GBM_BO_USE_RENDERING` together with a modifier list fails; a LINEAR buffer is made with `GBM_BO_USE_LINEAR` alone or with the modifier list `[0]` and no flags; but an imported linear dmabuf is not a renderable target (framebuffer status `GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT`, 0x8cd6).
So "allocate with the compositor's modifiers through GBM" cannot work on NVIDIA; the GPU has to draw into its own tiling and a copy goes to the compositor.
Without native layers (`gfx.webrender.compositor` false) the driver's own EGL Wayland platform does the cross-GPU copy and the window works, but no layer is declared, so a 3D video is shown flat.

## Hardware decoding on the NVIDIA GPU in a container

`nvidia-vaapi-driver` (Debian) is not in the bench image and `apt-get install` fails on unmet dependencies there: `apt-get download nvidia-vaapi-driver libgstreamer-plugins-bad1.0-0 libgstreamer1.0-0 libgstreamer-gl1.0-0 libgstreamer-plugins-base1.0-0`, `dpkg -x` into a folder, mount it at `/opt/nvd` and set `LD_LIBRARY_PATH=/opt/nvd LIBVA_DRIVERS_PATH=/opt/nvd/dri LIBVA_DRIVER_NAME=nvidia NVD_BACKEND=direct MOZ_DISABLE_RDD_SANDBOX=1` plus the prefs `media.ffmpeg.vaapi.enabled`, `media.hardware-video-decoding.force-enabled`, `media.rdd-ffmpeg.enabled`.
A `ctypes` `vaInitialize` on `/dev/dri/renderD129` proves the driver loads ("VA-API NVDEC driver [direct backend]", profiles 0 to 28) before the browser is blamed.
The browser log then says `Using preferred hardware codec h264` and `VAAPI locking dmabuf surface`; `IsHardwareAccelerated=false` means the driver did not load.
Without the per-pair test the package dies at the first decoded frame with the same error 7 (also with the compositor on a software renderer).

## Trap: the fix for the crash took the WebGL canvas out of its layer (360 video doubled, VR crashed)

Symptom: with the per-pair test in place, on the discrete GPU route a 360 video on YouTube draws twice in one view (the stereo canvas shown whole, undeclared: no `kde_stereo_content_v1.set_content(3)`, eyes identical) and a WebXR "Enter VR" ends the browser with `importing the supplied dmabufs failed`; the same pages work on the compositor's GPU.
Cause, two parts: (1) a WebGL canvas reaches the compositor as an external dmabuf layer that carries the stereo mark; not promoting it (the rule that is right for a decoded YUV picture) drops the layer and the declaration; (2) `NativeLayerRootWayland::BorrowExternalBuffer` makes the `wl_buffer` (the `create_immed` import request) as soon as the picture is attached, so a copy at commit comes too late.
Fix: promote RGB pictures always; when the pair is not importable keep the layer, do not borrow the buffer, copy to `wl_shm` at commit (`NativeLayerWaylandExternal::CopyToSharedMemoryLocked`). Look the pair up only in the tranches whose `tranche_target_device` is the `main_device`: a scanout tranche for another device lists what that device can scan out, not what the compositor imports.
How it was found: live YouTube in the two-container rig with a stereo-capable virtual output (`KWIN_VIRTUAL_STEREO_MODES=1` and the capable-anaglyph output config; without it the GPU route's canvas is not a dmabuf layer and the symptom differs), `WAYLAND_DEBUG=client` (no `set_content(3)` on the discrete route, 4 on the other) and `xr465.py` (the session crashed with error 7 after the first 2560x1024 canvas buffer). A WebXR "Enter VR" needs a trusted click (`WebDriver:ElementClick`, not `element.click()`) and `permissions.default.xr` 1. Parallax of the sample page between the routes: cross-correlation of the two eye captures, 8 px on both.

## Trap: a solid green video with hardware decoding on NVIDIA (cause found, ORDER 471)

Symptom: the video area is a flat dark green (0, 77, 0 on the screenshot: Y, U and V all zero in BT.709 limited range), both eyes identical, the log says `Using preferred hardware codec` and `VAAPI locking dmabuf surface` (or `Using vulkan DMABufSurface`), no protocol error. It appeared with nvidia-vaapi-driver 0.0.18, with master 4430507 and with Mozilla's own Vulkan Video path alike, so it is not the driver.
Cause: a decoded YUV dmabuf that the compositor cannot import (`DMABufCompositorCanImport` says 0: another GPU, or NVIDIA's block-linear modifier 0x300000000606014 that KWin does not list) was still pushed with PREFER_COMPOSITOR_SURFACE and without direct composition. WebRender then makes it a native surface it draws itself, and `wr_renderer_lock_external_image` passes no GL context for every compositor surface on the Wayland native compositor ("Wayland native compositor doesn't use textures", bug 1959975), so `RenderDMABUFTextureHost::Lock` returns texture 0 for both planes and WebRender samples zeros. Fix: push such a picture as an ordinary image (`preferCompositorSurface && supportsDirectComposition` for the YUV cases in `DMABUFTextureHostOGL::PushDisplayItems`); then the renderer's own GL context makes the textures. The same patch is right for every decoder (VA-API, Vulkan).
How it was found, in the order that narrowed it:
1. The decode is right: a canvas readback of the playing video (`drawImage` into a 2D canvas, Marionette) shows the real picture while the compositor capture is green.
2. The driver's export is right: `scripts/dmabuf-import-probe.c` decodes frame N through VA-API on the render node, exports it like Gecko (`vaExportSurfaceHandle`, DRM_PRIME_2, separate layers), imports each plane in EGL and prints each plane's mean next to the software decode. It matched in the same process, in a forked process that opens the GPU after the descriptors arrive (SCM_RIGHTS), with the GBM platform and with the Wayland platform, with the export before the sync as Gecko does, and with a surface exported once and reused hundreds of frames later. Not that either.
3. `gfx.webrender.compositor=false` gave the right picture, so the fault is in the native compositor's path: the Parent process logged no `DMABufSurfaceYUV::CreateTexture()` at all (only the RDD's verify step did), which led to `RenderDMABUFTextureHost::Lock(..., nullptr)`.
Rig: a two-container script (KWin in one container on the AMD node, the browser in another with `--device nvidia.com/gpu=0` and the AMD node, the same Wayland socket). Traps of the rig: a browser container with only the CDI device gives `FEATURE_FAILURE_NO_DRM_DEVICE` (add the other render node); NVIDIA's EGL on Wayland needs glvnd's default vendor list, never `__EGL_VENDOR_LIBRARY_FILENAMES` alone (it hides egl-wayland: "no EGL display"); a dev build's `dist/bin` holds relative symlinks, so mount the whole objdir (`/o`) and run `/o/dist/bin/...-bin` with `LD_LIBRARY_PATH=/o/dist/bin` ("Couldn't load XPCOM" otherwise); a child process that exits with `_exit` loses buffered stdout (fflush first).

## NVIDIA decoding and the RDD sandbox

nvidia-vaapi-driver does not start in the sandboxed decoder (RDD) process: it opens `/proc/version` and, when that fails, logs "Potential Firefox sandbox detected, failing to init" and returns (`NVD_FORCE_INIT=1` skips the check); past it, CUDA's ioctls on /dev/nvidia-uvm (plain numbers 0x30000001, 1 to 255, not _IOC encoded) and the NVIDIA RM ioctls ('F' type) are trapped, and `chown` of the device nodes, so cuInit fails (`CUDA ERROR 'out of memory'` after the seccomp rules were widened: the cause behind that was not found). Everyone's answer is `MOZ_DISABLE_RDD_SANDBOX=1` (Mozilla bug 1748460). Mozilla's own Vulkan Video path (`media.hardware-video-decoding-vulkan.enabled`, bugs 2021722 and 2046954) decodes on NVIDIA with the sandbox on and no VA-API driver: the log says `Using vulkan DMABufSurface`, about:support keeps HARDWARE_VIDEO_DECODING blocked because the Vulkan route is its own feature. Mesa hosts are unaffected. Symptoms to read: seccomp violation lines `syscall 16` (ioctl), `92` (chown), `302` (prlimit64) in the RDD; `libva error: ... init failed`; `IsHardwareAccelerated=false` after the decoder says hardware.
Measured: driver 615.71.09, RTX 3060, `MOZ_GFX_SPOOF_GL_VERSION="4.6.0 NVIDIA 535.54.03"` keeps software decoding (the blocklist id says why), `media.hardware-video-decoding.enabled=false` too.

## Traps

- `eglinfo -p gbm` picks the NVIDIA node whatever the vendor file says; judge the compositor's GPU from its log or `gbm_create_device` on each node, not from `eglinfo`.
- Without `XDG_RUNTIME_DIR` Gecko falls back to X11 and never reaches this bug.
- Mozilla bug 2076178 has the same error text from a different cause (HDR compositor, NV12 chroma plane, NVIDIA): read the modifier in the log before joining it.

## A mark a site does not carry

A page can take the right click, so the context menu's 3D Video is out of reach on a site like YouTube.
The browser puts the same choices in the application menu (3D Video, Display Settings), acting on the page's main playing video (largest playing area, frames included).
The site's own VR button appears only for videos the site marks as spherical; the browser does not fake a mark to make it appear.
