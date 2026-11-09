# An Android container reaching the host OpenXR runtime

This is the allocator and Vulkan-import preflight for a guest transport, not a completed OpenXR bridge.
Keep the application's views and poses at the host runtime boundary; the runtime still supplies one declared left-first full side-by-side window to Stereo KWin.
Depth limits remain the host runtime's existing KWin input.

## Check the running allocator first

1. Boot the exact system/vendor pair in an isolated Waydroid session and verify its image hashes.
2. Record `getprop ro.hardware.gralloc`, `getprop ro.hardware.egl`, the accessible DRM nodes and the loaded mapper/allocator libraries.
3. Allocate a real `AHardwareBuffer` with the graphics usages the application will need.
   Inspect every native-handle fd with `/proc/self/fd`, `/proc/self/fdinfo` and `DMA_BUF_IOCTL_SYNC`.
   An fd count alone cannot distinguish ashmem, memfd and dma-buf.
4. Run the same check on `/dev/null`; it must be rejected with `ENOTTY`.
   Treat another error as inconclusive, not as a positive dma-buf result.
5. Identify each fd's role: pixel storage and allocator metadata need not use the same kind of fd.
   If the running allocator supplies only shared-memory fds, stop the dma-buf transport work at this prerequisite.
   A source tree containing `gralloc.gbm` does not prove the process selected it.

The [diagnostic probe](../scripts/gralloc-fd-probe.c) tries CPU, GPU render/sample, and combined usages with a 64 by 64 RGBA buffer.
Exit 0 means every inspected fd accepted the dma-buf sync operation; exit 2 means at least one returned `ENOTTY`; exit 1 means setup or an inconclusive operation failed.
Its successful ioctl result is only an allocator gate: it does not prove image import, correct modifier/stride handling, fences or OpenXR presentation.
Its exit 2 is deliberately conservative: a mixed handle needs further inspection, not a conclusion that it has no dma-buf.
A measured minigbm handle contained a pixel dma-buf and a separate memfd reserved region.

Build inside an isolated development container with a matching Android source tree and NDK mounted read-only:

```sh
compiler="$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/x86_64-linux-android29-clang"
"$compiler" -Wall -Wextra -Werror \
    -I"$ANDROID_ROOT/frameworks/native/libs/nativewindow/include" \
    -I"$ANDROID_ROOT/system/core/libcutils/include" \
    gralloc-fd-probe.c -landroid -ldl -o gralloc-fd-probe
```

Use `i686-linux-android29-clang` for a 32-bit client.
Run the resulting executable inside the isolated Android container with a timeout and capture its actual exit status.
It is a platform diagnostic: `AHardwareBuffer_getNativeHandle` belongs to the VNDK header, not the public NDK application API.
The probe resolves it from `libnativewindow.so` and reports failure if that symbol is unavailable.

Measured on 2026-11-09 with the edition's Android 13 image in the retained software-configured Waydroid rig: both x86 and x86_64 selected `gralloc.default`, allocated all three usages successfully and returned one memfd per handle.
All six allocation fds were named `memfd:gralloc-buffer` and rejected the dma-buf sync ioctl with `ENOTTY`; both diagnostic processes exited 2 with zero inconclusive errors.
The loaded allocator hashes matched the accepted image manifest.
This establishes the result for that running configuration; the separate GBM configuration below has a different result.

## Qualify GBM explicitly

Keep a saved copy of the existing Waydroid configuration and expose the graphics mode as an explicit choice.
Test changes belong in an isolated configuration; never rewrite the shared image's graphics default to make a transport probe pass.
For the measured Android 13 image, these properties select its shipped legacy GBM module with a virtual GPU:

```ini
[properties]
ro.hardware.gralloc=gbm
gralloc.gbm.legacy=true
gralloc.gbm.device=/dev/dri/renderD128
ro.hardware.egl=mesa
ro.hardware.vulkan=virtio
```

These are a test configuration, not a qualified product preset.
Recreate the private Android session, then verify the live properties and loaded module in both ABIs.
Without `gralloc.gbm.legacy=true`, Android's property initialization rewrites `gbm` to `minigbm_gbm_mesa` for vendor API 33 or later.

For an accelerated VM, [QEMU's virtio-gpu documentation](https://www.qemu.org/docs/master/system/devices/virtio/virtio-gpu.html) and [Mesa's Venus requirements](https://docs.mesa3d.org/drivers/venus.html) describe the required host blob support and Venus capability set.
Use a headless EGL render node, host memory and Venus enabled on the virtual GPU, and a supported host Vulkan driver.
Check the guest kernel's reported features and run `vulkaninfo` inside the guest with the intended ICD explicitly selected.
The physical host's `vulkaninfo` is only a virtualization prerequisite.

The measured GBM configuration returned three pixel dma-bufs per ABI, all accepting the sync ioctl.
Linux in the same VM enumerated a Venus device and advertised dma-buf import and DRM modifiers.
The next check still failed: send an actual Android buffer fd by `SCM_RIGHTS`, together with its validated format, dimensions, plane count, byte stride and modifier, to a Linux Vulkan receiver in that VM.
For the tested 64 by 64 RGBA buffer, stride was 256 bytes and the modifier was linear.
The format query advertised importability and image creation succeeded, but `vkGetMemoryFdPropertiesKHR` aborted in the Venus driver on both ABIs.
The render server reported an invalid resource ID while querying its properties.
No Vulkan memory import, pixel readback or OpenXR presentation was proven.

The receiver should proceed to import/bind memory and compare every pixel against a known pattern only after that prerequisite works.
Wait for Android CPU-unlock completion before transfer, keep the buffer alive until the receiver finishes, and obey Vulkan's fd ownership transfer on successful import.
This small test does not qualify asynchronous swapchain fences or frame reuse.
An explicit attempt to select the shipped Zink backend in this image failed graphics allocations and repeatedly crashed SurfaceFlinger; it is not a working alternative.
Restore the saved configuration and verify the original allocator again before leaving the test.

## What the next transport gate needs

Waydroid's [GBM allocator](https://github.com/waydroid/android_hardware_waydroid/blob/lineage-20/gralloc/gralloc_gbm.cpp) exports a PRIME fd with `gbm_bo_get_fd` and carries stride and modifier metadata.
The default Android allocator creates ashmem-backed allocations instead.
Qualify the actual GBM/DRM configuration and import in the intended host Vulkan device before treating those descriptors as portable swapchain images.
Android and the host runtime must share a kernel for direct Unix-socket fd passing.
When the test runs Waydroid inside a VM, the host runtime for that test belongs inside the same VM; a guest fd does not become a station-kernel dma-buf through a file share.

The Android loader's broker/service discovery, the runtime client socket, and swapchain handles are separate gates.
A connected socket does not convert an Android hardware buffer into a Linux dma-buf.
Use matching client/server IPC definitions and explicit errors for a missing socket or unsupported allocator.
The final proof is an Android `hello_xr` red view 0 and blue view 1 captured at KWin, plus a missing-socket failure and a deliberately exchanged-view failure.

## Traps

- **Symptom:** `virtio-vga-gl` or `egl-headless` is unavailable, or QEMU cannot open `libEGL.so.1`.
  **Cause:** a minimal QEMU image lacks its matching OpenGL modules or the EGL loader; the Mesa vendor library alone is insufficient.
  **Fix:** verify package candidates, install matching QEMU modules and the EGL loader in the disposable image, and check the device/display help before booting.
  **How found:** QEMU's help and startup log; the corrected image reached guest boot.
- **Symptom:** Venus advertises its capability set, but guest `vkCreateInstance` returns `ERROR_OUT_OF_HOST_MEMORY`, alongside QEMU commands `0x10c`, `0x208` and `0x209` failing.
  **Cause in the measured case:** the separately packaged `virgl_render_server` executable was missing.
  **Fix:** install the matching render-server package in the QEMU container and restart the private VM.
  **How found:** [QEMU issue 2997](https://gitlab.com/qemu-project/qemu/-/issues/2997), the package file list, then successful guest Venus enumeration after installation.
- **Symptom:** a configured `gbm` test runs `minigbm_gbm_mesa` instead.
  **Cause:** the Android property-service compatibility rewrite runs after loading Waydroid's properties.
  **Fix:** use the existing `gralloc.gbm.legacy=true` opt-in when the test specifically requires the legacy module, and assert the live selection.
  **How found:** live `getprop`, loaded mapper libraries and `system/core/init/property_service.cpp`.
- **Symptom:** a real dma-buf passes the ioctl probe but the Vulkan consumer aborts before importing memory.
  **Cause established so far:** Venus's resource-properties query cannot find the transferred virtual resource; the precise renderer/kernel defect remains unisolated.
  **Next gate:** repair or qualify the virtual graphics import path, or qualify a compatible native graphics device shared by Android and its runtime under one kernel.
  Do not call fd allocation a successful swapchain transport.
  **How found:** both ABI senders, matching metadata, render-server errors and a GDB backtrace at `vkGetMemoryFdPropertiesKHR`; core dumps remained disabled.
- **Symptom:** binding the diagnostic socket under a host-side Android rootfs directory fails with `ENOENT`.
  **Cause:** Android's data mount exists in its container mount namespace.
  **Fix:** for a private diagnostic, resolve the data directory through the live container init process's `/proc/PID/root`; for the feature, bind a dedicated shared socket directory explicitly.
  **How found:** the failed bind followed by successful fd receipt through the container-visible inode.
- **Symptom:** a successful Android graphics allocation has a native handle with one fd, yet the dma-buf gate fails.
  **Cause:** the selected `gralloc.default` calls `ashmem_create_region`, and libcutils implements that allocation using memfd on the measured kernel.
  **Next gate:** select and qualify the intended GBM/DRM configuration, with an accessible supported render node and matching graphics drivers.
  Do not reinterpret a shared-memory fd as a dma-buf or silently substitute another transport.
  **How found:** runtime properties, process maps, fd targets and the `ENOTTY` result, then the allocator and libcutils source.
- **Symptom:** the NDK compile cannot find `native_handle_t` or `AHardwareBuffer_getNativeHandle`.
  **Cause:** allocation is an NDK API, while native-handle inspection is a platform/VNDK API.
  **Fix:** compile this diagnostic against the matching platform headers and resolve the exported `libnativewindow` function explicitly.
  **How found:** the compiler error, `include/vndk/hardware_buffer.h` and `libnativewindow.map.txt` in the Android tree.
- **Symptom:** `qemu-img create` cannot open the backing file even though the retained overlay is mounted.
  **Cause:** that overlay names another backing disk at an absolute path.
  **Fix:** inspect the whole backing chain and mount every backing disk read-only at the paths the chain records; only the new overlay is writable.
  **How found:** `qemu-img info --backing-chain` inside the isolated QEMU container.
- **Symptom:** the QEMU container exits 125 with no QEMU output.
  **Cause:** its `timeout` process became PID 1.
  **Fix:** use Docker's `--init`, keeping the timeout and disk guard.
  **How found:** the exit status matched the existing [proof-rig lesson](../../stereo-proof-rig/references/lessons-2026-11.md), and the corrected container booted.
- **Symptom:** `/system/bin/sh: cat: inaccessible or not found` when copying a probe through `lxc-attach`.
  **Cause:** the attached shell inherits a host command search path that does not locate Android's tools.
  **Fix:** use `/system/bin/cat` explicitly for the transfer.
  **How found:** the guest unit's exit 127 and journal line; the absolute-path invocation then transferred both binaries with matching hashes.

Credits: Android's contributors, Waydroid's contributors, Monado's contributors and DisplayXR's contributors.
