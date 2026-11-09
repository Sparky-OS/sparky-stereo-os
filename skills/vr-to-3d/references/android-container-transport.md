# An Android container reaching the host OpenXR runtime

This is the allocator preflight for a guest transport, not a completed OpenXR bridge.
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
5. If the running allocator supplies shared-memory fds, stop the dma-buf transport work at this prerequisite.
   A source tree containing `gralloc.gbm` does not prove the process selected it.

The [diagnostic probe](../scripts/gralloc-fd-probe.c) tries CPU, GPU render/sample, and combined usages with a 64 by 64 RGBA buffer.
Exit 0 means every inspected fd accepted the dma-buf sync operation; exit 2 means at least one returned `ENOTTY`; exit 1 means setup or an inconclusive operation failed.
Its successful ioctl result is only an allocator gate: it does not prove image import, correct modifier/stride handling, fences or OpenXR presentation.

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
This establishes the result for that running configuration; the image also contains the separate GBM allocator, whose runtime export/import path was not tested here.

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
