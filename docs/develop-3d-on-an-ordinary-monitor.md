# Develop 3D and XR on an ordinary monitor

**For developers of 3D and XR programs:** write and check stereo 3D work on the screen you already have.
The real 3D television, headset or glasses-free panel is the last check, of work that is already right.
This page puts the pieces in the order you would use them.

## 1. Hand Stereo KWin two eyes, once

**The contract:** full side by side, left eye first, both eyes complete, at your resolution, declared once to the compositor.
Everything after that, every kind of screen, is Stereo KWin's job.
The rules, with their specifications: [house formats](house-formats.md); the design in one page: [STEREO3D.md](https://invent.kde.org/danielcamposramos/kwin/-/blob/stereo3d/STEREO3D.md).

**Three ways to get there:**
- **Ask the graphics API for stereo:** OpenGL quad buffer, an EGL multiview window or a two-layer Vulkan swapchain. The edition's Mesa packs the two eyes into one full side-by-side picture and declares it for you.
- **Draw both eyes yourself:** put them side by side in one surface, a window or a subsurface, and declare it with `kde-stereo-content-v1` ([plasma-wayland-protocols](https://invent.kde.org/libraries/plasma-wayland-protocols)). The shared declaration library does it for Wayland and for X11.
- **Pictures:** the shared stereo layer (`libstereo-layer1`) shows a stereo photograph in a window, from the file's own mark.

A 2D interface stays 2D: keep the 3D area in its own surface, and the rest of the window is the same in both eyes.

## 2. See it on any monitor

**Anaglyph:** Stereo KWin's anaglyph output shows the same full side-by-side picture on any ordinary monitor, with red and cyan glasses.
Choose it for that screen in System Settings, Display Configuration, in the screen's Resolution list.
Your program does not change: it still hands over full side by side, and the output decides.

**Several screens:** each screen can run a different 3D output at the same time, for example anaglyph on your monitor and HDMI 3D on a television.
That holds for a mirrored screen too, even across two GPUs: tested on two Sony 3D televisions showing one copied screen, one on an AMD integrated GPU in frame packing at 30 Hz and the other on an NVIDIA RTX 3060 in top and bottom at 60 Hz, both in 3D.

## 3. Test the real HDMI 3D path without a 3D television

**[vkms-stereo-bench](../tools/vkms-stereo-bench/README.md):** a kernel's virtual display driver (VKMS) is given the EDID of a 3D television in a virtual machine, so the 3D modes can be set and each eye read back pixel by pixel. It runs with KUnit, IGT's `kms_3d` and Stereo KWin.
**The step-by-step guide:** [Test stereo without a 3D TV](test-stereo-without-a-3d-tv.md).
**Stereo KWin, ready to use:** the bench's compositor phase needs a root file system with Stereo KWin, published on [our repository server](https://repo.sparkyos.org/bench/kwin-root/) with the source packages of everything modified in it; `tools/build-kwin-root.sh` builds one yourself.

## 4. A 3D display inside a virtual machine

**[A virtual machine with a 3D display](stereo-vm.md):** a QEMU guest with HDMI 3D modes, shown in stereo on Stereo KWin in QEMU's own window, virt-viewer and Karton.
Use it when you are writing an operating system's or a driver's stereo code and have no 3D display.

## 5. Glasses-free panels

**[DisplayXR](https://github.com/DisplayXR/displayxr-runtime)** is the open runtime for spatial (lenticular) displays.
Its simulated display can draw interlaced output (`SIM_DISPLAY_OUTPUT=interlaced`), which makes placement and scaling errors visible on an ordinary monitor.
Stereo KWin will publish window geometry to DisplayXR, so its apps run on Plasma with each vendor's own weaver; the design is agreed in [displayxr-runtime#1928](https://github.com/DisplayXR/displayxr-runtime/issues/1928).
The panel itself is the last check.

## 6. Phones and Android

**A phone as a 3D screen:** [Flat Headset](https://github.com/Sparky-OS/flat-headset) puts a phone in a Cardboard-style viewer as a 3D screen for the desktop, through a KWin output in the headset's mode, KRdp and KDE Connect.
[StereoDroid](https://github.com/Sparky-OS/stereodroid) makes the same phone a headset for SteamVR on Linux, with head tracking.
Both are planned.
**Android apps:** Android's own media framework learns the frame packing marks of 3D video in [androidx/media#3439](https://github.com/androidx/media/pull/3439), in review.
The same rule holds there: a program hands over two eyes, and the screen it lands on decides how they are shown.

## 7. Headsets

**KDE's own VR Mode** ([KWin merge request 8671](https://invent.kde.org/plasma/kwin/-/merge_requests/8671), a draft) puts the Plasma desktop into a headset through OpenXR, on Monado or WiVRn.
On a flat screen, the same two eyes your program hands over are what a headset shows.

## 8. Then the real screen

Check the finished work on the real 3D television, headset or panel.
By then it is right on the bench and right in anaglyph, so the real screen confirms; it does not debug.

Sparky Stereo OS, Daniel Ramos's edition of SparkyLinux (by Paweł "pavroo" Pijanowski).
