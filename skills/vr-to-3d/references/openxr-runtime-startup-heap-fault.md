# The OpenXR runtime aborts at start: `malloc(): unaligned tcache chunk detected`

Found on 2026-11-21 (queue row 762c) on the edition's DisplayXR runtime 2.66.3 (+stereo3d10 and +stereo3d11, the same programs), with libxext6 2:1.3.4-1+b4.
DisplayXR's own tracker has the same symptom on Ubuntu with its main branch: [DisplayXR #2711](https://github.com/DisplayXR/displayxr-runtime/issues/2711), open, no cause given.

## Symptom

- An OpenXR program (DisplayXR's `cube_hosted_legacy_vk_linux`, the edition's paired headset row) dies within a second of starting, now and then: `malloc(): unaligned tcache chunk detected`, sometimes `free(): chunks in smallbin corrupted`, sometimes a plain SIGSEGV.
- The runtime's log stops at the same place every time: after `#868: repaint loop start` and the `Color (#1589) [vk_native]` line, before `#886 ... VK_LAYER_DXR_queue_lock route`.
- The next start usually works. Measured on a headless Stereo KWin: 2 and 4 failures in 40 starts with the container pinned to two CPUs (+10 and +11), 0 in 38 on a quiet machine, 2 in 3 while a build ran beside it; DisplayXR's own 1 ms display poll (`DXR_DISPLAY_HOTPLUG_POLL_MS=1`) gave 4 in 20.
- Under AddressSanitizer it never happens, and ThreadSanitizer reports nothing that explains it.

## Cause

The damaging write is in libXext, an X.Org client library, not in the runtime:

- libXext's Generic Event extension (`src/Xge.c`) keeps one process-wide record, `xge_info`. `_xgeFindDisplay()` creates it on first use and hands it to `XextAddDisplay()` without a lock; `_xgeDpyClose()`, run by `XCloseDisplay()`, frees it when the last display that used it closes (libXext commit ed8d50ba, 2012, "Destroy generic event extension after last display is removed").
- Every extension a client sets up on a display registers with it (`XextAddDisplay()` calls `xgeExtRegister()`), RandR included.
- So when one thread closes its display while another thread is setting up RandR on its own display, the second thread writes into the freed record: `XextAddDisplay()` (extutil.c:167) stores `extinfo->head` at offset 0 of the freed 24-byte block, which is where glibc keeps a freed chunk's tcache pointer. The next small allocation in the first thread finds a garbage pointer.

What triggers it in the runtime is several threads using separate X displays at once, each legal in Xlib's thread model:

- DisplayXR's display snapshot during `xrCreateSession` (`target_screens_build` → `os_display_desktop_enumerate` → `query_monitors`: a private display opened, RandR queried, closed);
- DisplayXR's in-process hotplug poll (a thread doing the same every 500 ms, `DXR_DISPLAY_HOTPLUG_POLL_MS`);
- the edition's window depth observer (patch 0020, `comp_vk_native_depth.c`), a thread that opens its own display and queries RandR through libstereo-declare at the end of compositor creation, right when the main thread takes its display snapshot. That is why the edition's failures all fall at the same log line.

glibc notices the damage at the next allocation of that size in the thread that freed it: in the runtime that is libdbus's `dbus_parse_address()` inside `query_mutter()`, exactly the stack in DisplayXR #2711. It is where the damage is seen, not where it is made.

## Fix

In libXext: keep the record for the life of the process, as every other libXext extension (`XEXT_GENERATE_CLOSE_DISPLAY` only removes the display) and libXrandr (`static XExtensionInfo XRRExtensionInfo`) already do. The record gets static storage; `_xgeFindDisplay()` no longer creates it and `_xgeDpyClose()` no longer frees it.
A runtime change is not the fix: the same library race reaches any program that opens and closes X displays on more than one thread.

## How it was found

1. The paired route reduced to a headless Stereo KWin with two virtual outputs and the sample started 40 times with the route's environment; the same message at the same log line.
2. ASan (60 starts) and UBSan: silent. TSan (3 starts): one benign flag race. Valgrind memcheck on the runtime: clean in a passing start. All consistent with a write from a library none of them instruments that needs an interleaving.
3. gdb on each start (20 starts, two CPUs pinned) caught one abort with every thread: the main thread in `malloc` under `query_mutter()`, the depth observer just past its first round of X calls, everything else idle.
4. A 60-line program in which four threads open an X display, query RandR and close it crashed in 10 of 10 rounds; memcheck with Debian's `-dbgsym` packages named the write, the free and the allocation in libXext.
5. Red and green: Debian's libxext source rebuilt unchanged still crashes the program 10 of 10; rebuilt with the fix it finishes 10 of 10 and memcheck reports 0 errors. The runtime +11 itself, unchanged, pinned to two CPUs, with the library given by `LD_LIBRARY_PATH`: with DisplayXR's 1 ms poll 4 failures in 20 starts (stock), 2 in 20 (rebuilt unchanged), 0 in 20 (fixed); without it 4 in 40 (stock), 0 in 40 (fixed).

The rig, the tools and their traps: [stereo-proof-rig: a diagnostic build with sanitizers](../../stereo-proof-rig/references/sanitizer-diagnostic-build.md).
