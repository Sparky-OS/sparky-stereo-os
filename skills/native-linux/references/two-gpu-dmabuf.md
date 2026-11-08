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

Compare the compositor's `main_device` with the client's render node (both device numbers mapped to their PCI device through `/sys/dev/char/MAJOR:MINOR/device`, so a card node and a render node of one GPU compare equal; libdrm is not linked into Gecko).
When they differ, the client keeps drawing into its own buffers and gives the compositor a `wl_shm` copy of each committed frame (Gecko `NativeLayerWaylandRender::CopyToSharedMemoryLocked`, `gfxVars::DMABufCompositorOnOtherGPU`).
Measured on an RTX 3060 against KWin on the AMD iGPU: a WebGL2 canvas and a 1080p video stay at 60 fps, the marked video still declares its stereo content.

What does not work, measured with `gbm_bo_create*` and an EGLImage on the NVIDIA node: `GBM_BO_USE_RENDERING` together with a modifier list fails; a LINEAR buffer is made with `GBM_BO_USE_LINEAR` alone or with the modifier list `[0]` and no flags; but an imported linear dmabuf is not a renderable target (framebuffer status `GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT`, 0x8cd6).
So "allocate with the compositor's modifiers through GBM" cannot work on NVIDIA; the GPU has to draw into its own tiling and a copy goes to the compositor.
Without native layers (`gfx.webrender.compositor` false) the driver's own EGL Wayland platform does the cross-GPU copy and the window works, but no layer is declared, so a 3D video is shown flat.

## Traps

- `eglinfo -p gbm` picks the NVIDIA node whatever the vendor file says; judge the compositor's GPU from its log or `gbm_create_device` on each node, not from `eglinfo`.
- Without `XDG_RUNTIME_DIR` Gecko falls back to X11 and never reaches this bug.
- Mozilla bug 2076178 has the same error text from a different cause (HDR compositor, NV12 chroma plane, NVIDIA): read the modifier in the log before joining it.

## A mark a site does not carry

A page can take the right click, so the context menu's 3D Video is out of reach on a site like YouTube.
The browser puts the same choices in the application menu (3D Video, 3D Display), acting on the page's main playing video (largest playing area, frames included).
The site's own VR button appears only for videos the site marks as spherical; the browser does not fake a mark to make it appear.
