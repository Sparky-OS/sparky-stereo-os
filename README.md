# Sparky Stereo OS

🇨🇦 [English](README.md) · 🇧🇷 [Português](README.pt-BR.md) · 🇵🇱 [Polski](README.pl.md) · 🇫🇷 [Français](README.fr.md) · 🇩🇪 [Deutsch](README.de.md) · 🇲🇽 [Español](README.es.md) · 🇯🇵 [日本語](README.ja.md) · 🇰🇷 [한국어](README.ko.md) · 🇨🇳 [简体中文](README.zh-CN.md) · 🇭🇰 [繁體中文](README.zh-TW.md)

**Create and explore in 3D on the screen you already have: paint, edit photos and video, study molecules and globes, then watch films and play games.**
It is made for every kind of 3D screen: 3D TVs and projectors, VR headsets, glasses-free 3D displays, and any monitor with red-cyan glasses.
On a plain 2D monitor the same desktop works without any change.
Sparky Stereo OS, Daniel Ramos's edition of SparkyLinux (by Paweł "pavroo" Pijanowski), is a Linux system with a new Stereo KDE Plasma desktop.

**Lighter on your machine and on the planet:** every package ships without the comments and notes that programs never read, so the same work takes less processing, less energy and less wear.
[Measured](docs/lean-code-packages.md#why-it-matters) on a 2016 laptop: preparing a program for the compiler takes 2 to 4% less work than with the same files unstripped, and nothing is lost.

<a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/translucent-stereo-desktop-anaglyph.jpg" width="99%" alt="The Stereo Desktop in 3D with translucent windows: Dolphin's Settings menu and its colour-scheme list in front, the glass windows behind stepping back, the system monitor and the wallpaper deepest (red-cyan anaglyph)"></a>

<a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/doom-2016-in-a-window-anaglyph.jpg" width="32%" alt="DOOM (2016) in a window, in 3D, with the flat Plasma panel below it (red-cyan anaglyph)"></a> <a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/marble-globe-anaglyph.jpg" width="32%" alt="Marble's globe in front of the stars, in 3D (red-cyan anaglyph)"></a> <a href="docs/edition-in-detail.md#seen-in-3d"><img src="docs/screenshots/stereo-desktop-anaglyph.jpg" width="32%" alt="The Stereo Desktop in 3D: the panel at the screen, a sound pop-up in front of it, and the windows behind stepping back (red-cyan anaglyph)"></a>

*Red-cyan glasses show these in 3D ([more](docs/edition-in-detail.md#seen-in-3d)).*

**Status: beta 1, for testers.** Tested on 3D TVs, on ordinary monitors with red-cyan glasses and on an Android phone in an inexpensive viewer; glasses-free displays and standalone headsets are in progress.

**Next step: try it on your Windows PC from a USB stick, without installing anything:** [one page, ten steps](docs/guides/try-on-windows.en.md).
<br>Ask for the download and tell us about your 3D gear, in your language: [🇨🇦](https://github.com/Sparky-OS/sparky-stereo-os/issues/26) [🇧🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/25) [🇵🇱](https://github.com/Sparky-OS/sparky-stereo-os/issues/27) [🇫🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/80) [🇩🇪](https://github.com/Sparky-OS/sparky-stereo-os/issues/153) [🇲🇽](ISSUE-ES) [🇯🇵](https://github.com/Sparky-OS/sparky-stereo-os/issues/81) [🇰🇷](https://github.com/Sparky-OS/sparky-stereo-os/issues/83) [🇨🇳](https://github.com/Sparky-OS/sparky-stereo-os/issues/84) [🇭🇰](https://github.com/Sparky-OS/sparky-stereo-os/issues/85)

- <a id="science-and-engineering"></a>**[Science and engineering](docs/edition-in-detail.md#science-and-engineering):** Marble's globe, KAlgebra's plots and Kalzium's molecules in 3D; 3D models and circuit boards are in progress. Scanning is planned: a video of a part, a site or a specimen becomes a 3D model.
- <a id="create"></a>**[Create](docs/edition-in-detail.md#create):** paint in 3D and in deep colour (16 bits per colour instead of 8), and edit 3D photos and video. Scanning is planned: a video of an object or a place becomes a 3D model you can walk around.
- <a id="watch-and-play"></a>**[Watch and play](docs/edition-in-detail.md#watch-and-play):** 3D films, photos and games, in a window or full screen.
- <a id="vr-is-also-a-stereo-monitor"></a>**[VR is also a stereo monitor](docs/edition-in-detail.md#vr-is-also-a-stereo-monitor):** a headset, or a phone in a viewer, is a 3D screen for this desktop too.
- <a id="for-developers"></a>**[Develop](docs/edition-in-detail.md#for-developers):** make your program 3D once; the desktop adapts it to each screen.
- **[Another distribution?](docs/other-distributions.md)** Why we do not package for it, and how its maintainers can adopt our fixes.

<a id="depth-on-the-desktop"></a>
## The Stereo Desktop: new frontiers for theme design

**On this desktop, a theme decides what pops and what dives:** [new frontiers for theme design](docs/edition-in-detail.md#depth-on-the-desktop).

## How it works

<a id="why-one-format-full-side-by-side-at-any-resolution"></a>**Programs describe each picture; the desktop adapts it for each screen.** For stereo, both views travel together in one full side-by-side buffer. The proposed HDR extension preserves the picture's colour description and reconstruction information through that same division of work.
[In detail](docs/edition-in-detail.md#how-it-works)

## More about the edition

- <a id="who-builds-it"></a>[Who builds it](docs/edition-in-detail.md#who-builds-it)
- <a id="where-it-is-going"></a>[Where it is going](docs/edition-in-detail.md#where-it-is-going)
- <a id="seen-in-3d"></a>[Seen in 3D](docs/edition-in-detail.md#seen-in-3d)
- <a id="for-theme-designers-and-customizers"></a>[For theme designers and customizers](docs/edition-in-detail.md#for-theme-designers-and-customizers)
- <a id="stereo-in-the-open-stack-not-in-one-product"></a>[Stereo in the open stack, not in one product](docs/edition-in-detail.md#stereo-in-the-open-stack-not-in-one-product)
- <a id="programs-the-edition-changes-for-stereo-3d-and-deep-colour"></a>[Programs the edition changes for stereo 3D and deep colour](docs/edition-in-detail.md#programs-the-edition-changes-for-stereo-3d-and-deep-colour)
- <a id="our-branches-on-kdes-gitlab"></a>[Our branches on KDE's GitLab](docs/edition-in-detail.md#our-branches-on-kdes-gitlab)
- <a id="merged-outside-sparky-stereo"></a>[Merged outside Sparky Stereo](docs/edition-in-detail.md#merged-outside-sparky-stereo)
- <a id="documents"></a>[Documents](docs/edition-in-detail.md#documents)
- <a id="tools"></a>[Tools](docs/edition-in-detail.md#tools)
- <a id="the-base-three-open-lists"></a>[The base: three open lists](docs/edition-in-detail.md#the-base-three-open-lists)

## Credit

Sparky Stereo OS, Daniel Ramos's (Capitain Jack) edition of SparkyLinux (by Paweł "pavroo" Pijanowski).
Everyone this edition stands on, by name: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

**Cite it:** [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23309024.svg)](https://doi.org/10.5281/zenodo.23309024)

**Support it:** [![Sponsor Daniel](https://img.shields.io/badge/Sponsor-danielcamposramos-EA4AAA?style=flat-square&logo=githubsponsors)](https://github.com/sponsors/danielcamposramos) [![Donate to SparkyLinux](https://img.shields.io/badge/Donate-SparkyLinux-2777AD?style=flat-square)](https://sparkylinux.org/donate/) Sponsoring Daniel funds this edition, and a donation to SparkyLinux supports Paweł's distribution, the base it is built on.

[In detail](docs/edition-in-detail.md#credit)

## Licence

The documents are licensed under the [Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): share and adapt them, giving credit to Sparky Stereo OS.
[In detail](docs/edition-in-detail.md#licence)
