# Sparky Stereo OS

Sparky Stereo OS 9 "Mashtabba", based on Debian 14 "Forky": the stereo 3D edition of SparkyLinux, KDE Plasma only.
It is in development.

## Why one format: full side by side, at any resolution

**The standard in three lines.**
- **Stereo KWin** (KDE Plasma's compositor, with our stereo changes) speaks full side by side, at any resolution.
- **Programs** decode or generate stereo in any standard, and deliver full side by side, at any resolution, to Stereo KWin.
- **Outputs** (Stereo KWin's filters at the end, one per kind of screen) convert from that to whatever each screen needs.

That is what makes stereo work across GPUs, across monitors (2D ones included) and across every 3D output format.

**Two places, two rules.**
Inside a program, anything goes: a player reads every packing a file can carry, an engine renders its eyes however it likes.
Inside Stereo KWin, only full side by side exists: both eyes at full size, left eye first, at any resolution, declared once.
The output filters then turn that into whatever the screen needs: a 3D television's own HDMI 3D modes, anaglyph on any monitor, interleaved and frame-sequential displays, a headset.

**It is how sound already works on Linux.**
A program hands PipeWire plain PCM, at whatever rate it likes.
PipeWire resamples, mixes and sends it to HDMI, Bluetooth or a USB DAC, and the program never learns which.
Nobody calls that a limitation: it is why every Linux program plays sound on every device.
Full side by side is the stereo picture's PCM, and Stereo KWin is its PipeWire.
A new kind of 3D screen needs one new output filter, and every stereo program already written works on it the day the filter lands.

**Why only one format.**
With several formats, the work is every input format times every output format times every program that wants stereo.
The formats and the displays are short lists; the programs are an open list, and that is the term that never ends.
Every earlier attempt put the format question on each program: quad-buffer needed a workstation card, NVIDIA's 3D Vision needed one vendor's driver, and every player grew its own menu of packings.
Each program had to know the display, and almost none did.
Here a program learns stereo once: it renders two eyes, declares them to Stereo KWin, and never needs to know what a television or a headset is.

**Why full side by side.**
- **Programs already produce it.** Games and VR engines render two viewports side by side, most 3D files carry side by side, and our Mesa packs quad-buffer OpenGL and two-layer Vulkan into it at swap.
- **It loses nothing.** Each eye keeps its full resolution; half formats exist only in the output filters, where a display asks for them.
- **It survives the path.** One ordinary buffer passes through X11, Xwayland, screenshots, screencasts and remote desktop unchanged.
- **The eyes stay in sync.** Both eyes travel in one buffer, committed once, so they always show the same instant; that is what lets every output, frame sequential included, be built from the same frame.

The converting costs copying rows and columns, work Stereo KWin does every frame anyway; every test runs in software rendering (llvmpipe) as well as on a GPU.
The design in one page: [STEREO3D.md](https://invent.kde.org/danielcamposramos/kwin/-/blob/stereo3d/STEREO3D.md).

## The Desktop Cube: what one format makes possible

Plasma's Desktop Cube, rebuilt on the standard, shows what follows from one format without inventing anything new.
- **It is a 3D application, treated like a game:** its scene has its own depth and hands Stereo KWin full side by side, two views of one scene, one camera per eye.
- **Its faces are your real desktops, each a stereo surface.** The windows on a face sit on the desktop's three planes (sunk, screen and popped, with the pop your own setting), so each face is a relief, and the cube's cameras see the windows standing off its faces from any angle.
- **When it closes on one desktop, it is the desktop:** the front face lands on the screen plane, identical to the flat desktop.
- **It is the seed of the VR home:** the same scene, seen through a headset's cameras, is a floating 3D desktop.

**On a 2D screen, too.** A straight 2D screen shows only the left eye, as always, and never renders the second one. But during the cube's animation that one view is still the real 3D scene: live desktops on a turning cube, windows in relief, depth shown by perspective and motion alone. Desktop interfaces have seen little new in years; the cube that is real depth on a 3D screen is something new on a 2D one, before anyone puts on glasses.

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
