# A declared child window: its depth limits and its first pair (ORDER 17, milestone 5 round 2)

A program whose 3D area is a child window (CloudCompare, gmsh's FLTK view, Togl in Netgen, ParaView's render view, a Qt window that embeds a GLX child) declares the child, not its top level. This page is what Stereo KWin, Xwayland and Mesa owe such a child and how each part was found. Written 2026-11-18 from KWin 6.7.4-2+stereo3d59, Mesa 26.1.6-1+stereo3d26 and Xwayland 24.1.15-1+stereo3d3, measured in the proof rig (kwin_wayland --virtual --xwayland, AMD render node).

## Recipe

1. The child lists itself in its top level's `_KDE_NET_WM_STEREO_CONTENT_CHILDREN` and declares `_KDE_NET_WM_STEREO_CONTENT` 3 on itself (Mesa's GLX does both at the first swap).
2. Stereo KWin (declaration support 11 on the root, `_KDE_NET_WM_STEREO_CONTENT_SUPPORTED`) redirects the child and then writes `_KDE_NET_WM_STEREO_DEPTH_LIMITS` on it: CARDINAL/32, two values, sunk then popped, 24.8 fixed point, pixels of a view 1920 wide (2560 1024 = 10 and 4). It writes again when the person's limits, the output or the child list change, and deletes it when the child's declaration or the child goes. The top level gets no property of its own unless it declares itself.
3. The program reads it from the child, never from the top level: `stereo_depth_x11_get_limits(display, child, &limits)` and `XSelectInput(child, PropertyChangeMask)` (see [depth-limits-declare.md](depth-limits-declare.md)). `-ENODATA` means offered, not delivered yet: a program that draws once says so or waits for the event; it never invents a separation.
4. Mesa's GLX, on DRI3 and the software path, waits for that property (at most half a second) before the first present of a declared child, when the root announces support 11 and the window is not a top level. `LIBGL_DEBUG=verbose` prints `stereo child 0x...: the compositor took the child after N us`; a compositor that does not answer is said on stderr and the presents go as before.
5. Mesa's pair rule (ORDER 561b: one copy tolerated, two take the declaration back, three flips return it) ignores a completion with mode SUBOPTIMAL_COPY: it is neither a copy nor a confirmed flip (EGL on X11, the Vulkan stereo layer and both GLX paths).
6. A Wayland subsurface that declares stereo content and follows the depth (`kde_stereo_depth_v1`) gets the limits as a top-level does, also when it starts following after its window is shown (s59-0003).

## Proof (rig, one fresh session per row, AMD, no redraw sent)

| Stack | Toy child (`scripts/glx-child-first-pair.c`, one swap at once) | gmsh -stereo | CloudCompare, Enable 3D once |
|---|---|---|---|
| Published (KWin +58, Mesa +25) | flat and told, 3 of 3 | not run | 2 pairs of 5, 3 flat and told; no limits on the child, the "no limits" sentence |
| KWin +59, Mesa +25 | 1 pair of 6 | flat and told, 3 of 3 | 2 pairs of 3, limits on the child |
| KWin +59, Mesa +26 with only the wait | 3 of 5 | | |
| KWin +59, Mesa +26 | 10 of 10 | 5 of 5 | 10 of 10, limits 2560 1024 on the child, rows -2/+1 at 10/4 and -4/+2 at 20/8 (predicted -1.92/+1.08 and -3.83/+2.16) |

## Traps, symptom first

- **Symptom:** the child never gets `_KDE_NET_WM_STEREO_DEPTH_LIMITS`; `stereo_depth_x11_get_limits` answers `-ENODATA` for ever on a KWin that announces 10.
  **Cause:** s52-0001 (KWin +stereo3d52, "Tell a window that declares stereo content the depth limits of its output") wrote the property on the window that declares only; `X11StereoChildren` tracked the children but nothing wrote on them.
  **Fix:** `X11Window::updateStereoDepthLimits()` writes on every tracked child that holds content, `X11StereoChildren::unwatch()` deletes it, the child list change schedules the update, and the announced support is 11 (s59-0001). Test `testStereoChildWindowDepthLimits`, red on +58 and green on +59.
  **How found:** reading the one writer, then `props2.py` on the child (the property list of every window of the tree) in a session of +58.
- **Symptom:** a declared Wayland subsurface that asks for the depth after its window was shown gets no `depth_limits`.
  **Cause:** `StereoDepthStates` watches only the top-level surface's `stereoDepthFollowed()`; a subsurface's follow scheduled nothing.
  **Fix:** the follow is announced up the subsurface tree (s59-0003); test `testLimitsOnDeclaredSubsurface` (s59-0004), red on +58, green on +59.
  **How found:** the test written to check the Wayland side was red on both.
- **Symptom:** a program that draws once (or draws on demand) shows its child flat, Mesa says "is shown flat", and nothing brings it back; the 3D area is a pair only after the program makes a new drawable.
  **Cause, two parts.** (a) Mesa declares at the first swap and presents at once; Stereo KWin redirects the child some tens of milliseconds later and Xwayland gives it a surface only then, so the first presents are real copies (`xwl_present_check_flip` reason 1, no surface). (b) The first flip on the new surface completes as SUBOPTIMAL_COPY while the compositor's dmabuf feedback is unread (`xwl_present_maybe_set_reason`); when both feedback flags are set the second flip does too; Mesa read the mode as a copy and two such took the declaration back although both pictures had reached the surface. A flat child never flips, so the three flips that should bring it back never come.
  **Fix:** (a) the first present of a declared child waits for KWin's limits property (patch 0043); (b) SUBOPTIMAL_COPY is not a copy for the pair rule (patch 0044). The rule of ORDER 561b is unchanged: a real copy still counts, one is tolerated, two take the declaration back. Test: `tests/glx-child-first-pair.c` with `check-glx-child-first-pair.py` (red on Mesa +25, green on +26).
  **How found:** the toy child with `EARLY=1` (the declaration written before the swap) was a pair when the swap came 80 ms later and flat at 30 ms: a race. Then Xwayland rebuilt with a print in `xwl_present_check_flip`, `xwl_present_flip` and `xwl_present_flip_notify_vblank` for non-top-level windows (`scripts/xwayland-print-present-decisions.txt`): old Mesa gave four COPY decisions with reason 1; Mesa with the wait gave FLIP with mode 3 on the first present and sometimes on the second. With the wait and Xwayland made to report mode 1 for children the toy was a pair 10 of 10, which isolated the two parts.
- **The wait looks long in a log.** It is 20 to 50 ms on a loaded rig and 1 to 4 ms idle; it is once per drawable declared.
- **A property written by KWin is not "KWin holds the surface".** The limits arrive after the redirect request is on the connection, which is enough for the child to be flippable by the time the program presents; it is not an acknowledgement of the surface serial (a CI Xwayland never associates one), so no test waits for a surface.
- **A rig session under load flatters or hides the race.** Under four builds the threshold of the early declaration moved from 30 to 80 ms; count runs on a quiet machine and report the count, not one picture.
- **`dpkg -i` of the Mesa set into a rig image installs five packages** (the ones the image has). `libgl1-mesa-dri` carries `libgallium`, so the GLX library and the driver always travel together.
- **Quick GLX-only builds do not stand in for the package.** A meson build of `libGLX_mesa` alone (softpipe, no radeonsi) offers "no stereo visual"; use it only to compile-check a GLX change, then build the package.
