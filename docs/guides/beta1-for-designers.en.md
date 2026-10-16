# Sparky Stereo OS beta 1 for designers and 3D artists

You can see the whole desktop in 3D on the screen you already own, explore stereo photos and video, and judge how depth changes the way a desktop feels.
This beta is a working desktop for creative people, with clear limits on which creative applications and theme features are ready today.

Sparky Stereo OS, Daniel Ramos's edition of SparkyLinux (by Paweł "pavroo" Pijanowski)

## Get the image

The image is sparky-stereo-os-9-mashtabba-beta1-x86_64.iso; the download link goes to beta testers: ask for it in the [beta tester thread](https://github.com/Sparky-OS/sparky-stereo-os/issues/26).
It is about 5.2 GB and needs a USB stick of at least 8 GB.

SHA-256: `3564fc23315117bb552543235e889e5a398c9cf13e41ec0cceb6086ff43a25ab`.
SHA-512: `cd7c3da5ae699b951471a4c9d6e7443f5a8944fd7eb3a0f2f7d311c96275689be1e056c0ea96296f4ffd75ba4c3b21a5d79c499bb8a34e43b7d89784a35bd377`.

On Windows, run `certutil -hashfile <file> SHA256` and compare the result with the SHA-256 above.
On Linux, run `sha256sum <file>` and compare the result with the same value.

## What you can make and see today

The desktop itself has three depth planes: the active window sits at the screen, its menus and tooltips pop forward, and the wallpaper and background windows sink behind it.
The depth is subtle, only a few pixels, and you can set its limits in System Settings under “3D Depth”.
The stacking order matches the flat desktop, so a pile of windows reads as a pile while the active window stays in front.
These desktop depth rules are built and shipped in beta 1.

![The desktop shown in red and cyan anaglyph](images/beta1/anaglyph-desktop.jpg)

On a normal monitor, enable “Anaglyph” for that screen and use red and cyan glasses.
A 3D television can use one of its own HDMI 3D modes, and Stereo KWin converts the same desktop image for each screen.
The display settings screenshot shows the per-screen stereo controls.

![Per-screen stereo output controls](images/beta1/display-settings.jpg)

Dolphin shows stereo photo previews, and Gwenview opens stereo photos such as MPO, JPS and stereo PNG.
Spectacle keeps both eyes when it captures a stereo window.
The mpv and Bino players handle 3D video, with FFmpeg carrying stereo signals through video formats.

The image also includes GIMP and Calligra Words.
The default look, Sparky Stereo, is built on KDE's Oxygen style with the Oxygen Dark colours.
The theme guide describes how the sunk, screen and popped planes shape a theme, while Stereo Oxygen and its paired stereo icons are still being made.

## Theme work and current limits

For a theme, the built rules are the depth range chosen by the user, the active window at the screen, menus and tooltips in front, and the wallpaper and background windows behind.
Shadows follow the plane they fall on, and the pointer follows the item beneath it.
Theme work that depends on scaled depth elements, stereo icons, special depth effects or 3D video backgrounds is described as designed or coming, so do not treat it as shipped in beta 1.
Read [Depth on the desktop](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/depth-on-the-desktop.md) and [For theme designers and customizers](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/for-theme-designers.md) for the current rules and their status.

Blender, Krita, Kdenlive and Marble are not included in beta 1.

## Try it, then install if you want

Write the ISO to a USB stick and start the live session to try the desktop before installing.
The tested USB paths are `dd` on Linux and Ventoy; Rufus itself was not run, though its DD Image mode is the same raw copy as the tested `dd`.
To install beside Windows, start in UEFI mode, leave at least 30 GB of unformatted free space after shrinking the Windows partition in Windows, then use “Replace a partition” on that free space.
Windows' own fallback loader remains unchanged in the tested dual-boot path.

## Known beta 1 issues

Machines with 32-bit UEFI, mostly older Atom tablets, do not boot this image.
MokManager's first “Press any key” screen times out after about 10 seconds.
The installer slides are in English even when the installer is set to German or another language.
The GRUB menus still show SparkyLinux's blue atom, Quick Settings still offers Breeze and Breeze Dark, and KDE's Welcome Center opens beside Sparky Welcome at first login.
The edition's own package repository is not online yet, so apt reports that source as unreachable while Debian, SparkyLinux and deb-multimedia updates work.
A live USB is slower than an installed system.

## Tell us what you find

Use [issue #26 in English](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) to report what worked or what got in your way.
Include your computer, graphics card and display models, the steps you took, what you expected, what happened, and screenshots when they help.
