# vk-views: one surface, swapchains of two views and of one

A Vulkan client that keeps one window and one `VkSurfaceKHR` and makes a timed sequence of swapchains with two image layers or one on it, as a program that turns its 3D off and on again does.
It tells a declaration that outlives its pair (the window shown as two halves) from a right withdrawal, on Wayland and on X11, through Mesa's own presentation or through the Vulkan stereo layer.

Build (Debian testing: `libvulkan-dev`, `libwayland-dev`, `libxcb1-dev`, `wayland-protocols`):

```sh
x=/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml
wayland-scanner client-header $x xdg-shell-client-protocol.h
wayland-scanner private-code $x xdg-shell-protocol.c
cc -O1 -Wall -I. -o vk-views vk-views.c xdg-shell-protocol.c -lvulkan -lwayland-client -lxcb
```

Run it in a Stereo KWin session whose output is in a side-by-side 3D mode (the rig of [stereo-proof-rig](../../SKILL.md)), capture with `capture.py` at moments inside each phase, and read the captures with `views.py CASEDIR` (it reads `shot-N.png` and the times in `shots.txt`):

- `PHASES="2:4,1:4,2:4,1:0"`: views and seconds per phase; the last lasts until the program is stopped.
- `OLD=0`: destroy the previous swapchain before the next one instead of naming it `oldSwapchain`. Run both: the two orders take different paths in a layer.
- `X11=1`: an X11 window through Xwayland; the client then prints its window's `_KDE_NET_WM_STEREO_CONTENT` every second (`x11 declaration 3` or `0`).
- `VK_VENDOR=0x10de`: NVIDIA's device (the Vulkan stereo layer serves it); `VK_DRIVER_FILES` picks a Mesa driver.

What `views.py` prints for each capture: `PAIR` (left eye red, right eye blue), `FLAT` (each eye holds the one picture whole: green left half, yellow right half), `HALVES` (left eye green only, right eye yellow only: the one picture shown as a pair), `OTHER` (anything else, such as the one picture mixed with the last pair), `NONE` (no window found).
A right run reads `PAIR FLAT PAIR FLAT`, and on X11 the declaration follows: `3`, `0`, `3`, `0`.

`seq-session.sh OUTDIR` runs several programs one after the other in one fresh Stereo KWin session (`SEQ="APP|VAR=V;APP|..."`, each for `RUN` seconds, from a folder mounted at `/bin-fx`) and lists the person's kept problems after each: the way to prove that a problem is told once for several programs and ends when a pair works.
