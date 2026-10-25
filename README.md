# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇫🇷 [Français](README.fr.md) · 🇰🇷 [한국어](README.ko.md)

**Create and explore in 3D on the screen you already have: paint, edit photos and video, study molecules and globes, then watch films and play games.**
A 3D TV works, so does any ordinary monitor with cheap red-cyan glasses, and now a compatible Android phone in an inexpensive viewer: a [usable stereo desktop over USB](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md), tested on older hardware.
Sparky Stereo OS, Daniel Ramos's edition of SparkyLinux (by Paweł "pavroo" Pijanowski), is a Linux system with a new Stereo KDE Plasma desktop.

**Read the architecture:** [illustrated guide and repository map](docs/architectural-synthesis.md), with a [full-size infographic and text version](docs/architecture-infographic.md), adapted and checked from Daniel's Gemini / NotebookLM research.

<a href="#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="The Stereo Desktop in 3D with translucent windows: Dolphin's Settings menu and its colour-scheme list in front, the glass windows behind stepping back, the system monitor and the wallpaper deepest (red-cyan anaglyph)"></a>

**Stereo Desktop:** the desktop itself has depth.
What you are using sits at the screen and its menus come forward, like Marble's menu and sub-menu here, while the windows behind step back one after another, like papers in a pile, with the wallpaper deepest.
A 3D program keeps its own depth inside its window, like Marble's globe.
A few pixels each, within limits you choose.

<a href="#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) in a window, in 3D, with the flat Plasma panel below it (red-cyan anaglyph)"></a> <a href="#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="Marble's globe in front of the stars, in 3D (red-cyan anaglyph)"></a> <a href="#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="The Stereo Desktop in 3D: the panel at the screen, a sound pop-up in front of it, and the windows behind stepping back (red-cyan anaglyph)"></a>

*Red-cyan glasses show these in 3D ([more](#seen-in-3d)).*

**In development:** the [Flat Headset development APK and matching PC update instructions](https://github.com/Sparky-OS/flat-headset/tree/main/apk) are available, and a developer ISO for testers now starts on new PCs with Secure Boot on, on older BIOS PCs and on 32-bit UEFI machines; the final stereo edition ISO is still being prepared ([where it is going](#where-it-is-going)).

- **[Create](#create):** paint in 3D and in deep colour (16 bits per colour instead of 8), and edit 3D photos and video.
- **[Science and engineering](#science-and-engineering):** Marble's globe, KAlgebra's plots and Kalzium's molecules in 3D; 3D models and circuit boards are in progress.
- **[Watch and play](#watch-and-play):** 3D films, photos and games, in a window or full screen.
- **[Develop](#for-developers):** make your program 3D once; the desktop adapts it to each screen.
- **[Another distribution?](docs/other-distributions.md)** Why we do not package for it, and how its maintainers can adopt our fixes.

**Next step: tell us about your 3D gear** and hear first when it is ready.
<br>Sign up in your language: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

### VR is also a stereo monitor

Most headsets are a pair of small screens, one for each eye, and the rest split one screen in two, just as a 3D TV does, so this one desktop serves both.
- **The 3D screen already in your pocket:** an inexpensive Cardboard-style viewer turns a compatible Android phone into a screen for the stereo desktop, in full colour, with a separate view for each eye. On 19 October, Daniel accepted the USB half top-and-bottom setup on a Redmi Note 7 and a 2016 A10 laptop as usable: the desktop works and the mouse is responsive. Video is much improved but still somewhat choppy; the first home Wi-Fi test feels closer to USB, while Direct Wi-Fi has longer stalls. Full resolution and more devices still need testing ([measurements and limits](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md)). The PC does the drawing, giving an older phone another use. The [development APK, source and matching PC update instructions](https://github.com/Sparky-OS/flat-headset/tree/main/apk) are available together; update the development live USB or installed PC first. The Android viewer remains a test build. Photos of [the first test](https://github.com/Sparky-OS/flat-headset#the-first-test-12-october-2026) and [the desktop on the phone](https://github.com/Sparky-OS/flat-headset#the-desktop-on-the-phone-14-october-2026).
- **VR films:** Bino plays 360° and 180° films, flat or in 3D, on any 3D screen, and the mouse turns the view.
- **VR games:** Half-Life 2 and DOOM (2016) reach a 3D screen through their VR modes.

## Who builds it

Daniel, from a favela in Brasília, with two human contributors so far: Jeromy Streets, whose video wallpaper for Plasma ([org.kde.video](https://github.com/Sparky-OS/org.kde.video)) now lives in Sparky-OS with him as its maintainer, and Eff (effcol), who keeps iZ3D's code alive as [wiz3D](https://github.com/Sparky-OS/wiz3D) and maintains it here.
Stereo on Linux waited years for volunteers: earlier attempts stalled because reviewers had no 3D display, and the work spans the kernel, Mesa, KWin, FFmpeg, the players and the web standards.
No other developer came forward to carry it, so the other partners at work here are AI ones, directed and checked by Daniel and named in [AI provenance](docs/ai-provenance.md).
If you would rather see it built by human hands, you are more than welcome: every fork is public, and every task is open.
It is all built and tested on two ordinary machines, a home PC and a 2016 laptop: [the hardware](docs/hardware.md).
On that laptop, every desktop case holds 24 fps in 2D and 3D: [what stereo costs KWin, measured](docs/measurements/kwin-stereo-cost-a10-2026-10-23.md).

## Where it is going

The edition is the working proof, and what it finds goes back to open standards.
Daniel chairs the W3C [Procedural Memory Knowledge Representation Community Group (PM-KR)](https://www.w3.org/community/pm-kr/) with Milton Ponson.
Our report [Stereo 3D on Linux and the Web](https://www.w3.org/publications/spec-generator/?type=respec&url=https://raw.githubusercontent.com/w3c-cg/pm-kr/main/reports/source/stereo-3d-adoption-report.html) is there as an individual proposal, input for the group to discuss: which established specifications already carry 3D, what Linux and the web never adopted, and what a browser would need.
It is also the subject of our talk at W3C's Media and Entertainment Interest Group on 13 October 2026 ([slides](docs/talks/2026-10-13-w3c-me-ig.md)).
Joining the group is free with a W3C account, and help is welcome: test on your display, review the report, or bring your use case.

## Create

**Paint, edit photos and edit video in 3D, and paint in deep colour: 16 bits per colour instead of 8.**
- **Painting:** Krita paints on a 16-bit canvas, and on a 3D canvas with 16 bits in each eye.
- **Photos:** digiKam and Showfoto show 3D photos in the album, the light table, the slideshow and the editor; KolourPaint edits a 3D picture and saves it with its 3D mark.
- **Video:** in Kdenlive a clip knows its 3D layout, the monitors can show it in 3D, and the render keeps the 3D mark.
- **Stories:** [StorySplat](https://storysplat.com) ("Turn your 3D scans into interactive tours") builds tours inside 3D scans of real places, right in the browser, and its 3D View shows them in 3D on any of the registered outputs, first tested side by side on a Sony 3D television.

Each program in full: [Programs](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

### For theme designers and customizers

**On this desktop, a theme decides what pops and what dives:** [new frontiers for theme design](#depth-on-the-desktop).

## Science and engineering

**Study and design in 3D: a globe, plots and molecules work in 3D today, and 3D models and circuit boards are in progress.**
- **Learning and science:** Marble's globe, KAlgebra's plots, Kalzium's molecules and the Kubrick cube, in 3D by default on a 3D desktop.
- **3D models and circuit boards:** 3D previews in OpenSCAD, KiCad and F3D are in progress.
- **From the desk to the client, in full colour:** the same model in depth on a glasses-free 3D monitor at the engineer's desk (with [DisplayXR](https://displayxr.org), in progress), on a 3D TV or projector for a team or a training class, and on every worker's and client's own phone in a cardboard viewer ([Flat Headset](https://github.com/Sparky-OS/flat-headset)). It is open from end to end, so no one is tied to one display maker.

Each program in full: [Programs](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

## Watch and play

**3D films, photos and games show in 3D in their own window or full screen, and the rest of the desktop stays as it is.**
- **Screens:** a 3D TV, monitor or projector, the HDMI 3D sets of 2010 to 2013 included, or any ordinary monitor with red-cyan glasses; each screen can show a different kind of 3D at the same time, and glasses-free 3D monitors are in progress with the DisplayXR team.
- **Films:** 3D videos play in 3D in Haruna, VLC, mpv, Bino, PlasmaTube and more.
- **Photos:** Gwenview, digiKam and KolourPaint show 3D photos (MPO, JPS and stereo PNG) in 3D.
- **Games:** DOOM (2016) in a window and Half-Life 2, both through a VR mode ([the formula](docs/formula.md)).
- **A kernel tuned for play:** the edition runs Linux 7.3 with our stereo patches. Its new scheduler raised a game's lowest frame rate from 4 to 29 fps on an older CPU in its author's own test ([the numbers](https://lore.kernel.org/all/20260511113104.563854162@infradead.org/)), and it lets AMD cards with little video memory keep a game's memory on the card ([the change](https://pixelcluster.dev/VRAM-Mgmt-fixed/)).

Each program, what it gains and how it was proven: [Programs](#programs-the-edition-changes-for-stereo-3d-and-deep-colour).

### Seen in 3D

The pictures on this page are screenshots taken with the edition's Spectacle, which keeps both eyes.
Red-cyan glasses show them in 3D here; the MPO files open in 3D in the edition's photo programs, on any of the registered outputs. All of them, each with its red-cyan version and a direct MPO download: [the screenshot gallery](docs/screenshots/README.md). Daniel's own 3D photos from an LG Optimus 3D phone, 2014 to 2016, with the originals: [the photo gallery](docs/photos/README.md).

- **Stereo Desktop, translucent** ([MPO](https://raw.githubusercontent.com/Sparky-OS/sparky-stereo-os/main/docs/screenshots/translucent-stereo-desktop.mpo)), on the 3D TV, 15 October 2026. The windows are glass, so the pile shows through. Measured between the eyes: Dolphin, the focused window, 0 px, and its Settings menu +5 px (in front, at the user's popped limit); the long colour-scheme list 0 px, because it touches the top of the screen and a popped thing that touches the edge stays at the screen; Thunderbird behind -3 px; the system monitor widget and the wallpaper -10 px; the panel 0 px. The two email addresses are blurred in both eyes.
- **Stereo Desktop, a menu over a menu** ([MPO](docs/screenshots/stereo-desktop-dialogs.mpo)), on a 3D TV in frame packing, 13 October 2026. Measured between the eyes: the focused Marble window 0 px, its Settings menu +2 px and the Panels sub-menu +4 px, the four windows behind -3, -5, -8 and -10 px, the widgets and the wallpaper -10 px; inside the window, Marble's own 3D: the Earth's labels +12 px, the stars' -13 px. The messages in the Diolinux chat behind are blurred.
- **DOOM (2016) in an ordinary window** ([MPO](docs/screenshots/doom-2016-in-a-window.mpo)), based on [KHARVOX](https://github.com/CactusVRStudios/KHARVOX), CactusVRStudios' DOOM (2016) VR conversion mod (MIT): the game has depth while the panel and the window frame stay flat in both eyes. Measured between the eyes: the nearest rock 23 px apart, the far mountains 1 px, the panel 0 px.
- **Marble's globe** ([MPO](docs/screenshots/marble-globe.mpo)): the Earth in front of the screen (+11 px) and the stars behind it (-12 px), the side panel flat. This shot predates fixes made since; the menu-over-menu picture shows Marble today.
- **Stereo Desktop, a pop-up** ([MPO](docs/screenshots/stereo-desktop.mpo)), the same day. Measured between the eyes: the panel 0 px (at the screen), the sound pop-up +4 px (in front), the three windows behind -3, -7 and -10 px, and the system monitor widget -10 px, at the back with the wallpaper.

<a id="depth-on-the-desktop"></a>
## The Stereo Desktop: new frontiers for theme design

**For the first time, a theme decides what pops and what dives, not only how things look.**
For decades, shadows, bevels and raised buttons have only pretended; on the Stereo Desktop it is real, and gentle: a few pixels, within limits you choose (System Settings, "3D Depth").

- **What you use pops:** menus, tooltips, notifications and dialogs come out toward you, and the window you work in sits at the screen. *Built, and seen on a 3D TV on 13 October 2026 ([the picture at the top](#seen-in-3d)).*
- **The rest sinks:** the windows behind step back one after another, like papers in a pile, and the wallpaper dives deepest. *Built.*
- **Small things keep their place:** the pointer takes the level of whatever it is over, a shadow lies on what it falls on, and a pinned window, like a webcam over your slides, keeps popping over everything. *Built.*
- **Wallpapers in 3D:** a 3D photo as your background keeps its own pop and dive, far behind every window. *Built.* 3D video backgrounds come next, with Jeromy Streets' video wallpaper. *Coming.*
- **Screensavers in 3D:** the classic starfield and the stereo savers, in real 3D. *Built.*
- **Pictures and icons in 3D:** 3D photos show in 3D in Dolphin's previews and in the picture viewers. *Built.* Icons drawn as a pair, one for each eye, are part of Stereo Oxygen, the edition's own look. *Coming.*
- **Effects that really pop and dive:** a closing window can fly toward you in pieces, or dive behind the screen and bounce on a floor. *Built on our KWin branch, coming in the next package.* Window switchers that fan out in 3D, and the Desktop Cube in real 3D. *Coming.*
- **3D from the moment you switch on:** the boot splash and the login screen follow the 3D mode you saved for your main screen. *Built.*

**And it is still a normal 2D desktop.**
On an ordinary screen nothing changes: the same theme, the same layout, the same effects, drawn once.
3D appears only where a screen can show it, or through red-cyan glasses, and a theme made for 3D is also a complete 2D theme.

<a id="the-desktop-cube-what-one-format-makes-possible"></a>The details: [Depth on the desktop](docs/depth-on-the-desktop.md) and [For theme designers and customizers](docs/for-theme-designers.md); ideas, sketches and 3D mockups are welcome in the [themes issue](https://github.com/Sparky-OS/sparky-stereo-os/issues/78).

## For developers

**Make a program 3D once: hand the desktop both eyes, and it takes care of every screen.**
You can write and check the work on the screen you already have.
- [Develop 3D and XR on an ordinary monitor](docs/develop-3d-on-an-ordinary-monitor.md): start here.
- [Your 3D scene in stereo, from a web page](docs/web-3d-in-stereo.md): three.js, WebGL and WebXR, from red and cyan glasses in any browser to every 3D screen.
- [House formats](docs/house-formats.md) and [Stereo labor division](docs/stereo-labor-division.md): the rules, tied to the specifications.
- [Test stereo without a 3D TV](docs/test-stereo-without-a-3d-tv.md) and [A virtual machine with a 3D display](docs/stereo-vm.md): test 3D output on a virtual display or in a virtual machine; a ready root file system with Stereo KWin is on [our repository server](https://repo.sparkyos.org/bench/kwin-root/).
- [Skills](skills/README.md): instructions for people and AI assistants working on the edition.

## How it works

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**Programs describe each picture; the desktop adapts it for each screen.** For stereo, both views travel together in one full side-by-side buffer. The proposed HDR extension preserves the picture's colour description and reconstruction information through that same division of work.

**The stereo contract in three lines.**
- **Stereo KWin** (KDE Plasma's compositor, with our stereo changes) speaks full side by side, at any resolution.
- **Programs** decode or generate stereo in any standard, and deliver full side by side, at any resolution, to Stereo KWin.
- **Outputs** (Stereo KWin's filters at the end, one per kind of screen) convert from that to whatever each screen needs.

Why full side by side, one desktop on two 3D TVs from two GPUs, and how the same principle extends to HDR: [How it works](docs/how-it-works.md). The [HDR declaration](docs/stereo-hdr-content.md) is a design awaiting implementation and cross-format device tests; the HDR interchange representation remains an engineering choice to validate. Existing stereo and deep-colour tests do not validate that HDR path.

## Stereo in the open stack, not in one product

Elsewhere, stereo is tied to one product: one headset, one vendor's injector, one vendor's kernel.
Here it is a property of the open layers (KDE, the kernel, the file formats), so it reaches the screen you already own: [Stereo in the open stack](docs/open-stack.md).

## Programs the edition changes for stereo 3D and deep colour

What 3D brings to each program, from films and photos to globes and molecules: [Programs](docs/programs.md).
How each one was changed and proven, by area (the display path, video, science and engineering, images, simulators, the system, and what is not done yet): [Programs in detail](docs/programs-in-detail.md).

## Our branches on KDE's GitLab

Every KDE change is a branch of our fork on [invent.kde.org](https://invent.kde.org/danielcamposramos), tested by KDE's own CI before it is proposed upstream: [the branches and their CI results](docs/kde-branches.md).

## Merged outside Sparky Stereo

**20 October 2026: IANA registered three Matroska depth-plane types**, referencing our stereo-layer specification. Separate depth tracks now have assigned identifiers for the left-eye, right-eye and background planes. The six proposed packed-frame modes remain under expert review. [Registry milestone and upstream merges](docs/upstream-merges.md#registered-identifiers).

Where a program breaks stereo or deep colour on the way to the screen, the fix goes to that program's own project.
Projects such as HandBrake, mpv, Qt Multimedia and PeerTube have merged fixes from our work; every one, with the maintainer who merged it, and what is in review, is in [Merged outside Sparky Stereo](docs/upstream-merges.md).
Each piece is shown working before it is called done, with the numbers and a picture in anaglyph and MPO: [Proofs](docs/proofs/README.md).
What people who work with stereo said about it, in public and with links: [What people said](docs/what-people-said.md).

## Documents

[The VR-engine-to-3D-display formula](docs/formula.md), [the first KWin runs on real TVs](docs/first-runs/kwin-2026-10-01/README.md) and [the W3C talk slides](docs/talks/2026-10-13-w3c-me-ig.md) of 13 October 2026; every page is in [docs](docs/).

## Tools

[vkms-stereo-bench](tools/vkms-stereo-bench/README.md) checks 3D modes on a virtual display, and [hibernate-bench](tools/hibernate-bench/README.md) checks hibernation under Secure Boot, both in a virtual machine.

## The base: three open lists

The research behind this edition is public, in three curated lists anyone can copy (CC0): [awesome-stereoscopy](https://github.com/danielcamposramos/awesome-stereoscopy) for stereo 3D, [awesome-linux-hdr](https://github.com/danielcamposramos/awesome-linux-hdr) for HDR and deep colour, and [awesome-vr](https://github.com/danielcamposramos/awesome-vr) for virtual reality.

## Credit

Sparky Stereo OS, Daniel Ramos's (Capitain Jack) edition of SparkyLinux (by Paweł "pavroo" Pijanowski).

**Package maintainers**, each with full rights over their own repository in [Sparky-OS](https://github.com/Sparky-OS):

| | |
| --- | --- |
| <a href="https://github.com/effcol"><img src="https://github.com/effcol.png?size=96" width="72" alt="Eff"></a> | **Eff (effcol)**<br>Maintains [wiz3D](https://github.com/effcol/wiz3D), the universal stereoscopic 3D wrapper for DirectX, OpenGL, AMD HD3D and NVIDIA 3D Vision, based on iZ3D, for every system, and its package here, [Sparky-OS/wiz3D](https://github.com/Sparky-OS/wiz3D).<br>[![Follow Eff](https://img.shields.io/badge/Follow-effcol-2777AD?style=flat-square&logo=github)](https://github.com/effcol) |
| <a href="https://github.com/halverneus"><img src="https://github.com/halverneus.png?size=96" width="72" alt="Jeromy Streets"></a> | **Jeromy Streets (halverneus)**<br>Created and maintains [org.kde.video](https://github.com/Sparky-OS/org.kde.video), the video wallpaper and lock screen for KDE Plasma.<br>[![Follow Jeromy](https://img.shields.io/badge/Follow-halverneus-2777AD?style=flat-square&logo=github)](https://github.com/halverneus) |

**Version:** Sparky Stereo OS 9 "Mashtabba", based on Debian 14 "Forky", KDE Plasma only.

Everyone this edition stands on, by name: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**Special thanks:**
- **David Fattal**, co-founder of Leia and maintainer of DisplayXR, for his encouragement, his time and his effort, and for testing our desktop on the 3D displays he builds.
- **Milton Ponson** and **Christoph Dorn**, Daniel's arms in the W3C PM-KR group, every member of that group, and **Dave Raggett**, **Ian Jacobs** and **Chris Needham** of the W3C, who opened its doors to this work.
- **Tim Berners-Lee** and everyone who built the Internet, layer by layer, and gave it away.
- The **Foottroller** team, for opening the door to walking in VR with your feet on Linux.
- **Eric Allard**, the engineer who brought Johnny 5 to life in *Short Circuit*; the film's writers, **S. S. Wilson** and **Brent Maddock**; and its music, by **El DeBarge**, **Peter Wolf**, **Ina Wolf** and **David Shire**, played many times while this edition was built.

**Cite it:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**Star it:** [![GitHub stars](https://img.shields.io/github/stars/Sparky-OS/sparky-stereo-os?style=flat-square&logo=github&label=Stars)](https://github.com/Sparky-OS/sparky-stereo-os/stargazers) ⭐ If Sparky Stereo OS is useful to you, a star helps other people find it.

**Support it:** [![Sponsor Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Donate to SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Sponsoring Daniel funds this edition, and a donation to SparkyLinux supports Paweł's distribution, the base it is built on.

<a href="https://sourceforge.net/p/sparkyos/"><picture><source media="(prefers-color-scheme: dark)" srcset="https://sourceforge.net/sflogo.php?type=18&amp;group_id=3189517"><img alt="SparkyOS on SourceForge" src="https://sourceforge.net/sflogo.php?type=17&amp;group_id=3189517" width="200"></picture></a>

## Licence

The documents are licensed under the [Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): share and adapt them, giving credit to Sparky Stereo OS.

> "Information is power. But like all power, there are those who want to keep it for themselves."
> — Aaron Swartz, [*Guerilla Open Access Manifesto*](https://archive.org/details/GuerillaOpenAccessManifesto) (July 2008)

The scripts under `docs/first-runs/` and the tools under `tools/` are code and are licensed under the GNU General Public License, version 2 or later (GPL-2.0-or-later); see [LICENSE-GPL-2.0](LICENSE-GPL-2.0).
