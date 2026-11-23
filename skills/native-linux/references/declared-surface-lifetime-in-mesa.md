# A declared surface's lifetime in Mesa

**For** anyone who meets a crash or a damaged heap around a Wayland surface declared full side by side (a 3D area, a player's video, a stereo window): the orders in which a client may take such a surface down, what each must leave safe, the minimal client that runs them all, how to build the edition's Mesa with sanitizers in a rig and read its trace, how to tell which layer wrote, and the traps met on queue row 830 (November 2026).

Row 830 began as "our Mesa corrupts a program's memory when a declared two-view surface is destroyed, on radeonsi".
It ended with Mesa cleared under memcheck and the sanitizers on every order below, the heap damage traced to a write into freed memory by the program's own stereo module, and a different crash found in the edition's player.
The method is the point of this page: suspect the vendor's whole stack first, then read what each control really ran, then let a memory checker say which side wrote ([search-upstream-first](../../search-upstream-first/SKILL.md#a-driver-fault-the-vendors-whole-stack-before-the-hunt-and-again-after-it)).

## The two routes to a declared pair

| Route | Who declares | What Mesa runs |
| --- | --- | --- |
| The program draws its two views into one buffer twice a view wide and declares the surface with `libstereo-declare` (OBS's preview, a player's video) | the program, on its own connection's queue | an ordinary window surface: none of the stereo code of the Wayland EGL platform runs |
| A two-view EGL window, `EGL_MULTIVIEW_VIEW_COUNT_EXT` 2 (Qt's stereo window, SDL, GLFW) | Mesa, at the first right-eye draw (`kde_stereo_content_v1` on the surface's queue; a `wp_viewport` too below protocol version 2) | the stereo path: buffers twice as wide, the pack at swap, the declaration destroyed in `eglDestroySurface` |

Stereo KWin refuses a second declaration of one surface (`error_already_declared`), so the two never meet on one `wl_surface`.

## The orders a client may take, and what each must leave safe

`sparky-os/packages/mesa/tests/egl-declared-pair-lifetime.c` in the build repository runs each one, on both routes and on a plain window (`mono`, the 2D control), with or without a second declared surface drawing on its own thread (`THREAD=1`), and exercises the heap between rounds so that glibc checks its chunks.

| Order | What the client does | Must stay |
| --- | --- | --- |
| `declared` | destroys the EGL surface, then the `wl_surface` while it is declared, and withdraws the declaration only afterwards | memory-safe; the late `destroy` of the declaration is allowed |
| `surface-first` | destroys the `wl_surface` while the EGL surface still draws on it, then the EGL surface | memory-safe |
| `withdraw-first` | withdraws, then destroys (the safe order) | clean |
| `hide-show` | attaches a null buffer and shows the same surface again | clean |
| `resize` | resizes every frame while declared | clean |
| `redeclare` | withdraws and declares again on the same surface every frame | clean |
| `late-release` | destroys everything right after a swap, before the compositor releases the buffers | memory-safe |
| `current-destroy` | destroys the EGL surface while it is current (EGL defers it), the native window and the surface at once; the deferred destruction runs at the next `eglMakeCurrent` (libobs's `obs_display_destroy`) | memory-safe |
| `never-withdrawn` | never withdraws | see the trap below: a protocol error, by design |

Measured on Mesa 26.1.6-1+stereo3d29 under Stereo KWin's virtual output: radeonsi, Mesa's zink on an NVIDIA card (the edition's session route), llvmpipe and NVIDIA's own EGL, 40 rounds a case, all clean; under Valgrind's memcheck on radeonsi, `0 errors from 0 contexts` on every order.

## Recipe

1. **A rig on a dated snapshot** ([dated-snapshot-rig.md](../../stereo-proof-rig/references/dated-snapshot-rig.md)), one fresh `kwin_wayland --virtual` per case, the program under `WAYLAND_DEBUG=client` once to prove the declaration and the buffer width are on the wire (`set_content(3)`, `create_immed(..., 640, 240, ...)` for two 320-wide views).
2. **Each route on each card:** the AMD render node; the NVIDIA card through CDI with Mesa's EGL vendor first, `MESA_LOADER_DRIVER_OVERRIDE=zink` and `LIBGL_KOPPER_DISABLE=1` (Mesa's Wayland platform and dma-buf path without radeonsi or amdgpu), KWin on NVIDIA's own EGL; `LIBGL_ALWAYS_SOFTWARE=1`; NVIDIA's own EGL (no Mesa at all).
3. **`GLIBC_TUNABLES=glibc.malloc.tcache_count=0`** in the client makes glibc check a freed chunk's links on more paths.
4. **Memcheck before sanitizers:** `valgrind --error-exitcode=99 --undef-value-errors=no --fair-sched=yes` instruments the driver and every system library; read the `ERROR SUMMARY` line of each run.
5. **A sanitizer build of the edition's Mesa** from the round's source tree: meson with `-Dgallium-drivers=radeonsi,zink,llvmpipe -Dvulkan-drivers= -Dglvnd=enabled -Db_sanitize=address,undefined -Db_lundef=false`, `-O1 -g -fno-omit-frame-pointer`, installed into a folder with an EGL vendor file naming its `libEGL_mesa.so.0`; the client is built with the same sanitizers so that the runtime comes first; put the folder first with `LD_LIBRARY_PATH`, `LIBGL_DRIVERS_PATH` and `__EGL_VENDOR_LIBRARY_FILENAMES`.
6. **Which side wrote:** an invalid user-space write comes with its stack under memcheck or the sanitizers.
   A damaged heap with no such report points below (an ioctl filling more than its buffer: the same test on a newer kernel decides) or at code the run did not instrument.

## Telling glibc's messages apart

- `malloc(): unaligned tcache chunk detected` is glibc finding a freed block whose link word was overwritten: something wrote into memory after it was freed.
- `realloc(): invalid next size` and `double free or corruption` are the same damage met at another call.
- The backtrace at the abort shows only where glibc noticed (in row 830 a Qt paint allocation); the writer is found by memcheck, or by reading what the program did to freed objects in the step before.

## Traps, symptom first

- **Symptom:** OBS aborted with `malloc(): unaligned tcache chunk detected` after its preview was hidden and shown, on radeonsi only; a bisect pointed at "a declared surface with a two-view buffer destroyed while declared". **Cause:** the program's own stereo module, on the widget's Hide event, called `obs_display_set_views()` on the `obs_display` OBS had freed a moment before at `visibleChanged(false)`: a mutex lock, a field write and an unlock in freed memory, and only when the surface was declared. The bisect's variants were exactly the ones without that write, and the "radeonsi only" was the heap's layout, not the driver. **Fix:** the module follows the display's property synchronously and drops the old pointer (sparky-stereo-obs, ORDER 61). **How found:** the module's source at the crash's commit, the run times against the commit times, glibc's exact message, and memcheck and the sanitizers silent on Mesa in every order above.
- **Symptom:** a program that re-declares a new surface after a hide dies with `kde_stereo_content_v1#N: error 0: wl_surface was destroyed before a set_content request`. **Cause:** `libstereo-declare` keeps its declarations keyed by the `wl_surface` pointer; a declaration never withdrawn stays, and a new surface allocated at the same address reuses the old object. **Fix:** withdraw a declaration even after its surface is gone (`stereo_remove_wayland()` with the old pointer is allowed); the client's `never-withdrawn` order shows the error.
- **Symptom:** the edition's mpv dies with SIGSEGV in `surface_handle_enter` (`video/out/wayland_common.c`) at its first frame, 2D files too, once `libstereo-declare` 1.11 or later is installed; 1.10 plays. **Cause:** `libstereo-declare` binds `wl_output` objects of its own on the program's connection (for the output's width), the compositor sends `wl_surface.enter` once per `wl_output` the client bound, and mpv 0.41's handler dereferences the output it does not know. **Fix:** upstream mpv's f4d13e1c2c "wayland: handle null output in wl_surface.enter event" (llyyr); any program's enter handler must ignore an output it did not bind. **How found:** gdb in the rig with `mpv-dbgsym`, then the same run with 1.10.0 and 1.12.1 of the library.
- **Symptom:** a Qt child window hidden and shown keeps the same `wl_surface` id on the wire. **Cause:** Qt 6.11 destroys only the child's `wl_subsurface` on hide; it keeps the `wl_surface` (Qt 5 destroyed it). Read the trace before saying "Qt destroyed the surface".
- **Symptom:** a Qt test program never exits after its last cycle; its drawing thread sits in `poll` inside `eglSwapBuffers`. **Cause:** swap interval 1 on a thread that waits for a frame event after the main event loop has ended. **Fix:** `eglSwapInterval(display, 0)` once per surface, as libobs draws its displays.
- **Symptom:** `kwin_wayland` copied under another name aborts with `Could not load the Qt platform plugin "wayland-org.kde.kwin.qpa" in "" even though it was found`. **Cause:** KWin's platform plugin goes with the program's own name. **Fix:** run the packaged binary with `--cap-add SYS_NICE`.
- **Symptom:** a sanitizer build of Mesa stops in `ac_parse_ib.c` with `null format string [-Werror=format-overflow=]`. **Cause:** GCC 16 at `-O1` with the sanitizers. **Fix:** `-Wno-error=format-overflow` in the diagnostic build's `c_args` only.
- **Symptom:** a frozen deb-multimedia mirror misses the packages with an epoch. **Cause:** apt names a downloaded file `libaom3_1%3a3.15.3-dmo1_amd64.deb`, the index's `Filename` has no epoch. **Fix:** strip `_N%3a` before matching; freeze what `dist-upgrade` takes as well as the install.
