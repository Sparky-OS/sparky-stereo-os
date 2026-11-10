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

That Venus failure is a result for the VM rig, not a requirement or failure of the native product.
For native qualification, put Android, the Linux consumer and a private `kwin_wayland --virtual` under the machine's own kernel.
Expose only the selected render node, run both Android ABIs, and select the Vulkan device by `VkPhysicalDeviceDrmPropertiesEXT` render major/minor rather than enumeration order.
Record its UUID for the eventual runtime selection.
Use the matching native Android graphics driver; `ro.hardware.vulkan=virtio` is specific to the virtual GPU, not a general GBM setting.
Require import/bind and all-pixel comparison, plus teardown and a matching before/after baseline.
An OpenGL driver name alone does not prove that a Vulkan driver is usable on that kernel/device.

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

## Check existing transport projects before writing the boundary

[xrtransport](https://github.com/xrtransport/xrtransport) already has a documented Waydroid client/runtime and native OpenXR server.
At revision `417b366` (read 2026-11-09), its [Waydroid guide](https://github.com/xrtransport/xrtransport/blob/417b366d91dee60e38ef9cd7aec13af1c82ec538/WAYDROID.md) requires a separate loader broker and supports Vulkan, with GLES planned.
Its core files declare LGPL-3.0-or-later; submodules and imported files retain their own licences.
Check its current contributor and maintainer policies before proposing contact; no project AI contribution rule was found in that snapshot, which is not permission.

The [Vulkan image importer](https://github.com/xrtransport/xrtransport/blob/417b366d91dee60e38ef9cd7aec13af1c82ec538/src/modules/vulkan/client/image_import.cpp) receives **host-created OPAQUE_FD memory and semaphore handles** in Android.
The host then copies from shared staging images into the real runtime's swapchain.
This differs from importing an Android gralloc PRIME dma-buf into Linux: a pass of either direction does not qualify the other.
For opaque memory and semaphore FDs, [Vulkan's compatibility tables](https://docs.vulkan.org/spec/latest/chapters/capabilities.html#external-memory-handle-types-compatibility) require both `driverUUID` and `deviceUUID` equality; this xrtransport snapshot checks the device UUID only.
Qualify both driver builds, not just the GPU name.
The Waydroid swapchain route does not consume legacy GBM native-handle metadata; its gate is compatible Android/host Vulkan opaque memory and semaphore imports on a matching device UUID.
DisplayXR can be the ordinary host OpenXR runtime in that architecture, subject to actual qualification; the transport does not replace the runtime's stereo output or depth policy.

## Traps

- **Symptom:** a Waydroid transport is assumed not to exist, so a new private-IPC bridge is planned from scratch.
  **Cause:** the project search missed an implementation of the same boundary.
  **Fix:** reconcile existing projects against the written design, including actual APIs, licence boundaries, broker discovery and errors, before selecting one.
  **How found:** xrtransport's Waydroid guide, Vulkan client/server sources and two-socket handle exchange contradict the absence claim.
- **Symptom:** a successful dma-buf probe is treated as proof that every FD-based transport works.
  **Cause:** opaque Vulkan allocations/semaphores and DRM dma-bufs have different metadata and import contracts, and may travel in opposite directions.
  **Fix:** qualify the selected route's exact handle types, directions, device identity and synchronization. Keep a CPU-write/import gate separate from asynchronous rendered swapchain proof.
  **How found:** following the actual `VkImportMemoryFdInfoKHR::handleType` and semaphore imports through xrtransport's source.
- **Symptom:** a transport has no fallback but still lacks a useful missing-socket error.
  **Cause:** a throwing connect can escape loader negotiation; a secondary socket failure may be logged without failing initialization and leave a blocking accept.
  **Fix:** inspect both channels, then run bounded absent-socket controls before accepting the user-facing behavior. Do not count a log-only branch as a passed control.
  **How found:** xrtransport's runtime entry point, Asio connect and Linux handle-exchange callbacks; this snapshot was inspected, not executed.

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
- **Symptom:** the guest completes filesystem sync and powers off, but its accelerated QEMU container exits 139.
  **Cause:** an additional teardown crash remains unisolated; guest shutdown is not proof that QEMU exited cleanly.
  **Next gate:** retain the serial shutdown and container exit state; investigate teardown separately if this rig is reused.
  **How found:** the final container-state check caught the nonzero exit, despite the guest's recorded power-off; core dumps stayed disabled.
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

## Native runner startup traps

These failures were captured during native qualification on 2026-11-09.
A subsequent native run reached LXC RUNNING with the root-mount and cgroup corrections below, then Android stopped before boot completed.
That verifies progress through LXC startup, not Android boot or graphics import.
A setup failure does not establish a Vulkan import failure.

- **Symptom:** Waydroid raises `container failed to start`, with no dedicated LXC log.
  **Cause:** the wrapper reports a timeout after its child has already failed.
  **Fix:** set `lxc.log.level = DEBUG` and `lxc.log.file` to a writable path in the private runner's results before starting the session; also set the front-end CLI options as described below.
  Preserve the effective config and its includes, LXC/Waydroid versions, mountinfo, cgroup paths and device numbers.
  Capture a bounded dump of the earliest available guest logcat records as soon as LXC runs, before cleanup, and record when logd was never reachable.
  **How found:** Waydroid's saved log contained the child's pivot and cgroup errors that were absent from the terminal exception; `tools/helpers/lxc.py:start` launches LXC in the background and `wait_for_running` raises after its status poll expires.
- **Symptom:** LXC reports `lxc_pivot_root: Invalid argument` inside a private runner.
  **Cause in the inspected fixture:** the runner entered an ordinary directory with chroot, leaving its current root without a mountpoint; LXC then tried to pivot again.
  This is an explicit EINVAL condition in [pivot_root(2)](https://man7.org/linux/man-pages/man2/pivot_root.2.html).
  **Correction followed by native LXC RUNNING:** make the private root a bind mount, pivot into it in the private mount namespace, and detach the old root tree.
  **How found:** the saved LXC error, the runner's chroot command, and `src/lxc/conf.c:lxc_pivot_root` in LXC's stable-6.0 source.
- **Symptom:** LXC cannot enable `+cpu +memory +pids` and reports resource busy.
  **Cause in the inspected fixture:** its supervisor processes occupied the parent cgroup LXC selected.
  The kernel's [no-internal-process rule](https://docs.kernel.org/admin-guide/cgroup-v2.html#no-internal-process-constraint) prevents distributing domain controllers from that populated parent.
  **Correction followed by native LXC RUNNING:** use a delegated transient unit and a cgroup namespace rooted there, with supervisor processes in `init.scope`.
  Root LXC with `lxc.cgroup.relative = 0` reads PID 1's cgroup and removes this suffix, selecting the empty delegated root.
  Verify that exact layout and a writable manager-side cgroup2 mount before starting.
  Android's own read-only cgroup automount is a separate setting.
  Do not apply this recipe without the private cgroup namespace: the root selected must be the delegated unit.
  **How found:** LXC's `__initialize_cgroups`, `current_unified_cgroup`, `prune_init_scope` and `__cgfsng_delegate_controllers`, matched against the logs.
- **Symptom:** private KWin cannot load `libEGL.so.1` although `/usr` is present.
  **Cause:** Debian's graphics-library symlink resolves through `/etc/alternatives`.
  **Fix:** expose that directory read-only in the private root too.
  **How found:** the library loader error and symlink chain; the next native run started KWin after this mount was added.
- **Symptom:** teardown cannot unload `binder_linux` despite a zero reference count.
  **Cause on the measured kernel:** the module has no exit function.
  **Fix:** record it as an explicit pre-existing prerequisite, leave it loaded, and compare against that baseline.
  Do not promise to restore an unloaded state after loading such a module, or misreport its planned retention as a cleanup failure.
  Binderfs instances and their devices still belong to the disposable namespace.
  **How found:** the coordinator's unload attempt, module behavior and next baseline.
- **Symptom:** normal teardown reports a post-stop hook failure with exit 126.
  **Cause:** older Waydroid configurations name the non-executable `/dev/null` as the hook to suppress automatic respawn.
  **Fix:** use an executable hook that returns success for a normal stop and failure for reboot/unknown targets, retaining respawn suppression.
  Current Waydroid already has this correction in `data/scripts/waydroid-post-stop.sh`; use that behavior when preparing a private fixture for an older installation.
  **How found:** the saved hook path and exit status, checked against Waydroid's current source before considering any upstream report.


- **Symptom:** LXC reaches RUNNING briefly, yet its configured DEBUG log remains empty and later attach fails to find init.
  **Cause in the inspected LXC 7.0.0 build:** front-end tools compile their logging code with `NO_LXC_CONF`, so those paths use the global logger rather than the per-container file descriptor.
  `lxc-start` initializes that logger before loading the container configuration and defaults its file to `none`.
  **Fix:** pass `-o /results/lxc.log -l DEBUG` explicitly to the real `lxc-start` command through a private test-only launcher; capture its stdout, stderr and exit status separately.
  Record the launcher's root, cwd, UID, results mount and file mode instead of assuming where an absolute path resolves.
  **How found:** LXC v7.0.0 `src/lxc/tools/meson.build:22`, `src/lxc/tools/lxc_start.c`, and `src/lxc/log.c:320` matched an unprivileged Debian LXC 7.0.0 reproduction: config-only logging produced zero bytes, explicit CLI logging retained the startup error.
  Later info and attach calls left its hash unchanged; `log_open` uses `O_APPEND`, not truncation.
- **Symptom:** no useful init console output survives an early exit.
  **Cause:** `lxc.console.path=none` makes `lxc_terminal_setup` return before opening `lxc.console.logfile`.
  Android first-stage init also redirects stdio to `/dev/null` before reporting its accumulated fatal setup errors through kmsg.
  **Fix:** omit the `none` setting and log the private console PTY; retain a bounded kernel-journal window and startup syscall trace too.
  Do not bind a host console or assume that an empty logcat proves init never executed.
  **How found:** LXC v7.0.0 `src/lxc/terminal.c:1117` and Android `init/first_stage_init.cpp:304`.
- **Symptom:** early Android exit with neither init kernel messages nor a context manager visible in the saved evidence.
  **Source-established prerequisite failure in the inspected fixture:** a default-deny device filter omitted character device 1:11, while this image's first-stage init requires `mknod("/dev/kmsg", ...)` and treats any failed CHECKCALL as fatal.
  Its kernel logger opens kmsg write-only and silently returns if that open fails.
  **Correction followed by native first- and second-stage init:** allow creation and writing of device 1:11 in the private test, retain the other device restrictions, and collect the resulting init syscalls and kernel messages.
  This grants Android writes into the shared kernel log; it does not require granting reads.
  Do not disable seccomp, AppArmor or no_new_privs without a recorded denial that requires it.
  **How found:** the captured device allowlist and Android `init/first_stage_init.cpp:263`, `:309`, `system/libbase/logging.cpp:113` and `:249`; no syscall trace of the original failed run was available, so its exact errno remains unverified; the next native run proceeded into Android services and recorded their kernel diagnostics.
- **Symptom:** a 32-bit exporter case is mistaken for a 32-bit Android image.
  **Cause:** case labels describe the app ABI while both exporters run in the same multilib x86_64 system image.
  **Fix:** inspect the actual `/init` symlink, executable mode, ELF machine and interpreter inside the mounted root, resolving absolute symlinks against that root.
  **How found:** read-only inspection of the accepted image found an executable ELF64 init and its executable linker64; the captured LXC config declared x86_64 for both exporter ABIs.


- **Symptom:** Android services report `createProcessGroup` failures with `Read-only file system`, even though the private LXC manager has a writable cgroup mount.
  **Cause in the inspected fixture:** Waydroid 1.6.3 `data/configs/config_base:10` supplies `cgroup:ro`, and `tools/helpers/lxc.py:151-170` concatenates that configuration without rewriting it.
  LXC 7.0.0 `src/lxc/cgroups/cgfsng.c:1940-1954` forces mounting on a unified hierarchy, while `:1839-1842` marks this mode read-only.
  The manager's mount does not establish the payload mount's access.
  **Correction followed by native writable mounts and no createProcessGroup errors in four cases:** request `cgroup:rw:force` only inside the disposable payload's delegated cgroup namespace, retaining the private outer namespace and other mount restrictions.
  Never apply this as an unrestricted host hierarchy bind.
  **How found:** init's strace showed uid-directory mkdir returning EROFS and the earlier cgroup2 mount attempts returning EBUSY; LXC logged its prior cgroup2 mount.
  Android init logs this error and continues (`init/service.cpp:664-679`), as does zygote (`com_android_internal_os_Zygote.cpp:1790-1795`), so it does not by itself prove the final boot blocker.
- **Symptom:** a three-minute boot timeout looks like an init crash, while the saved early logcat contains only startup records.
  **Cause in the measured run:** init remained alive until the runner stopped it; system_server took roughly 131 to 134 seconds starting services, and SystemUI repeatedly crashed while creating KeyguardService.
  The early logcat was deliberately retained once nonempty, and a 256-byte strace string limit cut off the Java cause and stack.
  **Fix:** retain an independent late all-buffer dump, a crash-buffer dump, boot properties, window/process state and guest mountinfo before any stop command, with bounded collection time and explicit failure statuses.
  Preserve the last kernel records before the stop timestamp and enough trace string bytes for the observed exception record.
  Distinguish a cleanup SIGKILL from an earlier fatal Java exception and distinguish progress from successful boot completion.
  A longer wait is not evidence that a repeated crash is harmless; obtain its full stack before changing the image or treating the problem as speed alone.
  **How found:** the traced Android log writes exposed the exception in every case and showed ActivityManager entering FinishBooting shortly before teardown.
  `ActivityManagerService.java:5130-5132` can defer that operation until the boot animation completes; its entry log alone is not a completed boot.
- **Symptom:** init reports signal 9 for odsign or idmap2d and this is mistaken for a spontaneous crash loop.
  **Cause in the measured run:** odsign requested its own stop after verification, and system_server requested idmap2d stop after work; init also cleans up oneshot process groups.
  **Fix:** correlate the control-message sender, service exit status and timestamp before attributing a stop to a crash or memory pressure.
  **How found:** kernel records showed `ctl.stop` from the service/controller, odsign exit 0 and its verification property already set; Android's `IdmapDaemon` documents its idle shutdown.
- **Symptom:** LineageOS 20 SystemUI repeatedly crashes creating KeyguardService, with `List.iterator()` on null at `AppOpsControllerImpl.setListening:12`.
  **Cause in the matched image:** R8 inlines `fetchCurrentActiveOps` into setListening; its mapping sends optimized line 12 to source line 186, the outer loop over `AppOpsManager.getPackagesForOps(int[])`.
  That overload forwards a nullable result: AppOpsService starts its result at null and leaves it null when no matching operation records are collected.
  A running service can return this value; it does not establish a missing service, a permission denial or a slow-boot dependency.
  The string-array overload normalizes null to an empty list, but this controller uses the integer-array overload.
  **Fix belongs in the image:** backport Yuichiro Hanada's [upstream null guard and regression test](https://github.com/LineageOS/android_frameworks_base/commit/42f21d60571b7f132f98c04782a7bbefb24a5bbd), bug 324329757.
  In the synchronous LineageOS 20 test, omit the newer branch's `mBgExecutor.runAllReady()` call; return only from the initial snapshot helper so listener registration still proceeds.
  Do not change container privileges, invent app-op history, or disable Keyguard to mask this valid empty state.
  **How found:** full late crash log, the accepted image's APK matching its retained build output, R8 mapping, AppOpsManager/AppOpsService source, and the existing [Waydroid report](https://github.com/waydroid/waydroid/issues/2428).
  A focused Java check of the extracted method reproduced the null-list failure before the guard and passed null, empty, active and inactive cases afterwards; full SystemUITests and a rebuilt native image remain separate gates.

- **Symptom:** after the AppOps correction, the boot deadline still expires, but SystemUI and the home activity continue initializing during diagnostic capture.
  **How found:** align the original process's strace writes with logcat, the final ActivityManager flags, and the runner's own stop; do not time a replayed logcat record as the original event.
  `mBooting=true`, `mBooted=false`, and `mCallFinishBooting=false` are earlier than the animation-completion gate: ActivityTaskSupervisor advances boot when resumed activities become idle, then WindowManager evaluates keyguard/windows and requests animation exit.
  A launcher process started for its Quickstep service does not prove its home activity ran; a newly started FallbackHome is a distinct milestone.
  **Correction to the fixture:** set a bounded wait from the latest observed progress, source deadlines and a stated margin, preserving the boot-completed property requirement and all temperature limits.
  Capture activity/window/user/last-ANR state if the extension still expires.
  Completed intermediate milestones and a nonfatal service ANR followed by progress do not prove eventual boot or a permanently blocked graphics buffer.

- **Symptom:** the first case starts cool, but the next starts hot and immediately reaches the safety stop.
  **Cause in the runner:** cooling was only before the whole batch; each later admission used the higher running-case limit.
  **Fix:** apply the original cool-start wait before every fresh case, after prior cleanup, with a bounded deadline and immediate disk/sensor failures.
  Retain the running-case stop threshold.
  Log temperature, threshold, case, epoch and wait duration; an untimestamped temperature sequence supplies values and sample counts, not exact cooling times.

- **Symptom:** the real compositor is reported killed by a signal during private setup.
  **How to investigate:** a victim journal entry identifies the signal, not its sender; inspect the complete staged launcher before asserting that the outer unshare omitted all PID isolation.
  Assert a different PID namespace, proc mounted for that namespace, and a private PID-1 process group/session before starting any desktop component; record these checks across pivot_root.
  Record existing graphical-session process PID/start-time fingerprints, including the compositor; detect disappearance, PID reuse and zombies during the run and at teardown without signalling those processes.
  A new process is allowed. The initial all-process rule failed on unrelated natural exits; the round-14 lifetime policy below replaces that rule while retaining identity checks for the session core.
  These guards do not establish a historical signal sender or replace native proof. Correlate the incident with the actual case start: an idle hash/cooldown stage cannot be attributed to private-session components that had not started. Preserve a corrected premise when the coordinator supplies a fuller timeline.

- **Symptom:** Android boots in a private PID/mount namespace, but the host's tracing_on, tracefs group or file modes change.
  **Cause:** a read-only sysfs parent does not stop privileged init from mounting kernel-global tracefs beneath it. Android's `init.rc` requests tracefs with gid 3012, and `atrace.rc` changes controls and permissions.
  **How found:** init's successful mount syscall, the matching rc lines, and before/after host tracing state; distinguish a real debugfs bind from an empty sysfs directory with the same path.
  **Correction prepared for native qualification:** mask tracing/debug with empty read-only mounts in both the manager namespace and LXC's newly mounted sysfs; prohibit fresh tracefs/debugfs mounts anywhere with an enforcing mount policy. A mask alone is insufficient while CAP_SYS_ADMIN remains.
  A preloaded per-case AppArmor profile avoids granting Android a policy-loading interface. LXC still needs genuine read-only feature descriptions visible to the manager: its AppArmor backend rejects a confined profile when mount mediation appears absent. Android gets a separate empty security mask.
  Require the loaded profile in enforce mode, verify Android's actual label/mounts, unload only the profile the runner added after confirmed shutdown, and retain it explicitly if shutdown fails.
  Compare host mount options, tracing modes/owners and control values before/after each case, including failure cleanup. Never consume trace streams or restore a changed value to manufacture a pass.
  Local mutation fixtures and parser-only checks establish detector behavior and syntax; kernel enforcement and boot compatibility require the native operator's run.

- **Symptom:** a real Android dma-buf reaches RADV, but the image-format query returns FORMAT_NOT_SUPPORTED for modifier `0x00ffffffffffffff`.
  **Cause:** DRM_FORMAT_MOD_INVALID does not name a layout. Older radeonsi leaves it unreported below GFX9 even when CPU usage has forced a linear allocation.
  **How found:** follow Waydroid legacy gralloc's CPU usage to GBM_BO_USE_LINEAR, DRI_IMAGE_USE_LINEAR, PIPE_BIND_LINEAR and the selected linear surface; then read the generation gate in `ac_compute_surface_modifier`. An invalid modifier alone proves neither linear nor tiled storage.
  **Prepared probe correction:** carry and validate the allocator-specific linear provenance, original modifier, stride and offset. Enumerate the receiver's real modifier support, query importability for explicit LINEAR, create with the supplied plane layout, and verify returned pitch/offset and memory bounds against the dma-buf. Reject unknown or contradictory metadata.
  Do not infer a device's modifier support from age or the package version string: [upstream GFX6–8 support](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/41557) exists and distributors can backport it. Record the advertised extension and format/plane query on each GPU.
  Core VK_IMAGE_TILING_LINEAR is only another possible route when its own capability and exact layout match are established; it does not accept arbitrary external row pitches. Do not silently try it after a modifier failure.
  This evidence applies to the inspected CPU-access allocation, not GPU-only swapchains, asynchronously rendered fences or every format. A native import/copy/pixel check is still required.

- **Symptom:** libdrm prints that amdgpu.ids is missing before successful Android allocation.
  **Cause and evidence:** the ASIC-name parser logs the missing marketing-name table and returns without failing device initialization; hardware capability queries use kernel information.
  Keep the warning visible, distinguish naming degradation from the actual allocator/import error, and avoid an image rebuild solely to explain an unrelated modifier failure.

- **Symptom:** a missing binder module is reported as teardown failure instead of the documented prerequisite exit.
  **Cause:** the failure handler performed already-armed baseline comparisons and replaced the prerequisite status. In the captured run, the system baseline was unchanged, but a legacy debugfs/tracing mount appeared.
  **Fix:** check the required pre-existing binder module before collecting test baselines; retain it once the operator has loaded it, since the measured kernel cannot unload that module. Exercise the real failure handler and aggregate result, not only the check's immediate exit code. Actual changes after a baseline is armed must still fail teardown.
  **Related observer trap:** looking inside an unmounted `/sys/kernel/debug/tracing` can automount tracefs. Read mountinfo first and inspect that alias only when already mounted; a new mount between checks still fails. Never traverse an unmounted alias just to build a baseline.
  **How found:** the prerequisite message, before/after mount lists, the guard's traversal, and Linux `trace_automount`/`debugfs_create_automount`. The lists establish the new mount; the kernel mechanism explains how reading can cause it without proving the historical reader.

- **Symptom:** a survival guard reports sshd-session, shell and sleep disappearing while the graphical session survives.
  **Cause:** the operator's short-lived launching SSH session was still alive when the baseline included all existing processes of the graphical user's UID.
  **Fix:** close that launching session before the detached runner takes its baseline. A measured launch used a delay before acquiring the bench lock; a delay alone is not proof that SSH has closed. The later lifetime policy below also distinguishes young helpers from the protected core; close the launching session rather than relying on its age.
  **How found:** the baseline PID/start-time records, process names and the operator's detached launch script.

- **Symptom:** a private enforcing AppArmor profile loads successfully, but lxc-start fails to apply it and Android never starts.
  **Cause:** the launcher itself is confined. Its `lxc/start-container` abstraction allows change_profile only to matching targets, including `lxc-*` and `lxc-**`; a unique name outside that family is still forbidden. The kernel audit names the launcher as the denied subject and the private profile as the target.
  **Fix:** use `lxc-` plus the unique lane/run/case name, check it against the installed abstraction at run time, reject an existing target, and retain add-only loading plus the enforce-mode check. Fail as a prerequisite with the reason when no pattern matches; do not edit/reload installed policy or select unconfined. A bounded matcher must refuse unrecognized syntax rather than invent its meaning; its successful source check does not prove the loaded kernel policy permits the transition.
  In the native investigation, the operator found packaged `lxc-waydroid` in complain mode. Do not reuse it or the installed lxc-default family: they are not the private enforcing guard. Keep that observed packaging fact distinct from a guarantee about all Waydroid installations.
  **How found:** lxc.log's failed label write, the kernel change_profile denial, and the installed abstraction's target rules. Local old-name rejection and corrected-name acceptance qualify the name check; the native run must still demonstrate the actual transition, Android label and mount isolation.

- **Symptom:** the isolation checker reports “Invalid PID/profile” after a profile rename, while a separate diagnostic says unconfined.
  **Cause:** the command entry point still validated the old prefix and rejected the argument before reading procfs; the unit test exercised only its inner comparison. The unconfined diagnostic was a manager-side `cat /proc/self/attr/current`, not the container init label.
  **Fix:** validate the full generated name, keep exact enforce-mode and read-only-mask checks, and exercise entry validation plus real fixture reads. Record requested PID, expected profile, AppArmor-specific label path, observed label and process start ticks, including failure cases; reject PID reuse. Never loosen a label check to fit an unrelated process.
  **How found:** LXC's successful change_profile log and init PID, the trace's successful label write immediately before exec, the diagnostic's writer in the runner, and the checker's early return. The policy's bare file rule inherits confinement on exec; it does not imply unconfined execution. A missing post-boot label snapshot remains missing evidence, even when the launch transition is established.

- **Symptom:** Android boot adds VSock/VMCI modules to the host, creating new tracing event directories despite private mount/PID/network namespaces and denied tracefs access.
  **Cause:** the image's adbd starts a VSock listener. `socket(AF_VSOCK, ...)` can trigger kernel `request_module("net-pf-40")`; CAP_SYS_MODULE is not required for this implicit autoload. Private network namespaces do not make loaded kernel modules private.
  **Prepared fix:** add `audit deny network vsock,` to the test's own enforcing AppArmor profile. Linux `__sock_create` calls `security_socket_create` before requesting the family module, so a denied creation returns before autoload. Keep installed policy and the kernel unchanged. Preserve the audited create denial under the exact private profile and trace socket/socketcall; a bind failure or an unrelated profile's denial is not proof. The captured adbd source retries permission errors in a detached listener thread, so denial need not block boot; continued boot still requires native measurement.
  Add sorted module names to the host kernel guard. Compare a prepared baseline containing only explicitly managed setup modules during cases, then compare the original baseline after those modules are unloaded. Reject every unplanned addition/removal and name it; never hide autoload by restoring a snapshot or silently unloading modules. The explicitly authorized, recorded five-module restoration below is a bounded test-fixture exception, not an exemption from the final census or tracing checks.
  **How found:** the adbd listener announcement at the registration timestamp, before/after module lists, new VSock trace entries, matching Android listener code, Linux socket-create ordering and transport module aliases. The old trace omitted socket syscalls, so source explains the mechanism without pretending the socket call was captured. A full saved module-list comparison also found PF_KEY, netlink-log and socket-diagnostic additions beyond the conspicuous VSock trace events; an excerpt filtered to VSock cannot establish full restoration. A family-specific denial is not a universal autoload barrier: retain the complete module guard and investigate any new names. Parser-only tests and synthetic denial records do not prove native denial, boot or import.


- **Measured native buffer gate:** a 64-bit Android AHardwareBuffer from legacy GBM reached the host RADV Carrizo device by SCM_RIGHTS. The receiver resolved the proven CPU-linear layout to modifier LINEAR, checked offset 0 and pitch 256 for the 64×64 RGBA allocation, imported/bound it, copied to staging, waited for the queue fence, and compared all 4,096 pixels: zero mismatches. Exporter acknowledgment and all three probe exits were successful. The exact enforcing init label/masks and audited VSock refusal passed in that case. This is one node/ABI and completed CPU writes; the overall run still failed host preservation because five other modules appeared. Do not promote this to a four-case, asynchronous swapchain or OpenXR pass.

- **Symptom:** after VSock is denied, the module guard names af_key, inet_diag, tcp_diag, udp_diag and nfnetlink_log.
  **Cause and evidence:** the captured system_server opens AF_KEY; its BPF statistics helper uses PF_KEY close as a synchronize_rcu barrier. Netd opens NETLINK_NETFILTER and configures NFLOG, and emits TCP SOCK_DIAG requests. System_server opens a SOCK_DIAG listener for TCP/UDP destroy groups. Linux may load a family at socket creation, a netfilter subsystem while processing a message, or diagnostic handlers at group bind, message receive and later socket-destroy work. A socket trace alone does not capture every trigger: retain bind, setsockopt, sendto/sendmsg/sendmmsg, write/writev and close when identifying the exact caller. An asynchronous kernel worker's module request must not be attributed to an unrecorded application send.
  **Confinement options:** an audited private AppArmor key-family denial runs before net-pf-15 autoload. AppArmor's family/type mediation does not distinguish netlink protocol numbers; LXC v2 seccomp supports a socket rule with ANDed argument predicates, for example `[0,16,SCMP_CMP_EQ] [2,12,SCMP_CMP_EQ]` plus an explicit errno. Preserve the generated base policy and other netlink protocols. Check every ABI: an i386 socketcall argument is a pointer to packed socket arguments, which classic seccomp cannot dereference; accepting a native socket rule is not proof that this path is covered.
  **Stop condition found in the image:** NETLINK_NETFILTER denial makes makeNFLogListener return an error, and the measured image's netd main logs it and exits 1. Its init service restarts both zygotes on restart. The matched Connectivity TrafficController also logs a failed SOCK_DIAG listener then dereferences the unset listener. A deny-only kit change cannot promise a boot with these error paths. Stop before attempting that deny-only configuration and report the precise paths; do not preload modules, disable the module guard, forge success, or silently remove networking functionality. Any restricted mode using denial must handle denied optional listeners explicitly and visibly while preserving normal behavior. The coordinator instead chose the restoration design below for this test, leaving normal Android networking intact.
  **How found:** correlate the trace's process names and request bytes with the Android and kernel sources; compare the staged image's netd with its retained build binary and its .text with debug symbols, then inspect the compiled error-to-exit branch. Source and disassembly establish that branch; they are not a native run of the proposed denial. A full module census still governs, including nfnetlink already present in the baseline; removing a test addition must not remove a baseline dependency.

Credits: Android's contributors, Waydroid's contributors, Monado's contributors and DisplayXR's contributors.


### Approved restoration of expected Android autoloads

- **Symptom:** the first native pixel import passes, but the complete module census still fails after Android has loaded af_key, inet_diag, tcp_diag, udp_diag and nfnetlink_log.
  **Cause and callers:** system_server and its NetworkStats thread open AF_KEY for the BPF statistics helper's synchronization barrier. Netd configures its NFLOG listener through NETLINK_NETFILTER and sends TCP SOCK_DIAG requests. System_server subscribes to TCP/UDP socket-destroy groups through NETLINK_SOCK_DIAG. The saved trace and sources establish these paths; the exact first UDP close/request was omitted from the original trace and is not claimed. Kernel socket-destroy work can request a diagnostic handler asynchronously. Keep bind, setsockopt, sendto/sendmsg/sendmmsg and close for both ABIs, alongside socket/socketcall and write/writev, to improve attribution without equating a nearby send with a worker's trigger.
  **Fix chosen for this test:** the coordinator explicitly approved allowing those five natural autoloads, then restoring only the additions after each Android case has stopped. Keep a single ordered list with caller evidence. Confirm the exact test unit is inactive/failed, its main/control PIDs are zero and its cgroup is empty or removed. Preserve the pre-removal kernel snapshot and module references/holders. An unexpected addition still fails the case, but cleanup removes approved unused additions and leaves the unexpected module untouched and named for the coordinator. Preserve that unexpected set in intermediate census checks. A missing baseline module still stops removal. Record approved cleanup separately; it cannot turn the case into a pass. Use `rmmod NAME` for each expected addition, tcp_diag and udp_diag before inet_diag; never `modprobe -r`, which could remove baseline nfnetlink. Do not remove a named module already in the baseline. Require zero use/holders, record every command and result, and stop on an in-use module, timeout, failed removal or census change. Do not force removal or preload the modules to disguise a change.
  **Proof required:** every case, including a failed boot or thermal stop, uses the same restoration after confirmed stop. Persist appeared/removed names, stop proof, removal results and `MODULE_RESTORE_PASS` only after exact baseline equality. Missing, malformed or incomplete restoration records fail teardown. Keep the complete post-restoration tracing, session and original-baseline checks; do not silently restore tracing controls. Preserve the private audited VSock refusal, already measured with successful boot/import. Round-12b fixtures cover order, baseline preservation, busy/unexpected modules, failed removals, live units and failure cleanup without executing module operations. The native restoration and other three node/ABI imports still require the coordinator's next run.
  **How found:** the accepted native trace/census and matching Android/kernel sources showed that these are Android networking paths; the compiled NFLOG error path exits netd and its onrestart restarts both zygotes. Refusal would break the service. The coordinator therefore authorized explicit teardown restoration in this disposable kit, rather than an image change. Upstream kmod's rmmod checks holders/refcounts and removes only the named module. This is scoped authorization for those five evidenced autoloads; unknown host changes still fail.

### Keep diagnostic tools from changing the host or consuming the boot budget

- **Symptom:** widening whole-boot strace adds netlink_diag to the host module census, although no Android SOCK_DIAG request is captured.
  **Cause:** strace 7.3's normal netlink send decoder calls `get_fd_nl_family`, which uses `get_sockaddr_by_inode` and its own NETLINK_SOCK_DIAG socket to request an AF_NETLINK dump. This happens without `-yy`. The kernel can autoload netlink_diag while answering that diagnostic request. The tracer's own calls are absent from the tracee files, so their absence does not exonerate the tool. See [strace v7.3 netlink.c](https://github.com/strace/strace/blob/v7.3/src/netlink.c), [socketutils.c](https://github.com/strace/strace/blob/v7.3/src/socketutils.c) and Linux's net/netlink/diag.c module alias.
  **Fix:** keep this instrumentation module out of the Android allowlist. Use `--decode-fds=none` and `-e raw=send,sendto,sendmsg,sendmmsg`, with `-e write=all` for independent payload dumps. Decode the saved netlink headers offline. This preserves native and i386 socketcall payloads without querying the host's diagnostic families. Do not pass `-yy` or re-enable send decoding later without the negative control.
  **How found:** the native trace had decoded netd netlink sends but no diagnostic request; matching strace source showed the implicit lookup. In a safe local nested-trace test, a test-only seccomp filter refused the tracer's diagnostic socket before kernel autoload. The old decoder attempted queries; the new options made zero queries while retaining payload bytes in both ABIs. No native tracer PID was recorded, and no actual module request was allowed in that local test.

- **Symptom:** a previously 221-second boot misses a 300-second deadline after wider tracing. The failing run has more selected syscall entries (261,568 versus 220,735), including 108,311 close entries, but fewer bytes and tasks because less boot work completed. Its logcat shows successful dexopts still advancing at timeout, not a new captured crash.
  **Cause and limit:** whole-tree ptrace, decoding, output and the tracer's own socket lookups add cost. Without seccomp-assisted filtering, even unprinted calls still incur ptrace stops; selected-entry counts are not total-stop counts. The native pair is not an isolated timing experiment and cannot assign the entire slowdown to one factor. A smaller log is not evidence of lower instrumentation cost.
  **Fix prepared:** run LXC directly, retain its DEBUG/console/stdout/stderr logs, mounted-init audit, early/crash/late logcat and kernel snapshots. Poll only the private proc namespace for exact netd/system_server/adbd identities and the expected enforcing label, then attach once per role. Capture socket/socketcall, bind, setsockopt, sends, write/writev and close, sharing a 4,000-selected-call or 300-second budget across that role's traced threads/children. A tracer SIGINT detaches; never signal the Android target. Keep PID/start ticks, argv, timestamps, cap reason, actual syscall count and errors. Missing/failed attribution cannot certify a successful case. Leave init, zygote and dex2oat untraced. Polling can miss the earliest calls, and the cap omits later calls; record these coverage limits rather than claiming a complete boot trace or an identified UDP worker.
  **How found and proof:** compare counted trace entries/bytes/tasks, the same system-server milestone and continuing dexopt completions; reproduce tracer overhead with an owned open/close fixture. The real tracer must detach at the cap while the fixture continues, and the fixture must survive timed detach. That local workload is not an Android boot benchmark. Keep the established native boot deadline; use the earlier completed native time as a planning reference only. Native attach permissions, boot time, absence of the instrumentation module and restoration through all node/ABI cases still need the next run.


- **Symptom:** the session guard fails during preflight on two `bwrap` processes and `glycin-image-rs`, before Android starts, while the compositor and desktop remain alive.
  **Cause:** an all-process baseline treated normal helper exits as session loss. The native before/after records held 109 then 106 identities; the three lost helpers had start ticks 4440923/4440926. Review uptime 44599.56 seconds and CLK_TCK 100 bound their earlier baseline ages below 190.33/190.30 seconds. Do not present a later uptime as an exact baseline age.
  **Fix:** record baseline uptime, clock ticks and age. Always protect logind's session leader, the user manager's MainPID, the compositor, plasmashell and ksmserver, even when newly started or the leader is root-owned. Protect other baseline processes aged at least 300 seconds; retain younger departures as named observations without failing. The five-minute threshold exceeds this measured helper age bound by over 109 seconds; it is a conservative policy, not a universal helper lifetime. Older helpers remain protected and can still cause a conservative stop.
  Check the original logind session identity/State and systemd scope ActiveState/InvocationID/ControlGroup at every poll. Session closing/removal or scope termination/restart must fail even if some process identities survive. PID reuse and zombies still fail for protected processes.
  **Signal boundary:** audit every kill and stop call. Keep private commands behind the asserted PID namespace and detached root. Restrict host cleanup to the exact transient service in system.slice, fingerprint and record its cgroup recipients before stopping, and refuse any session recipient regardless of age, including newly started helpers. Distinguish a private Android process with the desktop user's numeric UID by both its PID namespace and the exact case-specific enforcing AppArmor label; a desktop sandbox can also have a separate PID namespace. A recorded kit target must fail even when the helper policy would otherwise allow departure. Automatic service cleanup must remain confined to the same cgroup. This target census is not a kernel signal-delivery trace; it does not identify an unknown historical sender.
  **How found and proof:** correlate start ticks with uptime, replay the captured before/after identities, and inventory the runner's stop paths. Fixtures must pass a young helper's ordinary exit, fail a lost compositor, fail a session or scope ending with process files still present, and refuse an attempted stop targeting a young or new desktop helper before sending. Run these with fake proc/logind/systemd and mocked stops, never by terminating a person's desktop. Native admission, boot/import and final survival still need the next operator-run attempt.


- **Symptom:** all native cases fail before LXC starts with `FileNotFoundError` for a tracer module beside a PATH shim, although the extracted kit passes its local checks.
  **Cause:** `__file__` names the symlink used to invoke the launcher. `Path(__file__).with_name(...)` looks beside that link instead of beside the installed source. The previous diagnostic fixture supplied a fake supervisor, bypassing precisely the default import that failed natively; passing it did not establish the launch chain.
  **Fix:** resolve the launcher symlink before selecting a sibling module with `Path(__file__).resolve().with_name(...)`. Keep one source module instead of creating a second runtime copy. [Path.resolve](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve) follows symlinks; the direct-file import then uses that resolved filename.
  **How found:** native launcher stderr identifies the missing path, the runner shows the PATH symlink, and the source shows the unresolved sibling lookup. A saved prior archive reproduces the same missing path in an unprivileged container; the corrected archive reaches real tracer exec through the same installed entrypoint.
  **Check the installed chain:** execute the installation block read from the runner, invoke its discovered entrypoint, and let the real import machinery and supervisor run. Intercept import/exec requests to verify their actual files, executable bits and shebang/ELF interpreters. Read the generated LXC configuration and every include to discover hook and guest-init commands; trace the hook's executed programs too, and deliberately add a missing hook to prove the path walker rejects it. Do not maintain a separate hand-written list of companion scripts that can drift from the launcher.
  **Fixture boundary:** substitute only LXC itself and the Android process identity/profile lookup, targeting owned bounded workers. Keep the entrypoint, namespace guards, imports, supervisor, tracer command, actual strace exec and detach real. Run with a private PID namespace, no network, capabilities or devices, a read-only kit, writable disposable fixture paths and core dumps disabled. Check that workers survive detach. This proves packaged path resolution and tracer execution, not Android boot, actual AppArmor attachment permissions or native buffer import.
  **Measured outcome:** the preceding native session guard completed all four cases with no session failures and preserved the module census, but Android never started. Empty module restoration and absent VSock refusal in that run are consequences of the launcher failure; neither proves Android confinement or working tracer attachment.

## Native dma-buf gate completed, then qualify the runtime separately

**Measured, 10 November 2026:** a CPU-written 64×64 Android buffer from legacy GBM crossed SCM_RIGHTS and imported into native Vulkan on RADV CARRIZO and RADV HAINAN, with both x86_64 and i686 exporters.
All four readbacks matched all 4096 pixels; Android boot observations were 88, 89, 87 and 84 seconds.
The enforcing-profile, VSock-refusal, bounded-tracer, session-survival and kernel-state guards held, and each case removed the five expected autoloads, restoring the prepared module census.
This is a native allocator/import qualification, not an OpenXR rendering result.
The producer completed CPU unlock before transfer and held the allocation through acknowledgement; no producer fence crossed and no swapchain was reused.
The consumer's own Vulkan fence only waited for its readback copy.
The i686 exporter used the same multilib image, not a separate 32-bit OS.
The retained default allocator's memfd result remains valid for that mode.

For xrtransport, keep the next gate distinct: its Vulkan module exports host-created OPAQUE_FD memory and two persistent binary semaphores to Android, then copies into the host runtime's swapchain.
Compare both driverUUID and deviceUUID and query the external memory/semaphore capabilities before import; the existing client checks only the device UUID.
A successful Android dma-buf import does not establish this reverse-direction opaque-handle path.
Keep the system broker, the in-app runtime library, the RPC socket and the FD-exchange socket as separate checks.
Before wiring the native runner, obtain the operator's read-only inventory of the host OpenXR runtime, manifest, library and plug-ins.
A saved GPU import log does not say which OpenXR runtime is installed.
When the operator alone may access the target, ask for that inventory while completing independent builds; do not guess the target's installation from the build station.

- **Symptom:** the pinned xrtransport Android APK fails at `processDebugMainManifest`, although both native client ABIs compile.
  **Cause:** an SPDX comment precedes the XML declaration in its manifest.
  **Fix:** move the XML declaration to the first line and retain the licence comment immediately below it.
  **How found:** the real Gradle manifest-merger failure, the XML parser's line-2 error, and an upstream-head/issue/PR search; the same Gradle APK build succeeds after this two-line reorder.
  This is a local fork correction; it is not sent upstream without the person's decision.
- **Symptom:** a pinned hello_xr build rejects `ALooper_pollAll` as unavailable with a newer NDK.
  **Cause:** that sample declares NDK 23.2.8568313, while the attempted build used NDK 29.
  **Fix:** build the sample with its declared NDK, keeping the other component's toolchain separate.
  **How found:** compare the compiler error and NDK header with the sample's Gradle file; both x86_64 and x86 then compile with the declared NDK.
  If the source generator mixes its bundled Jinja2 with system MarkupSafe and fails on `soft_unicode`, put the source's complete vendored Python directory first in PYTHONPATH before configuring CMake.
  The source already supplies the matching dependencies; no API shim or vendor-code edit is needed.
- **System runtime discovery remains a native test.** xrtransport's APK supplies runtime service metadata but no system ContentProvider.
  The Khronos system-broker template can select this package through its supplied chooser; keep its normal OPENXR_SYSTEM permission and distinct system authority.
  Its extracted-library lookup returns the package's nativeLibraryDir, so use one ABI per qualification APK and verify the packaged ELF class; a multilib zip alone does not prove 32-bit discovery.
  A built, signed APK and a configured provider are packaging evidence only; still check the provider's returned path and a real loader launch after installing into the private test overlay.
