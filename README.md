# Sparky Stereo OS

**Create and explore in 3D on the screen you already have: paint, edit photos and video, study molecules and globes, then watch films and play games.**
A 3D TV works, and so does any ordinary monitor with cheap red-cyan glasses.
Sparky Stereo OS, Daniel Ramos's edition of SparkyLinux (by Paweł "pavroo" Pijanowski), is a Linux system with the KDE Plasma desktop.

<a href="#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="49%" alt="DOOM (2016) in a window, in 3D, with the flat Plasma panel below it (red-cyan anaglyph)"></a> <a href="#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="49%" alt="Marble's globe in front of the stars, in 3D (red-cyan anaglyph)"></a>

*Red-cyan glasses show these in 3D ([more](#seen-in-3d)).*

**In development:** nothing to download yet.

- **[Create](#create):** paint in 3D and in deep colour (16 bits per colour instead of 8), and edit 3D photos and video.
- **[Science and engineering](#science-and-engineering):** Marble's globe, KAlgebra's plots and Kalzium's molecules in 3D; 3D models and circuit boards are in progress.
- **[Watch and play](#watch-and-play):** 3D films, photos and games, in a window or full screen.
- **[Develop](#for-developers):** make your program 3D once; the desktop adapts it to each screen.
- **[Another distribution?](docs/other-distributions.md)** Why we do not package for it, and how its maintainers can adopt our fixes.

**Next step: tell us about your 3D gear** and hear first when it is ready.
Sign up in your language: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

## Create

**Paint, edit photos and edit video in 3D, and paint in deep colour: 16 bits per colour instead of 8.**
- **Painting:** Krita paints on a 16-bit canvas, and on a 3D canvas with 16 bits in each eye.
- **Photos:** digiKam and Showfoto show 3D photos in the album, the light table, the slideshow and the editor; KolourPaint edits a 3D picture and saves it with its 3D mark.
- **Video:** in Kdenlive a clip knows its 3D layout, the monitors can show it in 3D, and the render keeps the 3D mark.

Each program in full: [Programs](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

### For theme designers and customizers

**On this desktop, depth is a design material.**
The planes, the limits and the rules every theme keeps are set; effects with their own depth and 3D backgrounds behind the windows are coming.
What is built, what is designed, and an example theme in words: [For theme designers and customizers](docs/for-theme-designers.md).
Ideas, sketches and side-by-side mockups are welcome in the [themes issue](https://github.com/Sparky-OS/sparky-stereo-os/issues/78).

## Science and engineering

**Study and design in 3D: a globe, plots and molecules work in 3D today, and 3D models and circuit boards are in progress.**
- **Learning and science:** Marble's globe, KAlgebra's plots, Kalzium's molecules and the Kubrick cube, in 3D by default on a 3D desktop.
- **3D models and circuit boards:** 3D previews in OpenSCAD, KiCad and F3D are in progress.

Each program in full: [Programs](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

## Watch and play

**3D films, photos and games show in 3D in their own window or full screen, and the rest of the desktop stays as it is.**
- **Screens:** a 3D TV, monitor or projector, the HDMI 3D sets of 2010 to 2013 included, or any ordinary monitor with red-cyan glasses; each screen can show a different kind of 3D at the same time.
- **Films:** 3D videos play in 3D in Haruna, VLC, mpv, PlasmaTube and more.
- **Photos:** Gwenview, digiKam and KolourPaint show 3D photos (MPO, JPS and stereo PNG) in 3D.
- **Games:** DOOM (2016) in a window and Half-Life 2, both through a VR mode ([the formula](docs/formula.md)).

Each program, what it gains and how it was proven: [Programs](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

### Seen in 3D

The two pictures at the top are screenshots taken with the edition's Spectacle, which keeps both eyes.
Red-cyan glasses show them in 3D here; the MPO files open in 3D in the edition's photo programs and on a 3D television.

- **DOOM (2016) in an ordinary window** ([MPO](docs/screenshots/doom-2016-in-a-window.mpo)), based on [KHARVOX](https://github.com/CactusVRStudios/KHARVOX), CactusVRStudios' DOOM (2016) VR conversion mod (MIT): the game has depth while the panel and the window frame stay flat in both eyes. Measured between the eyes: the nearest rock 23 px apart, the far mountains 1 px, the panel 0 px.
- **Marble's globe** ([MPO](docs/screenshots/marble-globe.mpo)): the Earth in front of the screen (+11 px) and the stars behind it (-12 px), the side panel flat. This shot predates fixes made since, which a newer one will show.

## Depth on the desktop

**The desktop itself gets a little depth, on every screen: built, and coming with the next KWin package.**
**Three places, declared: sunk, screen and popped.** All subtle, a few pixels, within the limits you set (System Settings, "3D Depth").
The active window sits at the screen, its menus and tooltips pop, and the wallpaper and the windows behind sink; everything in between follows the stacking order, so a pile of windows reads as a pile of papers.
Pop is designed as a little scale and a little depth together, and on a 2D screen as the same scale plus a small move up and to the left.
<a id="the-desktop-cube-what-one-format-makes-possible"></a>The details, and the Desktop Cube built on the same standard: [Depth on the desktop](docs/depth-on-the-desktop.md).

## For developers

**Make a program 3D once: hand the desktop both eyes, and it takes care of every screen.**
You can write and check the work on the screen you already have.
- [Develop 3D and XR on an ordinary monitor](docs/develop-3d-on-an-ordinary-monitor.md): hand Stereo KWin two eyes once and see them in anaglyph on any monitor; the real screen is the last check.
- [House formats](docs/house-formats.md): one format inside the system for each medium, converted only where it enters and where it leaves.
- [Stereo labor division](docs/stereo-labor-division.md): who does what from the program to the screen, tied to the specifications.
- [Test stereo without a 3D TV](docs/test-stereo-without-a-3d-tv.md): a virtual display that speaks HDMI 3D, step by step, for driver, compositor and program developers.
- [A virtual machine with a 3D display](docs/stereo-vm.md): a QEMU guest with HDMI 3D modes, shown in stereo on Stereo KWin.
- [vkms-stereo-bench](tools/vkms-stereo-bench/README.md): each eye read back pixel by pixel in a VM, no 3D display needed; a ready root file system with Stereo KWin is on [our repository server](https://repo.sparkyos.org/bench/kwin-root/).
- [Skills](skills/README.md): instructions for people and AI assistants working on the edition and the programs it changes.

## How it works

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**In short: every program hands the desktop both eyes the same way, and the desktop converts them for each screen.**

**The standard in three lines.**
- **Stereo KWin** (KDE Plasma's compositor, with our stereo changes) speaks full side by side, at any resolution.
- **Programs** decode or generate stereo in any standard, and deliver full side by side, at any resolution, to Stereo KWin.
- **Outputs** (Stereo KWin's filters at the end, one per kind of screen) convert from that to whatever each screen needs.

That is what makes stereo work across GPUs, across monitors (2D ones included) and across every 3D output format.

**One picture, any screens, any GPUs.** One mirrored desktop on two 3D televisions at once, frame packing at 30 Hz from an AMD integrated GPU and top and bottom at 60 Hz from an NVIDIA RTX 3060, both in 3D. The program drew one full side-by-side picture; each output converted it for its own screen. It takes both halves: our driver changes, which give amdgpu and NVIDIA's open kernel modules the HDMI 3D modes, and this one-format contract.

Why one format, why full side by side, and why it is how Linux already handles sound: [How it works](docs/how-it-works.md).

## Stereo in the open stack, not in one product

Elsewhere, stereo is tied to one product: one headset, one vendor's injector, one vendor's kernel.
Here it is a property of the open layers (KDE, the kernel, the file formats), so it reaches the screen you already own: [Stereo in the open stack](docs/open-stack.md).

## Programs the edition changes for stereo 3D and deep colour

**One contract for every program: it hands the desktop both eyes, full side by side, and KWin's outputs decide how each screen shows them.**
- **The display path** (8): the kernel, Mesa, NVIDIA's open modules, egl-wayland, Xwayland, KWin, KScreen, the Wayland protocols.
- **Video** (14): FFmpeg, mpv, Haruna, VLC, Kdenlive, PlasmaTube, MKVToolNix and more.
- **Science and engineering** (12): Marble, KAlgebra, Kalzium, KiCad, OpenSCAD, GNU Octave and more.
- **Images** (9): Krita, Spectacle, Gwenview, digiKam, KolourPaint, the shared stereo layer and more.
- **Simulators and their rigs** (2): every raw control of a home cockpit in System Settings, and joysticks past 80 buttons (planned).
- **System** (2, and one fix beyond stereo): a stereo and deep colour page in KInfoCenter, the Cushion Swap File.
- **Not done yet** (2): Blender, and MAME with the emulators of 3D consoles.

Each program, what it gains and what we found on the way: [Programs](docs/programs.md).

## Our branches on KDE's GitLab

Every KDE change is a branch of our fork on [invent.kde.org](https://invent.kde.org/danielcamposramos), tested by KDE's own CI before it is proposed upstream: [the branches and their CI results](docs/kde-branches.md).

## Merged outside Sparky Stereo

Where a program breaks stereo or deep colour on the way to the screen, the fix goes to that program's own project, in its own style.
- **HandBrake** ([#8100](https://github.com/HandBrake/HandBrake/pull/8100), 16 September 2026): x264 encodes declare their 3D packing.
- **Universal Media Server** ([#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330), 19 September 2026): 3D video stays declared through transcoding.
- **MKVToolNix** ([ebd8445b](https://codeberg.org/mbunkus/mkvtoolnix/commit/ebd8445b1185d35d6bdbb9c1463757fbc9aa7c29), 21 September 2026): Matroska StereoMode from the H.264 stream.
- **MKVToolNix, HEVC** ([70889f220e](https://codeberg.org/mbunkus/mkvtoolnix/commit/70889f220e), 11 October 2026): the same from the HEVC stream.
- **mpv** ([#18490](https://github.com/mpv-player/mpv/pull/18490), 23 September 2026): the 3D layout read from the stream itself.
- **Teams for Linux** ([#3070](https://github.com/IsmaelMartinez/teams-for-linux/pull/3070) by its maintainer, Ismael Martinez, from our report, 7 October 2026): the app starts on a minimal Debian or Ubuntu.
- **Qt Multimedia** ([778399](https://codereview.qt-project.org/c/qt/qtmultimedia/+/778399), 8 October 2026): HDR video tone mapped against its real peak.
- **spice-gtk** ([!159](https://gitlab.freedesktop.org/spice/spice-gtk/-/merge_requests/159), 10 October 2026): a display channel crash fixed.

Each one in full, and what is in review: [Merged outside Sparky Stereo](docs/upstream-merges.md).

## Documents

- [The VR-engine-to-3D-display formula](docs/formula.md): what a VR engine changes to drive a 3D display instead of a headset, worked out on Half-Life 2.
- [KWin stereo first runs, 2026-10-01](docs/first-runs/kwin-2026-10-01/README.md): the first stereo 3D outputs from KWin on real displays, with photos, logs and the scripts used.
- [Stereo 3D: carry the signal to the screen](docs/talks/2026-10-13-w3c-me-ig.md): slides for the W3C Media & Entertainment Interest Group call, 13 October 2026 ([HTML](https://repo.sparkyos.org/talks/2026-10-13-w3c-me-ig/)).

## Tools

- [vkms-stereo-bench](tools/vkms-stereo-bench/README.md): stereo modes on a virtual display, each eye read back pixel by pixel, for driver, compositor and application developers.
- [hibernate-bench](tools/hibernate-bench/README.md): hibernation under UEFI Secure Boot and a software TPM 2.0 in QEMU, with throw-away keys and nothing installed on the host.

## The base: three open lists

The research behind this edition is public, in three curated lists anyone can copy (CC0):
- **[awesome-stereoscopy](https://github.com/danielcamposramos/awesome-stereoscopy)**: stereo 3D formats, standards, tools, players, displays and headsets, and 190 years of history, from Wheatstone's 1838 stereoscope to spatial video.
- **[awesome-linux-hdr](https://github.com/danielcamposramos/awesome-linux-hdr)**: Linux HDR and deep colour from the specification to the photons: standards, drivers, compositors, applications and measurement.
- **[awesome-vr](https://github.com/danielcamposramos/awesome-vr)**: virtual reality: headsets, open runtimes, standards, media formats, comfort and accessibility, and sixty years of history.

## Credit

Sparky Stereo OS, Daniel Ramos's (Capitain Jack) edition of SparkyLinux (by Paweł "pavroo" Pijanowski).

**Version:** Sparky Stereo OS 9 "Mashtabba", based on Debian 14 "Forky", KDE Plasma only.

Everyone this edition stands on, by name: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**Cite it:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

<a href="https://sourceforge.net/p/sparkyos/"><picture><source media="(prefers-color-scheme: dark)" srcset="https://sourceforge.net/sflogo.php?type=18&amp;group_id=3189517"><img alt="SparkyOS on SourceForge" src="https://sourceforge.net/sflogo.php?type=17&amp;group_id=3189517" width="200"></picture></a>

## Licence

The documents are licensed under the [Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): share and adapt them, giving credit to Sparky Stereo OS.

The scripts under `docs/first-runs/` and the tools under `tools/` are code and are licensed under the GNU General Public License, version 2 or later (GPL-2.0-or-later); see [LICENSE-GPL-2.0](LICENSE-GPL-2.0).
