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

**A window's 2D part and its 3D area are separate surfaces.**
The 2D part (menus, toolbars, panels, the document around a picture) is the window's own surface, at its normal size, one eye's size, and declares nothing.
The 3D area (a stereo video, a 3D viewport, a stereo painting canvas) is a surface of its own that hands Stereo KWin full side by side.
Stereo KWin shows the 2D part identical in both eyes and gives the 3D area each eye's view, in place inside the window.
Only a program that is stereo and full screen only, whose whole window is the 3D area, makes its whole window stereo.
The separation is also what gives the 2D part its depth: its elements declare their planes (sunk, screen, popped), and Stereo KWin draws those for each screen, while the 3D areas carry their own eyes.

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

## Depth on the desktop

**Three places, declared: sunk, screen and popped.** All subtle, a few pixels, with the limits your own settings (System Settings, "3D Depth"). The active window sits at the screen; its menus, tooltips and notifications pop; the wallpaper and the windows behind sink.

**Everything in between is Stereo KWin's job, by stacking order.** Stacked background windows fan out from sunk towards popped, always behind the active window, in the same order as in 2D. A window caught in the middle of a pile, its edges out of the stack, reads as a sheet floating within it, the way a pile of papers looks in real life. No program declares this; it falls out of the order.

**In the background, each window is 2D.** A window in the pile is a flat sheet at its place in the stack: the desktop's pop effects inside it come to one plane. Its stereo content stays 3D: a movie or a game is full side by side wherever its window is, so a 3D movie plays on one screen while you work on another.

**Pop is real, not faked: a little scale and a little depth, together.** One value per element gives both cues: bigger and nearer when popped, smaller and further when sunk.
- **Everything follows its element's plane:** its text scales and moves with it, and so does its click area, so a popped element has no dead margin and a sunk one no click area beyond its picture. The plane's geometry lives inside the window itself, the one geometry that drawing and input both read.
- **Text shares its element's depth.** What tires the eyes is 2D text lying over a picture at another depth, not depth as such.
- **On a 2D screen, the pop is the same scale plus a move up and to the left,** so depth reads on every screen, with or without glasses.

## The Desktop Cube: what one format makes possible

Plasma's Desktop Cube, rebuilt on the standard, shows what follows from one format without inventing anything new.
- **It is a 3D application, treated like a game:** its scene has its own depth and hands Stereo KWin full side by side, two views of one scene, one camera per eye.
- **Its faces are your real desktops, each a stereo surface.** The windows on a face sit on the desktop's three planes (sunk, screen and popped, with the pop your own setting), so each face is a relief, and the cube's cameras see the windows standing off its faces from any angle.
- **When it closes on one desktop, it is the desktop:** the front face lands on the screen plane, identical to the flat desktop.
- **It is the seed of the VR home:** the same scene, seen through a headset's cameras, is a floating 3D desktop.

**On a 2D screen, too.** A straight 2D screen shows only the left eye, as always, and never renders the second one. But during the cube's animation that one view is still the real 3D scene: live desktops on a turning cube, windows in relief, depth shown by perspective and motion alone. Desktop interfaces have seen little new in years; the cube that is real depth on a 3D screen is something new on a 2D one, before anyone puts on glasses.

## Stereo in the open stack, not in one product

**Elsewhere, stereo is tied to a product.**
Steam runs on ARM only on Valve's own headset; on every other ARM device, Steam for Linux stays unsupported ([Valve, 4 October 2026](https://github.com/ValveSoftware/steam-for-linux/issues/13689)).
New glasses-free monitors deliver their 3D through Windows injectors ([ViewX, August 2026](https://www.prnewswire.com/news-releases/viewx-launches-liber-and-immer-glasses-free-ai-3d-displays-on-kickstarter-302857181.html)).
Cheap ARM boxes switch a television into HDMI 3D only on their vendors' kernels.
Each works inside its own walls, and stops at them.

**Here, stereo is a property of the open layers, so it reaches the screen you already own.**
- **KDE carries it.** KWin is the same compositor on the desktop, on ARM boards, on phones with Plasma Mobile and on televisions with Plasma Bigscreen, so one contract covers all of them. China's own desktops have built on KWin too ([UKUI's ukui-kwin](https://github.com/ukui/ukui-kwin), [Deepin's deepin-kwin](https://github.com/linuxdeepin/deepin-kwin)). A new kind of display, glasses-free included, is one more output filter in Stereo KWin, not one more injector per game.
- **The cheapest hardware already does it.** An Allwinner H616 box and a Rockchip RK3228A box switch a 3D television into HDMI 3D on their Android vendor kernels today, and the Raspberry Pi's mainline driver already allows HDMI stereo modes. Without Steam on ARM, the stereo there comes from the operating system: video, photos, the desktop and native programs.
- **One kernel fix reaches a whole ecosystem.** In mainline Linux, HDMI stereo modes are allowed by Intel's i915, nouveau and the Raspberry Pi's vc4. The shared HDMI bridge connector that many SoC display drivers build on, Rockchip's and Allwinner's among them, still reads "[TODO: Handle doublescan_allowed and stereo_allowed](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/display/drm_bridge_connector.c)", and none of the display drivers of China's chipmakers allows stereo modes. Fixing it once, in the DRM core, opens HDMI 3D on every board built on it.
- **Old hardware comes back.** The Radeon HD 7000 and R9 200 cards, sold alongside the 3D televisions of 2010 to 2013, now run amdgpu's modern display code by default ([Timur Kristóf, XDC 2026](https://indico.freedesktop.org/event/12/contributions/545/)), so HDMI work done there reaches them: an old PC and an old 3D television become a working stereo system again.

KDE carries it, cheap boxes prove it costs little, one kernel fix makes it universal, and old hardware makes it repairable.

## Merged outside Sparky Stereo

**Sparky Stereo is also a campaign.**
Where a program breaks stereo or deep colour on the way to the screen, the fix goes to that program's own project, in its own style.
Each merge below was reviewed and accepted by that project's maintainers.
Each one shows the next project the same problem already fixed elsewhere, and Sparky Stereo is the desktop where all of them meet.

**Merged:**
- **HandBrake** ([#8100](https://github.com/HandBrake/HandBrake/pull/8100), 16 September 2026): the x264 encoder writes the H.264 frame packing arrangement SEI (ITU-T H.264, Annex D), so an encoded side by side or top and bottom video declares itself.
- **Universal Media Server** ([#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330), merged 19 September, released in [15.9.0](https://github.com/UniversalMediaServer/UniversalMediaServer/releases/tag/15.9.0) on 5 October 2026): 3D video keeps its declaration through H.264 transcoding, so televisions and players switch to 3D on their own; the Sony Bravia profiles of 2011 and 2012 are corrected too.
- **MKVToolNix** ([ebd8445b](https://codeberg.org/mbunkus/mkvtoolnix/commit/ebd8445b1185d35d6bdbb9c1463757fbc9aa7c29), from [!6311](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6311), merged 21 September 2026): mkvmerge sets the Matroska StereoMode ([RFC 9559](https://www.rfc-editor.org/rfc/rfc9559)) from the AVC frame packing SEI.
- **mpv** ([#18490](https://github.com/mpv-player/mpv/pull/18490), 23 September 2026): the player detects the layout signalled in the stream itself, the frame packing SEI and the MP4 `st3d` box.

**In review:**
- **FFmpeg** ([#24628](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24628)): the H.264 and H.265 decoders honour the SEI's persistence, so the declaration holds for every frame, not only the first; [#24643](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24643): the stream's own declaration wins over the container's by default.
- **Media3, Android's media framework** ([androidx/media#3439](https://github.com/androidx/media/pull/3439)): the frame packing SEI read in MP4 and fragmented MP4, the right-eye-first modes, StereoMode in the WebM muxer.
- **x265** ([#986](https://github.com/Multicorewareinc/x265/pull/986)): a `--frame-packing` option that writes the H.265 frame packing arrangement SEI.
- **MKVToolNix** ([!6312](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6312)): the same StereoMode from the HEVC frame packing SEI.
- **VLC** ([!10366](https://code.videolan.org/videolan/vlc/-/merge_requests/10366)): the x264 module signals the input's stereo layout by default.
- **gamescope** ([#2438](https://github.com/ValveSoftware/gamescope/pull/2438)): the present mode of the nested output can be chosen, which ends a frame race seen when stereo games run through it.
- **NVIDIA's open kernel modules** ([#1386](https://github.com/NVIDIA/open-gpu-kernel-modules/pull/1386)): HDMI deep colour at the depth the display declares in its EDID (DC_30, DC_36, DC_48).
- **wiz3D** ([#33](https://github.com/effcol/wiz3D/pull/33)): a Linux build of its DirectX 9 stereo path.

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
