# A software-drawn X11 window declared full side by side

Learned on ORDER 88 (November 2026): a client that draws with XPutImage or XShm, no OpenGL and no Vulkan, declared `_KDE_NET_WM_STEREO_CONTENT` = 3, on Stereo KWin +stereo3d43 and +stereo3d46 under Xwayland.
The result first: it works, on the anaglyph twin (each view to its eye) and on the plain 2D output (the left view), at any size.
KWin sees only the window's surface through Xwayland, so what draws the window does not matter; the program's contract does.

## Recipe

1. Create the window at one view's size (W by H).
2. Read the root's `_KDE_NET_WM_STEREO_CONTENT_SUPPORTED`; at 3 or more call `stereo_declare_x11_format(display, window, STEREO_SBS_FULL)` (libstereo-declare, from support version 1; `stereo_declare_x11()` from 2 when the kind of content is known). Below 3, say the window is shown flat.
3. Map it. Stereo KWin makes the X window two views wide (`xwininfo` says 2W by H) and shows it at W by H.
4. Draw the picture at the X window's size: left view in the left half, right view in the right half, each at its own resolution. Redraw on every real `ConfigureNotify` and on `Expose`; the doubling can arrive late.
5. Take the size only from the events the X server sent. After each configure KWin sends a second, synthetic `ConfigureNotify` (`send_event` set) in the program's own units, one view wide. Ignore it, or read the real size with `XGetGeometry`.
6. At support 10 or more, KWin also writes `_KDE_NET_WM_STEREO_DEPTH_LIMITS` on the declared window (`CARDINAL/32`, two `wl_fixed_t` values: sunk then popped, pixels of a view 1920 wide, for the output the window sits on). Select `PropertyChange`, read it on each notify, and draw inside it; the reference `vr-to-3d/references/pose-and-separation-on-a-3d-screen.md` has the traps.

## Proof, per eye

Fixture: left half solid red with a white L, right half solid blue with a white R, a white one-pixel border round each half, so a swap, a squeeze and a one-eye-only result each show.
Session: Stereo KWin with Xwayland, the output in its anaglyph twin (`kscreen-doctor output.Virtual-0.mode.5`) and then in the plain 2D mode (mode 1), one fresh session per case.
Read, in this order:

- the declaration and the doubling: `xprop -name NAME _KDE_NET_WM_STEREO_CONTENT` is 3 and `xwininfo -name NAME` is twice the created width;
- KWin's own frame and buffer geometry from a KWin script (`workspace.stackingOrder`, `frameGeometry`, `bufferGeometry`): one view's size;
- two ScreenShot2 captures: on the anaglyph twin the capture is two eyes side by side, left first, and the rectangle must be red in the left eye and blue in the right eye, with no pixel showing them swapped and nothing differing between the eyes outside the rectangle; on the 2D output the rectangle is red (the left view) and no blue.

Negative controls that must fail or differ:

- undeclared: both eyes show the same squeezed picture, red then blue, in the window's own size;
- a client that trusts the last `ConfigureNotify` it received (the synthetic one): the left eye shows the whole packed picture, red and blue, and the right eye shows nothing.

## Traps

- **Symptom:** the whole packed buffer (red and blue side by side) in the left eye, the right eye empty, on a declared software-drawn window. **Cause:** the client redrew at the synthetic `ConfigureNotify` size (one view) into an X window that is two views wide, so only its left half was painted. KWin shows that half to the left eye and the unpainted right half to the right eye, as designed; it is not a compositor fault. **Fix:** size the picture from the X server's own event or `XGetGeometry`, never from the synthetic one. **Found by:** `xwininfo` said 2W while the client's log said W, and the negative control above reproduced the symptom exactly.
- **Symptom:** the picture is right only after a second or two. **Cause:** the doubling can arrive late when KWin's main thread is busy; a program that draws once never redraws. **Fix:** redraw on `ConfigureNotify` and `Expose`; capture only after the window has its doubled width.
- A colour check passes on a window that is the right colour in the wrong place: check the rectangle from KWin's buffer geometry, not from where the program asked for the window.
- Qt's xcb raster backing store and other toolkits that read their size from the last event are not covered by this recipe; check them with the same controls.
