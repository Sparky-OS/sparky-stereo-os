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
- **Qt Multimedia** ([778399](https://codereview.qt-project.org/c/qt/qtmultimedia/+/778399), merged 8 October 2026): the FFmpeg backend reports the mastering display's peak luminance in nits, as `QVideoFrameFormat::maxLuminance()` promises; it reported 10,000 times the value, so HDR video (PQ and HLG) was tone mapped against a peak 10,000 times too high. Tim Blechmann, the Qt Multimedia maintainer, improved its test and approved it.

**In review:**
- **FFmpeg** ([#24628](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24628)): the H.264 and H.265 decoders honour the SEI's persistence, so the declaration holds for every frame, not only the first; [#24643](https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/24643): the stream's own declaration wins over the container's by default.
- **Media3, Android's media framework** ([androidx/media#3439](https://github.com/androidx/media/pull/3439)): the frame packing SEI read in MP4 and fragmented MP4, the right-eye-first modes, StereoMode in the WebM muxer.
- **x265** ([#986](https://github.com/Multicorewareinc/x265/pull/986)): a `--frame-packing` option that writes the H.265 frame packing arrangement SEI.
- **MKVToolNix** ([!6312](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6312)): the same StereoMode from the HEVC frame packing SEI.
- **VLC** ([!10366](https://code.videolan.org/videolan/vlc/-/merge_requests/10366)): the x264 module signals the input's stereo layout by default.
- **gamescope** ([#2438](https://github.com/ValveSoftware/gamescope/pull/2438)): the present mode of the nested output can be chosen, which ends a frame race seen when stereo games run through it.
- **NVIDIA's open kernel modules** ([#1386](https://github.com/NVIDIA/open-gpu-kernel-modules/pull/1386)): HDMI deep colour at the depth the display declares in its EDID (DC_30, DC_36, DC_48).
- **PeerTube** ([#7816](https://github.com/Chocobozzz/PeerTube/pull/7816)): a video that declares its 3D packing in its container keeps it through transcoding, right eye first included.
- **wiz3D** ([#33](https://github.com/effcol/wiz3D/pull/33)): a Linux build of its DirectX 9 stereo path.

## Programs the edition changes for stereo 3D and deep colour

**One contract for every program below: programs hand the desktop full side by side, and KWin's outputs decide the screen.**
Each item names the program, links its own upstream project, says what it gains in the edition and what we found on the way.
**In the edition** means a package of it is in the Sparky Stereo repository today.
**In progress** means the work is done and measured, but no package is in the repository yet. **Planned** means not built yet.
What was proven is said per item, and it was proven on our headless KWin with captures of both eyes unless the item says otherwise; where a real display was used, it says so.

**The display path**
- [**Linux kernel**](https://www.kernel.org/): amdgpu lists and signals the HDMI 3D modes a display's EDID declares and times frame packing, full side by side is handled in the DRM core, i915, nouveau and amdgpu, and nouveau gains 16 bits per colour on Turing and newer. Stock amdgpu refuses the 3D modes, and nouveau's missing piece was deep colour; a Sony 3D television switched itself into 3D from System Settings on 2026-10-01. [in the edition]
- [**Mesa**](https://www.mesa3d.org/): OpenGL quad buffer, EGL multiview windows and two-layer Vulkan swapchains become one full side by side picture and are declared to KWin, and a Vulkan layer does the same over drivers outside Mesa. Mesa has to declare stereo before it doubles the window, or KWin treats the resize as a 2D window's; GLX offers stereo only when KWin announces it. [in the edition]
- [**NVIDIA open GPU kernel modules**](https://github.com/NVIDIA/open-gpu-kernel-modules): the 3D modes are built from the display's HDMI stereo block, and HDMI deep colour follows the depth the display declares, up to 16 bits. On an RTX 3060 driving a 3D television, KWin listed the television's 3D modes through NVIDIA's driver and the link ran at 12 bits, the display's own maximum; 16 bits is untested on hardware because no 48-bit display is at hand. [in the edition]
- [**egl-wayland**](https://github.com/NVIDIA/egl-wayland): the EGL external platform for NVIDIA on Wayland learns the two-view window (`EGL_EXT_multiview_window`) as Mesa's EGL has it. It builds and passes a protocol contract test; a real run on NVIDIA's driver is still to do. [in the edition]
- [**Xwayland**](https://www.x.org/releases/individual/xserver/): four patches give a redirected X11 child window a surface of its own, post its damage and keep alpha on 32-bit root surfaces, so a 3D area inside a toolkit window can be its own stereo layer. The gap they answer was measured: gmsh, ParaView, Sweet Home 3D, CloudCompare, GRASS and KiCad declared stereo on a child window, KWin read only top-level windows, and both eyes showed squeezed inside the 2D window; the proofs of those programs on the patched Xwayland are still open. [in the edition]
- [**KWin**](https://invent.kde.org/plasma/kwin): per-eye scene passes, stereo windows and subsurfaces, 3D modes and virtual 3D outputs, and depth on the desktop. We found that a window moved for depth lost its blur (`BlurEffect::shouldBlur` skips translated windows unless blur is forced), and that after Krita's splash screen KWin sends no new synthetic configure with the one-eye size, which squeezes the window. KWin now takes one stereo declaration, full side by side at any resolution, and that cleanup passes every job of KDE's CI ([pipeline](https://invent.kde.org/danielcamposramos/kwin/-/pipelines/1373213)). [in the edition]
- [**KScreen**](https://invent.kde.org/plasma/kscreen): the display's 3D modes appear with its other modes, labelled "(3D …)" with a suggestion for games and for movies, never chosen automatically. A suggestion of frame packing at 30 Hz for games was wrong and is corrected: games only from 60 Hz. [in the edition]
- [**plasma-wayland-protocols**](https://invent.kde.org/libraries/plasma-wayland-protocols): carries `kde-stereo-content-v1`, the declaration a program makes for a window or a subsurface, and the stereo output settings KScreen uses. Wayland and X11 declarations and the shared library were tested in containers (27 tests). [in the edition]

**Video**
- [**FFmpeg**](https://ffmpeg.org/): the package carries the seven patches of the review listed above, and the VVC decoder, which did not decode the frame packing message at all, now exports it. Tests (FATE) check the arrangement in output order with four threads, its cancellation and its end at a new coded video sequence. [in the edition]
- [**mpv**](https://mpv.io/): reads the layout from the stream, unpacks every packing to full side by side, draws the video in a layer below the controls and declares only the video; subtitles and the on-screen display are drawn once per view. Debian's 0.41.0 does not take the patches, so the package is upstream's 2026-09-29 snapshot; stock mpv exposed only the stereo layout of a video, not its projection, which a new track property now gives for 360 and VR180. [in the edition]
- [**MpvQt**](https://invent.kde.org/libraries/mpvqt): a video layer as a Wayland subsurface placed below the window, declared as full side by side while the video is 3D, at 10 bits, or half float for deeper video. Debian's libmpvqt3 aborts Haruna against Qt 6.11.2 (a Wayland native-interface revision mismatch), and the rebuild cures it. [in the edition]
- [**Haruna**](https://invent.kde.org/multimedia/haruna): 3D videos play in the layer with controls, subtitles and playlist identical in both eyes, 72 of 72 captures matching, installed from the packages. The unchanged Haruna squeezes both views into one picture and KWin sees a plain 2D window. [in the edition]
- [**VLC Stereo**](https://www.videolan.org/vlc/): the stereo edition of VLC 3.0 shows both views, reads the layout from the frame packing SEI (right eye first included) and from Matroska's StereoMode, and declares its window. VLC 3.0 parsed Matroska's StereoMode and ignored it, never read the SEI of an MP4 or Matroska file, because the packetizer that reads it does not run for them, and its command-line player shows no video at all on native Wayland, because KWin offers only stable xdg-shell and VLC 3.0 knows only `wl_shell`. [in the edition]
- [**Dragon Player**](https://apps.kde.org/dragonplayer/): 3D video in both eyes for every packing of H.264 Table D-8, with an input format menu and Swap Eyes for video that declares nothing, proved on builds of the same sources as the package; the menu itself was not driven in the tests. Debian describes it as a Phonon player, but it is QML on QtMultimedia, and a stock install does not start without QML modules its package does not depend on. [in the edition]
- [**Qt Multimedia**](https://doc.qt.io/qt-6/qtmultimedia-index.html): `QVideoFrameFormat::StereoMode` names every packing of H.264 Table D-8 and RFC 9559, with right eye first and the view of a frame in a sequence, filled from FFmpeg's stereo side data. Qt Multimedia had no stereo notion at all; a unit test of every mode passes (62 checks), and Qt may want another shape for the API. [in the edition]
- [**Kdenlive**](https://kdenlive.org/) and [**MLT**](https://www.mltframework.org/): a clip knows its packing, the monitors can show the left eye only or both eyes in 3D, and the render writes the frame packing SEI and the Matroska StereoMode. Kdenlive lost both when it rendered (0 SEI in the MP4 and the Matroska file), and Debian's MLT 7.40.0 consumer does not build against FFmpeg 9. [in the edition]
- [**Bino**](https://bino3d.org/): input in any standard, output always full side by side, with its output menu removed so nothing can break that, and with stereo 360 and VR180 turned by the mouse, the same direction in both eyes. Bino 2.8 reads a right-eye-first Matroska file as left first, because it compares ffprobe's JSON number with the string "1"; the fix of four lines is proved before and after. It runs on X11 through Xwayland, and on Wayland it does not run yet. [in the edition]
- [**PlasmaTube**](https://apps.kde.org/plasmatube/): packaged from KDE's 26.08.1 release, which is not in Debian, with 3D taken from the stream, then from the `yt3d` tags, then from the shape of the frame, and with 360 and VR180 as a flat view the viewer turns. 48 of 48 captures of declared clips were right in both eyes, and 24 of 24 for the panoramas; YouTube's own streams were not read, because the one public Invidious instance tried answered with its bot wall. [in the edition]
- [**Plank Player**](https://invent.kde.org/plasma/plank-player): Plasma Bigscreen's own player, driven by a remote control, packaged from KDE's sources because it is not in Debian. The video is a surface of its own declared full side by side, with the packing taken from the stream (the frame packing SEI and Matroska's StereoMode, right eye first included, also when the SEI comes only on keyframes) or from the shape of the frame; the on-screen display and menus stay identical in both eyes (0 differing pixels in 30 captures), and a 3D menu reached with the remote's keys picks the input format, Swap Eyes or one eye. The unchanged player declares nothing, so KWin sees a plain 2D window even for a marked 3D clip. [in the edition]

**Science and engineering**
- [**Marble**](https://apps.kde.org/marble/): the globe in stereo from one world and two cameras orbiting its centre, the stars at the globe's maximum parallax, and the map's controls flat in both eyes, switched on from View > Stereo 3D. Against the exact prediction the median disparity error was 0.16 px at 2 degrees and 0.29 px at 4, with no vertical difference, and with stereo off the window matches Debian's Marble to 0 differing pixels. The perspective view is in progress. [in the edition]
- [**KAlgebra**](https://apps.kde.org/kalgebra/) and [**Analitza**](https://invent.kde.org/education/analitza): the 3D plot is drawn once per eye by Qt's left and right buffers from one scene with two parallel cameras. The measured disparity of the axes followed the predicted one with a median error of 0.26 to 0.33 px at 2, 5 and 10 percent separation, with 0 differing pixels outside the plot. [in the edition]
- [**Kalzium**](https://apps.kde.org/kalzium/) and [**Avogadro**](https://avogadro.cc/): the molecule is drawn in stereo with the same two cameras (9 atoms, median error 0.06 px). On the way we found why Kalzium drew no molecule with Avogadro 2 ([KDE bug 463018](https://bugs.kde.org/show_bug.cgi?id=463018), open since 2022): Kalzium never registered the molecule with Avogadro's layer manager, and a three-file fix is ready for Kalzium on its own. [in the edition]
- [**Kubrick**](https://apps.kde.org/kubrick/): the cube is drawn once per eye, the background and labels stay flat, and picking uses the left eye. Measured against ray-cast predictions, the median error was 0.13 to 0.24 px on the software and the GPU client. [in the edition]
- [**Netgen**](https://ngsolve.org/): the `-stereo` option existed and did nothing; it now asks for a quad-buffer window and draws the mesh once per eye (near brick -5.01 px, centre 0, far +3.46 px, vertical 0). Debian's `netgen` also does not start with only that package installed, because the GUI loads `libnggui.so`, which only the development package ships. [in the edition]
- [**GNU Octave**](https://octave.org/): a figure takes `stereo` and `stereoeyeseparation` properties. Octave always projects orthographically, so each eye is a shear around the camera target (near -9.5 px, target 0, far +9.5 px), and the legend and 2D axes stay identical in both eyes. [in the edition]
- [**GRASS GIS**](https://grass.osgeo.org/): the 3D view (NVIZ) draws from two parallel cameras with an off-axis frustum and a setting for the eye separation. In the 8.5.0 build `glDrawBuffer` was compiled out, so everything drew to both eyes; the draw calls now go to the eye's own buffer. [in progress]
- [**KiCad**](https://www.kicad.org/): the 3D viewer renders each eye from its camera class, perspective and orthographic, with a setting in Preferences. The navigator gizmo differed between the eyes (18 and 332 pixels) because its headlight was placed with the eye's matrix; the cause is fixed and the difference is 0 of 7560 pixels. On the newer Mesa tried, the canvas was not declared as stereo although both eyes were packed, and that is not resolved. [in progress]
- [**OpenSCAD**](https://openscad.org/): the preview is drawn once per eye by Qt's stereo buffers with a setting for the separation, perspective and orthographic. Vertical disparity was 0 and the editor and console part had 0 differing pixels between the eyes. [in progress]
- [**F3D**](https://f3d.app/): a `--stereo` option and an eye angle, using VTK's own shear of the projection. F3D draws through render passes that never set the camera's stereo flag, so VTK's own stereo shear was not applied and the two eyes were pixel-identical even at a large eye angle; the change sets the same shear itself. [in progress]

**Images**
- [**Krita**](https://krita.org/en/): a 16-bit canvas on Wayland and a stereo 3D canvas. Krita forced X11, where under Xwayland it got only 8 bits, and offered only 8 and 10; with the change a ramp that holds 1 level at 8 bits holds 249 at 16. On Wayland the stereo canvas is now a surface of its own below the window, at 16 bits in each eye (249 levels, as in 2D) and with the canvas's colour description, and documents that are not stereo keep their 16 bits in the same session; outside the canvas the eyes differ by 0 pixels. The window around the canvas, which holds the 2D interface, is 8 bits until Qt keeps the depth a translucent window asks for (in progress). [in the edition]
- [**Spectacle**](https://apps.kde.org/spectacle/): a capture is side by side when a window or an output in it is 3D, and is saved as JPS for the JPG choice and as MPO for the PNG choice. Tested in containers (12 tests); the run on the desktop is still to do. [in the edition]
- [**KImageFormats**](https://invent.kde.org/frameworks/kimageformats): a plugin for JPS and MPO with the MIME types registered, read back by Pillow and exiftool, and every reader now reports a picture's stereo layout, as the edition's Qt does for PNG's registered `sTER` chunk. 650 JPS photographs from a 3D phone and 2,367 ordinary JPEGs decode with zero mismatches against plain JPEG decoding, and KDE's CI is green on every platform ([pipeline](https://invent.kde.org/danielcamposramos/kimageformats/-/pipelines/1373209)). [in the edition]
- [**KFileMetaData**](https://invent.kde.org/frameworks/kfilemetadata): one `stereo3dLayout` property for every stereo mark the specifications define: the H.264 and H.265 frame packing SEI, the MV-HEVC eye order, all 15 Matroska `StereoMode` values, PNG's `sTER`, JPS and MPO; files without a usable mark report nothing rather than a guess. KDE's CI is green ([pipeline](https://invent.kde.org/danielcamposramos/kfilemetadata/-/pipelines/1372927)). [in the edition]
- [**Gwenview**](https://apps.kde.org/gwenview/): MPO, JPS, stereo PNG, side by side and top and bottom pictures shown in 3D, with Swap Eyes; Photo Sphere pictures stay flat; anaglyph pictures are recognised (54 of 79 in our test set, no false positive on 2,428 ordinary photographs) and can be converted, with a note that the colours are approximate. All 650 JPS photographs of a 3D phone show in stereo, and KDE's CI is green ([pipeline](https://invent.kde.org/danielcamposramos/gwenview/-/pipelines/1373096)). [in the edition]
- **The shared stereo layer for pictures** (`libstereo-layer1`, ours): one policy and one Wayland layer for every picture viewer, as a C++ library and a QML module. File marks come first, then the user's choice; PNG padding is removed; Photo Sphere pictures stay flat; an anaglyph picture stays as it is on anaglyph and 2D screens and becomes a stereo pair on 3D screens. The picture is a surface of its own below the window, declared once as full side by side, with fit, zoom and pan the same in both eyes: 14 of 14 headless KWin runs passed with captures of both eyes, one declaration per picture and none for ordinary images. Gwenview moves onto it next, then the other viewers and the slideshows. [in the edition]

**System**
- [**KInfoCenter**](https://invent.kde.org/plasma/kinfocenter): a page "Stereo 3D and Deep Colour" under Graphics lists, per display, the HDMI 3D modes and the deep colour depths its EDID declares, with the maximum TMDS clock and the HDR it announces. It also says when an HDMI display sits behind a DisplayPort connector, where the adapter decides 3D and deep colour; it was run on the EDIDs of three real displays, and the buttons that open look-ups were checked with stand-in commands. [in the edition]

**Creative programs, not done yet**
- [**Blender**](https://www.blender.org/): its stereo needs X11 and OpenGL, and its HDR needs Wayland and Vulkan, so today one program cannot have both. Our first run stopped at "OpenGL 4.3 required" because every double-buffered visual had become stereo in an earlier Mesa build; that cause has been fixed in Mesa since, and Blender has not been run again. The planned route is a patch in our own build, so its side by side mode declares its viewport and works on any backend. [planned]

## Our branches on KDE's GitLab

Every KDE change above is a branch of our fork on [invent.kde.org](https://invent.kde.org/danielcamposramos), built and tested by KDE's own CI before it is proposed upstream.
Click a branch to read the code, or its CI result to see every job.

| Project | Our branch | KDE's CI |
|---|---|---|
| KWin | [`stereo3d`](https://invent.kde.org/danielcamposramos/kwin/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/kwin/-/pipelines/1373213) |
| KScreen | [`stereo3d-6.7`](https://invent.kde.org/danielcamposramos/kscreen/-/tree/stereo3d-6.7) | [green](https://invent.kde.org/danielcamposramos/kscreen/-/pipelines/1371083) |
| libkscreen | [`stereo3d-6.7`](https://invent.kde.org/danielcamposramos/libkscreen/-/tree/stereo3d-6.7) | [green](https://invent.kde.org/danielcamposramos/libkscreen/-/pipelines/1371082) |
| plasma-wayland-protocols | [`stereo3d-6.7`](https://invent.kde.org/danielcamposramos/plasma-wayland-protocols/-/tree/stereo3d-6.7) | [green](https://invent.kde.org/danielcamposramos/plasma-wayland-protocols/-/pipelines/1371605) |
| KImageFormats | [`stereo3d`](https://invent.kde.org/danielcamposramos/kimageformats/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/kimageformats/-/pipelines/1373209) |
| KFileMetaData | [`stereo3d`](https://invent.kde.org/danielcamposramos/kfilemetadata/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/kfilemetadata/-/pipelines/1372927) |
| Gwenview | [`stereo3d`](https://invent.kde.org/danielcamposramos/gwenview/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/gwenview/-/pipelines/1373096) |
| Spectacle | [`stereo3d`](https://invent.kde.org/danielcamposramos/spectacle/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/spectacle/-/pipelines/1371085) |
| MpvQt | [`stereo3d`](https://invent.kde.org/danielcamposramos/mpvqt/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/mpvqt/-/pipelines/1371080) |
| Haruna | [`stereo3d`](https://invent.kde.org/danielcamposramos/haruna/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/haruna/-/pipelines/1371081) |
| Dragon Player | [`stereo3d-26.04`](https://invent.kde.org/danielcamposramos/dragon/-/tree/stereo3d-26.04) | [green](https://invent.kde.org/danielcamposramos/dragon/-/pipelines/1371597) |
| Kdenlive | [`stereo3d-26.08`](https://invent.kde.org/danielcamposramos/kdenlive/-/tree/stereo3d-26.08) | [green](https://invent.kde.org/danielcamposramos/kdenlive/-/pipelines/1371602) |
| Plank Player | [`stereo3d`](https://invent.kde.org/danielcamposramos/plank-player/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/plank-player/-/pipelines/1372766) |
| Marble | [`stereo3d`](https://invent.kde.org/danielcamposramos/marble/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/marble/-/pipelines/1372607) |
| KAlgebra | [`stereo3d`](https://invent.kde.org/danielcamposramos/kalgebra/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/kalgebra/-/pipelines/1371619) |
| Analitza | [`stereo3d`](https://invent.kde.org/danielcamposramos/analitza/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/analitza/-/pipelines/1371575) |
| Kalzium | [`stereo3d`](https://invent.kde.org/danielcamposramos/kalzium/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/kalzium/-/pipelines/1372737) |
| Kubrick | [`stereo3d`](https://invent.kde.org/danielcamposramos/kubrick/-/tree/stereo3d) | [green](https://invent.kde.org/danielcamposramos/kubrick/-/pipelines/1371613) |
| Krita | [`sparky/stereo-canvas-wayland`](https://invent.kde.org/danielcamposramos/krita/-/tree/sparky/stereo-canvas-wayland) | not run on our fork |

## Documents

- [Stereo labor division](docs/stereo-labor-division.md): who does what to show a stereo picture, from the program to the screen, and what each part never has to care about, tied to the specifications.
  For application, engine and toolkit developers, driver developers, display and hardware people.
- [The VR-engine-to-3D-display formula](docs/formula.md): what a VR engine changes to drive a 3D display instead of a headset, worked out on Half-Life 2.
  For engine and game developers, and anyone porting a VR title to stereo displays.
- [KWin stereo first runs, 2026-10-01](docs/first-runs/kwin-2026-10-01/README.md): the first stereo 3D outputs from KWin on real displays, with photos, logs and the scripts used.
  For KWin and driver developers, and anyone who wants to see what the first runs showed.

## Credit

Sparky Stereo OS, Daniel Ramos's (Capitain Jack) edition of SparkyLinux (by Paweł "pavroo" Pijanowski).

Everyone this edition stands on, by name: [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

## Licence

The documents are licensed under the [Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0): share and adapt them, giving credit to Sparky Stereo OS.

The scripts under `docs/first-runs/` are code and are licensed under the GNU General Public License, version 2 or later (GPL-2.0-or-later); see [LICENSE-GPL-2.0](LICENSE-GPL-2.0).
