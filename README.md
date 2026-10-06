# Sparky Stereo OS

Sparky Stereo OS 9 "Mashtabba", based on Debian 14 "Forky": the stereo 3D edition of SparkyLinux, KDE Plasma only.
It is in development.

## Why one format: full side by side, at any resolution

Every program that shows stereo hands the desktop one thing: both eyes at full size, left eye first, side by side, at any resolution, declared once.
The desktop turns that into whatever the screen needs: a 3D television's own HDMI 3D modes, anaglyph on any monitor, interleaved and frame-sequential displays, a headset.

**Why only one format.**
With several formats, the work is every input format times every output format times every program that wants stereo.
The formats and the displays are short lists; the programs are an open list, and that is the term that never ends.
Every earlier attempt put the format question on each program: quad-buffer needed a workstation card, 3D Vision needed one vendor's driver, and every player grew its own menu of packings.
Each program had to know the display, and almost none did.
Here a program learns stereo once: it renders two eyes, declares them, and never needs to know what a television or a headset is.

**Why full side by side.**
- **Programs already produce it.** Games and VR engines render two viewports side by side, most 3D files carry side by side, and our Mesa packs quad-buffer into it at swap.
- **It loses nothing.** Each eye keeps its full resolution; half formats exist only at the edges, where a display asks for them.
- **It survives the path.** One ordinary buffer passes through X11, Xwayland, screenshots, screencasts and remote desktop unchanged.
- **The eyes stay in sync.** Both eyes travel in one buffer, committed once, so they always show the same instant; that is what lets every output be built from the same frame.

The converting costs copying rows and columns, work a desktop does every frame anyway; every test runs in software rendering as well as on a GPU.
The design in one page: [STEREO3D.md](https://invent.kde.org/danielcamposramos/kwin/-/blob/stereo3d/STEREO3D.md).

## Documents

- [Stereo labor division](docs/stereo-labor-division.md): who does what to show a stereo picture, from the program to the screen, and what each part never has to care about, tied to the specifications.
  For application, engine and toolkit developers, driver developers, display and hardware people.
- [The VR-engine-to-3D-display formula](docs/formula.md): what a VR engine changes to drive a 3D display instead of a headset, worked out on Half-Life 2.
  For engine and game developers, and anyone porting a VR title to stereo displays.
- [KWin stereo first runs, 2026-10-01](docs/first-runs/kwin-2026-10-01/README.md): the first stereo 3D outputs from KWin on real displays, with photos, logs and the scripts used.
  For KWin and driver developers, and anyone who wants to see what the first runs showed.

## Credit

Sparky Stereo OS, an edition of SparkyLinux, created by Paweł "pavroo" Pijanowski and Daniel Ramos (Capitain Jack).

## Licence

The documents are licensed under the [Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): share and adapt them, giving credit to Sparky Stereo OS.

The scripts under `docs/first-runs/` are code and are licensed under the GNU General Public License, version 2 or later (GPL-2.0-or-later); see [LICENSE-GPL-2.0](LICENSE-GPL-2.0).
