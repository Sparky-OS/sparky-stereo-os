# Glossary: the edition's names, from the file to the screen

**For** people who use Sparky Stereo OS, write programs for it or package it: every name the edition carries from the file to the screen, each with what it means here, the page that defines it, and the name it has in every format and interface that also has it.
Where a name belongs to a specification or to the W3C work, the entry points to the [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md), the glossary of the W3C Procedural Memory Knowledge Representation Community Group that Daniel chairs, which gives the clause, the group that owns the text and where to get it.

**Status, 4 November 2026.** Each entry says whether the thing is built (in the edition's packages), coming (built on a branch, in the next package), planned, or a proposal with where it was proposed.
Sparky Stereo OS is in development: a developer ISO for testers exists, and the stereo edition ISO is still being prepared ([where it is going](../README.md#where-it-is-going)).

## Why one name

The same idea gets one name here, in the file formats, in the desktop and in the proposals the edition sends out, so a device that speaks one of them speaks all of them.
No entry invents a second name for an idea that already has one; where a specification names it, that name is used and the clause is in the PM-KR glossary.

## Contents

1. [The edition and its parts](#1-the-edition-and-its-parts)
2. [The contract: one format inside](#2-the-contract-one-format-inside)
3. [Inputs: every packing, read in full](#3-inputs-every-packing-read-in-full)
4. [Outputs: every screen's own format](#4-outputs-every-screens-own-format)
5. [Depth on the desktop](#5-depth-on-the-desktop)
6. [Colour, sound and input devices](#6-colour-sound-and-input-devices)
7. [The system: Lean Code and the edition's own packages](#7-the-system-lean-code-and-the-editions-own-packages)
8. [Proving it](#8-proving-it)
9. [The edition's proposals and registrations](#9-the-editions-proposals-and-registrations)
10. [Where each name is defined elsewhere](#10-where-each-name-is-defined-elsewhere)
11. [Credits](#credits)

## 1. The edition and its parts

| Name | What it means here | Where it is defined |
|---|---|---|
| **Sparky Stereo OS** | Daniel Ramos's edition of SparkyLinux (by Paweł "pavroo" Pijanowski): a Linux system with a new Stereo KDE Plasma desktop, where stereo 3D and deep colour are part of the system, not a feature of a few programs. | [README](../README.md); [architectural synthesis](architectural-synthesis.md) |
| **Mashtabba** | The name of version 9, based on Debian 14 "Forky", KDE Plasma only. | [README, Credit](../README.md#credit) |
| **SparkyLinux** | The distribution the edition is an edition of, created by Paweł "pavroo" Pijanowski. | [architectural synthesis](architectural-synthesis.md#architecture-at-a-glance) |
| **Stereo Desktop** | The desktop itself with depth: what you use sits at the screen, its menus come forward, the windows behind step back, the wallpaper deepest, each a few pixels within limits you choose. | [README, the Stereo Desktop](../README.md#the-stereo-desktop-new-frontiers-for-theme-design); [depth on the desktop](depth-on-the-desktop.md) |
| **Stereo KWin** | KDE Plasma's compositor with the edition's stereo changes: it knows stereo, and only one kind, full side by side; it composes the desktop as two eyes and hands each output the pair. | [stereo labor division](stereo-labor-division.md#kwin-the-middle); the design in one page, [STEREO3D.md](https://invent.kde.org/danielcamposramos/kwin/-/blob/stereo3d/STEREO3D.md) |
| **Display Configuration** | KDE's display settings (KScreen) with the edition's 3D entries: a 3D TV's own 3D modes listed with its other modes, labelled, with a suggestion for games and for movies, never chosen automatically; per screen, the two toggles "Anaglyph" and "Other stereo formats", both off by default; "Keep this configuration?" with a return after 10 seconds. | [architectural synthesis, defaults](architectural-synthesis.md#defaults-per-hardware-type); [the beta guide](guides/beta1-dev-kit.pt-BR.md) |
| **The Graphics page** | System Settings, Hardware (package sparky-stereo-graphics): every GPU listed; Automatic draws the desktop on the GPU with the laptop panel, else the one with the most screens; players, games and anything started in 3D go to the GPU measured best on that machine; other programs stay on the desktop's GPU; browsers follow the power profile; every choice stays the person's. | [architectural synthesis, defaults](architectural-synthesis.md#defaults-per-hardware-type) |
| **sparky-stereo-hardware** | The package that detects the hardware and sets it up, the NVIDIA driver under the edition's version lock and the driver packages of detected racing wheels and flight devices included. | [architectural synthesis](architectural-synthesis.md#defaults-per-hardware-type); [GPU vendors' repositories](gpu-vendor-repositories.md) |
| **Flat Headset** | The Android app that turns a compatible phone in an inexpensive Cardboard-style viewer into a screen for the stereo desktop, each eye on its own half; accepted as a usable desktop over USB on 19 October 2026 on a Redmi Note 7 driven by a 2016 laptop. | [Flat Headset](https://github.com/Sparky-OS/flat-headset); [the measurement](https://github.com/Sparky-OS/flat-headset/blob/main/docs/usb-desktop-2026-10-19.md) |
| **The developer ISO, beta 1** | The ISO for testers: it starts on new PCs with Secure Boot on, on older BIOS PCs and on 32-bit UEFI machines; its Secure Boot key is enrolled through MokManager. | [the guides](guides/README.md) |
| **Sparky-OS** | The GitHub organization that holds the edition's repositories, each package maintainer with full rights over their own. | [README, Credit](../README.md#credit); [repository map](architectural-synthesis.md#repository-map) |
| **The skills** | Instructions for people and AI assistants working on the edition, public in `skills/` and installed by the sparky-stereo-skills package at `/usr/share/sparky-stereo-os`; `sparky-stereo` is read first. | [skills](../skills/README.md); [maintainer workflow](maintainer-workflow.md) |
| **task-sparky-stereo-os-developer, task-sparky-stereo-developer** | The two opt-in tasks: the distribution maintainer's (developer tools, the stack's development files, packaging tools, proof benches and the skills) and the application and game developer's. | [maintainer workflow](maintainer-workflow.md) |
| **AI provenance** | Which AI partners took part, from which lab, in which CRediT roles; Daniel conceives, designs, directs and verifies; no counts by commits or lines. In Knowledge3D's terms the partners are Synthetic Users. | [ai-provenance.md](ai-provenance.md); [PM-KR glossary: Synthetic User](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#synthetic-user) |
| **The three open lists** | The research behind the edition, public and CC0: awesome-stereoscopy, awesome-linux-hdr and awesome-vr. | [README](../README.md#the-base-three-open-lists) |

## 2. The contract: one format inside

### The presentation contract

**Programs describe each picture; the desktop adapts it for each screen.**
The stereo contract in three lines, from [How it works](how-it-works.md):

- Stereo KWin speaks full side by side, at any resolution.
- Programs decode or generate stereo in any standard, and deliver full side by side, at any resolution, to Stereo KWin.
- Outputs, Stereo KWin's filters at the end, one per kind of screen, convert from that to whatever each screen needs.

Sound already works this way on Linux: a program hands PipeWire PCM samples with their rate and channel layout, and PipeWire takes them to every device.
The same principle is written for every medium in the [house formats](house-formats.md) page: describe each content layer once, preserve its information through the stack, and convert for the screen at the output.

| Name | What it means here | Where it is defined | Elsewhere |
|---|---|---|---|
| **House format** | The shared representation of a medium inside the edition, converted where it enters and where it leaves: full side by side for stereo, one plane value per element for depth, the decoder's own bit depth for video colour, PCM at the source's rate for audio, every control raw for input devices. | [house formats](house-formats.md) | broadcast and post-production work this way, and so does PipeWire |
| **Full side by side** | The two eyes as separate complete pictures, side by side, left eye first, each at the resolution it already has, declared once. "Full" names the layout, not a size: any resolution per eye is the pact, half-width and half-height eyes included, so a half top-and-bottom 1920x1080 frame becomes one 3840x540 buffer; no program stretches or squeezes an eye, and Stereo KWin resizes once, at the output. | [how it works](how-it-works.md); [the picture KWin understands](stereo-labor-division.md#the-picture-kwin-understands) | HDMI 1.4a's 3D structure 3, "side-by-side (full)"; the layout of IMAX 3D's two projectors and of SteamVR's screenshots; [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#full-side-by-side-at-any-resolution) |
| **View** | One of the two pictures; named by view, never by eye or side, because a view can be a picture or a depth map. | [house formats, native X11 child placement](house-formats.md#native-x11-child-placement) | the PM-KR glossary's [view table](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#view-eye-constituent-frame) |
| **One view size** | The size one view is shown at, which the surface carries: the `wp_viewport` destination on Wayland, the window on X11, and `_KDE_NET_WM_STEREO_CONTENT_ONE_VIEW_SIZE` for an X11 child that holds both views at full width. | [house formats](house-formats.md#native-x11-child-placement); [x11-child-place](https://github.com/Sparky-OS/stereo-layer/blob/main/docs/x11-child-place.md) | RFC 9559's `DisplayWidth` and `DisplayHeight` |
| **Internal rendering resolution** | How many pixels each eye is drawn with, a quality setting the person picks in the program, higher than the output for sharpness or lower for speed; never matched to the screen by the program. | [the one option a program needs](stereo-labor-division.md#what-a-program-keeps-and-the-one-option-it-needs); [the contract in the skill](../skills/sparky-stereo/SKILL.md#part-one-the-contract) | DPFR's "two resolutions" |
| **Output resolution** | The screen's mode, which belongs to Stereo KWin's output. | same | |
| **A program's 3D options** | Enable 3D, the rendering resolution per eye and a shortcut to Display Settings; no output formats, 3D modes or monitor settings inside a program. A player adds the input corrections: the input packing, and "Swap left and right eyes" per file. | [stereo labor division](stereo-labor-division.md#what-a-program-keeps-and-the-one-option-it-needs); [simulators skill](../skills/simulators/SKILL.md) | |
| **Edge** | Where a conversion happens: before Stereo KWin the program or its library turns whatever it has into full side by side; after Stereo KWin each output turns full side by side into what its display needs; nothing in the middle knows formats. | [stereo labor division, in one minute](stereo-labor-division.md#in-one-minute) | |
| **A program's own output modes** | A program that has its own output modes loses them in the edition's build, so nothing can break the contract; its stereo settings live in a sister folder with "stereo" in the name. This is not removing functionality: Stereo KWin gives every program every output, on every screen. The offer to upstream is a separate patch that keeps the project's own defaults. | [the contract in the skill](../skills/sparky-stereo/SKILL.md#part-one-the-contract) | |
| **The engine, not the program** | When two programs need the same stereo code, it belongs in the layer they share: Qt Multimedia, MpvQt, Mesa, Stereo KWin, the shared libraries. | [the contract in the skill](../skills/sparky-stereo/SKILL.md#part-one-the-contract) | |
| **Stereo in the open stack** | Stereo as a property of the open layers (KDE, the kernel, the file formats), not of one product, so it reaches the screen you already own. | [open stack](open-stack.md) | |

### The declaration

**A program says once that a surface holds full side by side.**
The information travels with the object; the one value exists so that no consumer ever reads other layouts.

| Name | What it means here | Where it is defined | Status |
|---|---|---|---|
| **kde_stereo_content_v1** | The Wayland protocol, the edition's addition to plasma-wayland-protocols: `kde_stereo_content_manager_v1` gives a surface its content object, with the one value `side_by_side_full`. A compositor that adopts it keeps the KDE name after its own prefix, so the shared part says it is the same protocol. | [develop on an ordinary monitor](develop-3d-on-an-ordinary-monitor.md); [libstereo-declare](https://github.com/Sparky-OS/libstereo-declare) | built, protocol version 3 in libstereo-declare 1.8.0 |
| **_KDE_NET_WM_STEREO_CONTENT** | The X11 property, value 3, the same number as HDMI's "side-by-side (full)". | [the picture KWin understands](stereo-labor-division.md#the-picture-kwin-understands) | built |
| **_KDE_NET_WM_STEREO_CONTENT_CHILDREN** | A 2D X11 window's list of its stereo GL children; each child declares itself, Stereo KWin redirects it, Xwayland gives it its own surface, and it is drawn per eye at its place. | [stereo-layer, x11-child-place](https://github.com/Sparky-OS/stereo-layer/blob/main/docs/x11-child-place.md) | built |
| **_KDE_NET_WM_STEREO_CONTENT_CHILD_PLACE** | The proposed property, support version 8, that separates a listed child's buffer resolution from its destination rectangle and allows it below the parent surface, so a player submits source-sized video while the parent paints subtitles and controls at display resolution. | [house formats, native X11 child placement](house-formats.md#native-x11-child-placement) | proposal, needs the matching compositor and library support |
| **libstereo-declare** | The shared helper: `stereo_declare_x11()` and `stereo_declare_wayland()` with `STEREO_SBS_FULL`; on other desktops the calls return `-ENOTSUP`, nothing is sent and the window stays 2D. | [libstereo-declare](https://github.com/Sparky-OS/libstereo-declare) | built, 1.8.0 |
| **wp_content_type_v1, wp_viewporter** | The upstream Wayland protocols the edition uses for a surface's kind of content and for the size a view is shown at. | [libstereo-declare](https://github.com/Sparky-OS/libstereo-declare) (content-type-v1); [stereo labor division, references](stereo-labor-division.md#references) (wp_viewporter) | stable upstream |
| **3D area and 2D part** | A window's 2D part (menus, toolbars, the document around a picture) is its own surface at one eye's size and declares nothing; the 3D area (a stereo video, a 3D viewport, a canvas) is a surface of its own that hands Stereo KWin full side by side; Stereo KWin shows the 2D part identical in both eyes and gives the 3D area each eye's view, in place. Only a program that is stereo and full screen only makes its whole window stereo. | [how it works](how-it-works.md); [stereo window and 3D area skill](../skills/stereo-window-3d-area/SKILL.md) | built |
| **Stereo window** | A window that holds a 3D area; it sits on the ordinary desktop, next to 2D windows, windowed or full screen. | [stereo labor division](stereo-labor-division.md#the-picture-kwin-understands) | built |
| **A player's two layers** | The video, without controls, in a surface underneath, declared only when the video is 3D; the controls, subtitles and on-screen display in the window's own 2D surface above; the same structure for 2D videos, so only the declaration changes. | [stereo and HDR in one declaration, who creates the layer](stereo-hdr-content.md#3-who-creates-the-layer-the-shared-frameworks-never-the-program) | built in mpv, MpvQt, Qt Multimedia, VLC Stereo and MLT |
| **kde-stereo-hdr-content** | The designed successor of the stereo declaration: the stereo value and the HDR description in one object per content layer, so nobody adopts HDR without 3D. | [stereo and HDR in one declaration](stereo-hdr-content.md) | design, not built, not tried on an HDR screen |

### Two cameras, one world

**A program's part is the camera.**

| Name | What it means here | Where it is defined |
|---|---|---|
| **Two cameras, one world** | Look at the one world through two cameras, one per eye: the scene, its simulation and its lights exist once; only what a camera sees is rendered per eye. Not iZ3D's way, which repeats every draw call as if there were two worlds. | [program developers](stereo-labor-division.md#program-developers-applications-games-engines); [stereo two cameras skill](../skills/stereo-two-cameras/SKILL.md) |
| **Off-axis frustum** | Each eye's frustum shifted inward so both views meet at the screen's distance; never toe-in, which bends the picture differently in each eye. | [formula](formula.md#1-the-eyes-a-window-not-a-headset) |
| **Eye separation** | The camera moved half the separation to each side; on a 46-inch set, 2.5 game units (about 64 mm in Source) with the screen plane at 120 units looked right. | [formula](formula.md#1-the-eyes-a-window-not-a-headset) |
| **Screen plane, zero parallax** | The distance at which the two frustums share one window: objects there appear on the screen, nearer ones come out of it, farther ones go behind it. | [formula](formula.md); [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#disparity-parallax-the-screen-plane) |
| **2D stays 2D** | HUD, menus, crosshair, cursor and subtitles drawn once, identical in both eyes, at the screen's depth; 2D never sits over 3D that comes out of the screen. | [program developers](stereo-labor-division.md#program-developers-applications-games-engines); [formula, section 4](formula.md#4-the-2d-layer-hud-and-menus-on-the-screen-plane) |
| **The VR to 3D display formula** | What to change so a game's VR mode drives a 3D TV, projector or monitor instead of a headset, learned on Half-Life 2. | [formula](formula.md) |
| **wiz3D** | iZ3D's code kept alive as a Direct3D proxy by Eff (effcol), maintained in Sparky-OS: stereo for games that never had a VR mode, brought to the same design as the formula. | [README, who builds it](../README.md#who-builds-it); [formula](formula.md) |
| **The standard stereo APIs** | OpenGL quad buffer (`GLX_STEREO`, `GL_BACK_LEFT` and `GL_BACK_RIGHT`), `EGL_EXT_multiview_window`, a Vulkan swapchain with `imageArrayLayers` 2, Direct3D 11.1's stereo swapchain through Wine and DXVK: the edition's Mesa packs them into full side by side and declares them. | [toolkit and library developers](stereo-labor-division.md#toolkit-and-library-developers-qt-wine-mesa-players); [native Linux skill](../skills/native-linux/SKILL.md) |
| **Your sizes stay yours** | A program asks for its window at one eye's size and reads its size from the usual places; on X11 the real window is twice as wide behind the scenes and the synthetic ConfigureNotify gives the program its own size. | [program developers](stereo-labor-division.md#program-developers-applications-games-engines) |

## 3. Inputs: every packing, read in full

**Inputs are read in full.**
Every format a standard defines is read, both eye orders included, so nothing upstream has to change before it works here.

| Name | What it means here | Where it is defined | Elsewhere |
|---|---|---|---|
| **Stereo3DLayout** | The text value the edition's readers report (Qt, KImageFormats, KFileMetaData, stereo-layer, SVGStereo): `mono`; `sideBySide`, `sideBySideQuincunx`, `topBottom`, `checkerboard`, `rowInterleaved`, `columnInterleaved`, `frameSequential`, `blockLaced` and `multiView`, each `LeftFirst` or `RightFirst`; `anaglyphCyanRed` and `anaglyphGreenMagenta`; JPS's `anaglyphRedLeft` and `anaglyphRedRight`; and the depth layouts. A value outside the set means one picture. | [stereo-layer](https://github.com/Sparky-OS/stereo-layer#readme) | one table against every specification's names: [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#layout-packing-arrangement) |
| **Each format's own mark** | A file says it holds two views with its format's own field wherever the specification has one: H.264, H.265 and H.274 frame packing; Matroska `StereoMode`; the MP4 `st3d` box; PNG `sTER`; MPO's CIPA DC-007 tags; HEIF's `ster` and `stem`. Where a format has none, the edition defines a mark with its specification page first. Every mark is registered in stereo-layer and on awesome-stereoscopy's standards page. | [house formats](house-formats.md#the-rules-that-follow-from-it) | [PM-KR glossary, files and containers](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#8-files-containers-streams-and-apis) |
| **The order of decision** | For a video: the person's explicit choice first, because a mark can be wrong; then the stream's own mark; then the frame's shape, side by side only when at least three times as wide as high. For a still: file marks, then input choices, then format fallbacks, then the shape, a side-by-side pair from 2:1 to 3.6:1 only; Photo Sphere XMP vetoes shape detection. | [stereo-layer](https://github.com/Sparky-OS/stereo-layer#readme) | |
| **Swap left and right eyes** | The per-file correction a player or viewer offers for every file shown in 3D, declared or not, because a declaration can be wrong; never offered on 2D content; a program that renders its own 3D scene offers no swap. | [the contract in the skill](../skills/sparky-stereo/SKILL.md#part-one-the-contract) | the definitive swap is the output's, below |
| **Never touch the user's file** | A per-file choice (the eye swap, the packing chosen for an unmarked file) is kept where the program already keeps its per-file state, next to the resume position of "continue playback", and is forgotten with it; the program offers to save it to the file and writes the file only when the person chooses that; once saved, the file carries the correction and the option is unmarked again. | [the contract in the skill](../skills/sparky-stereo/SKILL.md#part-one-the-contract) | |
| **Anaglyph as input** | A red-cyan or green-magenta picture rebuilt into two eyes, so old anaglyph files show on every output. | [stereo-layer, anaglyph input](https://github.com/Sparky-OS/stereo-layer/blob/main/docs/anaglyph-input.md) | |
| **Picture with its depth** | A picture and its depth map are a stereo format: `Stereo3DLayout`'s depth layouts say where the picture and the depth are, `Stereo3DDepth` says what a depth sample means, and libstereo-dibr draws the two views (depth-image-based rendering); every other program shows the picture as before. Apple's portrait HEIF and JPEG, Google's Dynamic Depth and GDepth are read by the edition's KImageFormats. | [stereo-layer, depth marks](https://github.com/Sparky-OS/stereo-layer/blob/main/docs/depth-marks.md) | [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#picture-with-its-depth) |
| **MV-HEVC** | Two views as layers of one stream, assembled into one left-first side-by-side image without resizing by libstereo-av, shared by mpv, Qt Multimedia and VLC Stereo; a base layer is never assumed to be the left eye. | [stereo-layer, MV-HEVC](https://github.com/Sparky-OS/stereo-layer/blob/main/docs/mvhevc.md) | [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#multiview-two-views-as-layers) |
| **Stereo thumbnails and previews** | On a stereo desktop, stereo content shows in stereo wherever it appears, Dolphin's previews included; flat is the person's opt-out. A thumbnail of a stereo file is both views side by side, left first, marked `sideBySideLeftFirst`. | [README, the Stereo Desktop](../README.md#the-stereo-desktop-new-frontiers-for-theme-design); [stereo-layer](https://github.com/Sparky-OS/stereo-layer#readme) | |
| **Stereo screenshots** | A screenshot of a 3D window keeps both eyes and is saved as a 3D photo, JPS or MPO, by the edition's Spectacle; any viewer then shows the left eye, the right eye or the picture in 3D. | [open stack](open-stack.md); [programs](programs.md#create) | |
| **Stereo MIME types** | KImageFormats' plugin for JPS and MPO with their MIME types registered, read back by Pillow and exiftool. | [programs in detail](programs-in-detail.md) | |
| **The players and viewers** | VLC, Haruna, mpv, Bino (360° and 180° films too), PlasmaTube, Dragon Player and Plank Player play 3D films in 3D; Gwenview, digiKam, Showfoto and KolourPaint show and edit 3D photos; Krita paints on a 3D canvas, Kdenlive edits 3D video. | [programs](programs.md) | |

## 4. Outputs: every screen's own format

**Each output converts full side by side into what its device needs; a new kind of display is one new output filter, never a change in any program.**
The families: 3D TVs and projectors, VR headsets, glasses-free 3D displays, any monitor with red and cyan glasses, and a plain 2D monitor, unchanged.

| Name | What it means here | Where it is defined | Status |
|---|---|---|---|
| **Output filter** | The conversion at the end, one per kind of screen. | [outputs: where formats live](stereo-labor-division.md#outputs-where-formats-live) | built |
| **HDMI 3D modes** | A 3D TV's or projector's own 3D modes, every HDMI 1.4a structure: frame packing, field and line alternative, side by side full and half, top and bottom, and picture and depth, listed beside the 2D modes, labelled, never chosen automatically; choosing one sends the HDMI Vendor Specific InfoFrame and the TV switches by itself. | [every output is a filter](architectural-synthesis.md#every-output-is-a-filter-at-the-end); [the beta guide](guides/beta1-dev-kit.pt-BR.md) | built; physical TV tests and virtual-display tests documented |
| **Frame packing** | HDMI structure 0: the left eye, then as many lines as the vertical blanking (the active space), then the right eye, in one taller frame; the mode 3D Blu-ray players send, the one suggested for movies. | [test stereo without a 3D TV](test-stereo-without-a-3d-tv.md#the-idea) | built; [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#frame-packing) |
| **Virtual 3D modes** | Twins of every 2D mode with the same timing and link, on any screen: anaglyph for modern screens and for CRTs; half side by side and top and bottom for a 3D display switched by hand; rows for passive polarised panels; columns for parallax-barrier and lenticular panels; checkerboard for 3D-ready DLP televisions; frame sequential at 100 or 120 Hz for gear with its own glasses sync. Off by default, per output. | [every output is a filter](architectural-synthesis.md#every-output-is-a-filter-at-the-end) | built in Stereo KWin; each kind of panel still needs testers |
| **Anaglyph** | The toggle "Anaglyph" per screen; with it on, the Resolution list also shows `(anaglyph, modern screens)` and `(anaglyph, CRT)`; red and cyan glasses then show the desktop in 3D on an ordinary monitor. The matrices are Eric Dubois's (ICASSP 2001), a set for CRTs and one for modern panels. | [the beta guide](guides/beta1-dev-kit.pt-BR.md); [stereo labor division, references](stereo-labor-division.md#references) | built |
| **Other stereo formats** | The second toggle per screen; with it on, the Refresh rate list shows side by side, top and bottom, rows, columns, checkerboard and frame sequential, and a 3D TV's HDMI 3D modes if it announces them. | [the beta guide](guides/beta1-dev-kit.pt-BR.md) | built |
| **Frame sequential** | One eye per frame: on DisplayPort the kernel sends one eye per frame and signals it, and KWin commits whole pairs so a pair is never split; as a virtual mode at 100 or 120 Hz for shutter glasses and DLP projectors. | [every output is a filter](architectural-synthesis.md#every-output-is-a-filter-at-the-end) | DisplayPort proven on the VKMS virtual display; the run on a native DisplayPort monitor is pending |
| **Dual projection, Mirror rig** | Two outputs as one pair, one eye each, also across two GPUs; the Mirror rig applies the required reflection once, after eye selection. | [matched displays as one stereo output](paired-output-tests.md) | built and run in virtual machines; real timing across two GPUs needs a hardware window |
| **Replica** | A mirror of another output that copies the composed eyes and applies only its own layout, so a 3D television beside an anaglyph panel costs one scene pass per eye. | [every output is a filter](architectural-synthesis.md#every-output-is-a-filter-at-the-end) | built |
| **Swap eyes, per output** | One eye flip per output in Display Configuration, for a display, projector or pair of glasses that shows the eyes reversed; the definitive swap, applied to every 3D mode of that output. | [outputs: where formats live](stereo-labor-division.md#outputs-where-formats-live); [the contract in the skill](../skills/sparky-stereo/SKILL.md#part-one-the-contract) | built; some modes still come as left-first and right-first twins |
| **Keep the pair together** | Both eyes belong to the same source frame; composition and output conversion preserve that association, and an output never advances one eye to a new frame while keeping the other. | [KWin: the middle](stereo-labor-division.md#kwin-the-middle) | built |
| **A 2D screen** | Shows the left eye, unchanged; stereo themes render normally on 2D; the depth cues of the desktop read as the ordinary effects. | [depth on the desktop](depth-on-the-desktop.md) | built |
| **Headsets** | A headset is one more output filter fed the same full side by side: through OpenXR (KDE's own VR Mode, a draft, on Monado or WiVRn), through SteamVR where the headset works on Linux, and a phone in a viewer through Flat Headset. "VR is also a stereo monitor." | [README](../README.md#vr-is-also-a-stereo-monitor); [develop on an ordinary monitor, headsets](develop-3d-on-an-ordinary-monitor.md#7-headsets) | the phone over USB accepted; tracked headsets in development |
| **HT mode** | A headset used as a fixed 3D screen. | [sound: the same division](stereo-labor-division.md#sound-the-same-division) | |
| **Stereo Spectator** | One person plays in a headset while the room watches the 3D television; the sound stays in the room. | [sound: the same division](stereo-labor-division.md#sound-the-same-division) | |
| **Virtual screens in VR and AR** | A virtual screen placed inside a VR or AR experience is one more output: stereo content on it keeps its two views, each eye seeing its own. | [architecture at a glance](architectural-synthesis.md#architecture-at-a-glance) | in development, with the tracked headset path |
| **Glasses-free displays** | The compositor reports where a window is, and only the display vendor's weaver computes the lens phase, through DisplayXR's window geometry specification. | [house formats, references](house-formats.md#references); [open stack](open-stack.md) | planned, design agreed with DisplayXR |
| **The boot chain** | The boot splash and the login screen follow the 3D mode saved for the main screen, so the desktop is in 3D from the moment the machine switches on. | [README, the Stereo Desktop](../README.md#the-stereo-desktop-new-frontiers-for-theme-design) | built |
| **A virtual machine's window** | A QEMU guest with HDMI 3D modes, shown in stereo on the host by QEMU's own window, virt-viewer, virt-manager and Karton, each eye carried on its own over SPICE. | [a virtual machine with a 3D display](stereo-vm.md) | built in the edition's QEMU, SPICE and Karton packages; the guest driver patches not yet in the kernel |
| **The automatic 3D mode switch** | The switch Stereo KWin makes into a 3D mode, on an output that has them, while stereo content is shown; a window drawn per eye only for its desktop depth does not count as stereo content. | [depth inside every window](depth-inside-windows.md#how-the-depth-reaches-every-window); [STEREO3D.md](https://invent.kde.org/danielcamposramos/kwin/-/blob/stereo3d/STEREO3D.md) | built |

## 5. Depth on the desktop

**Three places, declared: sunk, screen and popped.**
All subtle, a few pixels, with the limits the person's own: System Settings, "3D Depth".

| Name | What it means here | Where it is defined | Elsewhere |
|---|---|---|---|
| **sunk, screen, popped** | The three planes: a thing is behind the screen, on it, or in front of it. The active window sits at the screen; its menus, tooltips, notifications and dialogs pop; the wallpaper and the windows behind sink. | [depth on the desktop](depth-on-the-desktop.md) | Union's `depth` value, SVGStereo's `svgstereo:depth`, the css-spatial proposal: [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#the-three-planes-sunk-screen-popped) |
| **3D Depth** | The System Settings page with the person's limits, stored in `kwinrc`, group `[StereoDepth]`, in pixels of a view 1920 wide, scaled to each screen; zero switches depth off. | [depth inside every window, the values](depth-inside-windows.md#the-values-and-what-each-one-is-for) | |
| **SunkLimit** | 10 px by default: desktop elements behind the screen, the windows in the pile stepping back, the wallpaper deepest. Behind the screen is like looking through a window, so this limit can be the larger one. | same | |
| **PoppedLimit** | 4 px by default: desktop elements in front of the screen, menus, popups, tooltips and dialogs, also the ones a window draws inside itself. | same | |
| **ElementLimit** | 1 px by default: a window's own elements (buttons, fields, tabs, rows, check boxes), either way, from the surface they lie on; the theme's shadows give the sign and the strength. 12 px is a measuring scale for tests, never a default. | same | |
| **The pile** | Everything in between is Stereo KWin's, by stacking order: background windows fan out from sunk towards popped, always behind the active window, in the same order as in 2D, so a pile of windows reads as a pile of papers; a window in the pile is a flat sheet, and its stereo content stays 3D. | [depth on the desktop](depth-on-the-desktop.md) | |
| **The stereo window, the edge rule** | A popped thing that touches the edge of its screen stays at the screen's depth, because depth in front of the screen that the screen's frame cuts through looks broken; panels touch the edges, so they sit at the screen. | [for theme designers](for-theme-designers.md#what-you-can-design-with-built) | SVGStereo's "stereo window" |
| **Shadows lie on what they fall on** | A window's shadow takes the depth of whatever it lands on, not of the window that casts it. | same | |
| **The pointer** | Takes the depth of what it is over. | same | |
| **Pinned windows** | A window kept above others stays popped over everything, like a webcam over slides. | [README, the Stereo Desktop](../README.md#the-stereo-desktop-new-frontiers-for-theme-design) | |
| **Pop: a little scale and a little depth, together** | One value per element gives both cues: bigger and nearer when popped, smaller and further when sunk; text and the click area follow their element; on a 2D screen the same scale plus a move up and to the left. | [depth on the desktop](depth-on-the-desktop.md); [for theme designers](for-theme-designers.md#pop-a-little-scale-and-a-little-depth-together-designed-coming) | designed, coming |
| **Depth inside every window** | Each element of the active window at a depth of its own, a pixel or less from the window: an outer shadow raises, an inset shadow sinks, the strongest shadow in the window a whole step of `ElementLimit`; the current tab on the window and the other tabs stepping back; levels fitted inside the limit the way Stereo KWin fits menus. | [depth inside every window](depth-inside-windows.md) | built in the edition's Qt, KWin and protocol packages |
| **Stereo Union** | The edition's fork of Union, KDE's style engine, named apart so developers never take it for KDE's own: it gives every element inside a window a small depth of its own, from the theme's shadows or a declared value, at a pixel or less. | [depth inside every window](depth-inside-windows.md); [for theme designers](for-theme-designers.md) | built on the edition's branch |
| **Stereo Union's depth value** | `depth: sunk | screen | popped | <percentage> | <number>` in Stereo Union, the edition's fork of KDE's Union style engine, a fraction of the user's limits; a declared depth always wins over shadow inference. | [for theme designers](for-theme-designers.md); [the public question to Union](https://discuss.kde.org/t/real-depth-for-oceans-elevation-a-design-question-for-union/50744) | built on the edition's branch |
| **Stereo Oxygen** | The edition's own look, made from KDE's Oxygen, the first theme made this way, with icons drawn as a pair, one for each eye. | [README, the Stereo Desktop](../README.md#the-stereo-desktop-new-frontiers-for-theme-design); [for theme designers](for-theme-designers.md) | coming |
| **3D backgrounds** | Stereo video and stereo stills behind the desktop, on the sunk side, through Jeromy Streets' video wallpaper plugin (org.kde.video); a 3D photo as the background keeps its own pop and dive far behind every window. | [for theme designers, 3D backgrounds](for-theme-designers.md#3d-backgrounds-coming) | the photo built; the video coming |
| **The Theme Editor** | The planned central editor where a theme's depth rules, 3D backgrounds and stereo icons are composed. | [architecture infographic](architecture-infographic.md) | planned |
| **Effects with their own depth** | A closing window that flies toward you in pieces, or dives behind the screen and bounces on a floor; window switchers that fan out in 3D. | [README, the Stereo Desktop](../README.md#the-stereo-desktop-new-frontiers-for-theme-design); [for theme designers](for-theme-designers.md#effects-with-their-own-depth-designed-coming) | built on the KWin branch, coming in the next package |
| **The Desktop Cube** | A 3D application treated like a game: its scene hands Stereo KWin full side by side, one camera per eye; its faces are the real desktops, each a stereo surface; when it closes on one desktop, it is the desktop; the seed of the VR home. | [depth on the desktop](depth-on-the-desktop.md#the-desktop-cube-what-one-format-makes-possible) | coming |
| **Stereo screensavers** | The classic starfield and the stereo savers in real 3D. | [README, the Stereo Desktop](../README.md#the-stereo-desktop-new-frontiers-for-theme-design) | built |

## 6. Colour, sound and input devices

| Name | What it means here | Where it is defined | Elsewhere |
|---|---|---|---|
| **Deep colour** | 10, 12 or 16 bits per component where the content, the software and the display support them; a 2010 to 2013 3D TV takes 12 bits; the house format for video colour is the decoder's own bit depth, never reduced in the middle. Deep colour alone is not HDR. | [house formats](house-formats.md); [architectural synthesis, deep colour and HDR](architectural-synthesis.md#deep-colour-and-hdr) | HDMI's `DC_30bit`, `DC_36bit`, `DC_48bit`; the DRM connector's "max bpc": [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#deep-colour) |
| **HDR in one declaration** | The designed path: per content layer the stereo value, the colour description (an upstream `wp_image_description_v1`) and the gain map per eye; per output, to linear light, the gain map weighted by that output's headroom, gamut and tone mapping, encoding at the output's depth; an SDR deep-colour 3D TV gets HDR tone-mapped into its 12 bits. | [stereo and HDR in one declaration](stereo-hdr-content.md) | [PM-KR glossary, HDR](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#hdr-the-signals-and-the-reconstruction); design only, not tested on an HDR screen |
| **Audio house format** | PCM at the source's own rate, the edition's floor 24 bit at 48 kHz; the sound server follows the source's rate instead of resampling; per device the best format the hardware takes, encoded formats passed through to the TV when its EDID accepts them, binaural on headphones for multichannel sound. | [house formats](house-formats.md); [audio skill](../skills/audio/SKILL.md) | being built |
| **Sound in XR** | A program renders its sound scene, never the speakers: speakers follow the room, headphones follow the head with binaural rendering through PipeWire's filter chain and SOFA (AES69) filters; HT mode and the Stereo Spectator keep the sound in the room. | [sound: the same division](stereo-labor-division.md#sound-the-same-division) | planned |
| **Input devices, raw** | Every button, axis and hat as the device reports it, in the kernel driver and SDL without dropping controls; KDE's game controller page shows every raw control beside the mapped gamepad view. | [house formats](house-formats.md); [game controller skill](../skills/gamecontroller/SKILL.md) | coming |

## 7. The system: Lean Code and the edition's own packages

| Name | What it means here | Where it is defined | Elsewhere |
|---|---|---|---|
| **Lean Code** | Prepare ahead of consumption: every text file a package ships has an authored form people read and a lean form the machine reads, recorded against each other, the original always restorable; measured on a 2016 laptop: builds against kernel headers 6 to 9 % faster, desktop programs 3 to 6 % smaller, boot unchanged. | [Lean Code packages](lean-code-packages.md); [the measurement](proofs/lean-code-a10-aba.md); [lean-code skill](../skills/lean-code/SKILL.md) | offered to PM-KR as a stepping stone: [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#lean-code) |
| **lc1** | The first format of the Lean Code mark, the control field `Sparky-Lean-Code: lc1 <manifest SHA-256>`, so clients do not repeat the projection; it certifies the qualified installed-payload pass, nothing more. | [Lean Code packages, package contract](lean-code-packages.md#package-contract) | |
| **The HR package** | `<package>-lc-hr`, the companion at the same version that holds the full authored text of the changed files; required in the repository, not a runtime dependency, not on the ISO by default. | [Lean Code packages](lean-code-packages.md#configuration-documentation-and-debugging) | |
| **dpkg-stereo** | The edition's tool: `--hr` retrieves an original, `--resolve` maps a lean line back to the authored source by its content and reports what it cannot resolve, `--verify` checks the projections, `--restore` reverses local projections. | [Lean Code packages](lean-code-packages.md) | |
| **The Cushion Swap File** | Daniel Ramos's memory-pressure design: the swap area stays off, is switched on only when memory runs low or falls fast, and is switched off again when it is safe; not a stereo mechanism. | [programs in detail](programs-in-detail.md); [architectural synthesis](architectural-synthesis.md#memory-policy-and-lean-code) | |
| **GPU vendors' repositories** | CUDA and ROCm update from the vendors' repositories, and the display driver stays the edition's, through apt pins: the edition's build of NVIDIA's open kernel modules and the amdgpu driver in its kernel carry HDMI 3D and deep colour. | [GPU vendors' repositories](gpu-vendor-repositories.md) | |
| **The edition's kernel** | Linux 7.3 with the edition's stereo patches: HDMI 1.4a 3D on amdgpu and NVIDIA's open kernel modules, every 3D structure, DisplayPort frame sequential behind a per-connector opt-in, VKMS speaking HDMI 3D, deep colour. | [README](../README.md#watch-and-play); [how it works](how-it-works.md) | |
| **sparky-ca** | Installation of CA certificates into the system; the ICP-Brasil catalogue and its checks are in the certificate skills. | [repository map](architectural-synthesis.md#repository-map); [certificate manager skill](../skills/certificate-manager/SKILL.md) | |
| **APTus** | Sparky's app installer, where org.kde.video is offered; the edition's app centre work is sparky-aptus-stereo-appcenter. | [for theme designers](for-theme-designers.md#3d-backgrounds-coming); [repository map](architectural-synthesis.md#repository-map) | |
| **Another distribution** | The edition is not packaged for other distributions, because stereo here is the whole path from a program to the screen; every fix is open for any distribution to adopt, and the goal is upstream. | [other distributions](other-distributions.md) | |

## 8. Proving it

**A change is done when it is measured, not when it compiles.**

| Name | What it means here | Where it is defined |
|---|---|---|
| **Both eyes, captured** | Clips or scenes marked so each eye can be read by a script, captured from the real compositor, checked over time: the right colour in each eye, the same frame number in both, one declaration per stereo surface, nothing declared for 2D content. | [the skill, what counts as proof](../skills/sparky-stereo/SKILL.md#part-two-what-counts-as-proof); [stereo proof rig skill](../skills/stereo-proof-rig/SKILL.md) |
| **The 2D control** | The changed program with stereo off against the distribution's own build, 0 differing pixels: the answer to "you will break something else". | same |
| **Proof pairs** | Every milestone that changes what a person sees is shown as a red-cyan anaglyph and an MPO, so anyone can see it with paper glasses or in 3D. | [proofs](proofs/README.md); [the screenshot gallery](screenshots/README.md) |
| **vkms-stereo-bench** | The bench that checks HDMI 3D modes on a virtual display in a QEMU guest: mode discovery, timing, where each eye lands, with optional compositor checks; it does not test the cable or the InfoFrame. | [test stereo without a 3D TV](test-stereo-without-a-3d-tv.md) |
| **The stereo virtual machine** | A QEMU guest whose display has HDMI 3D modes, shown on the host as a stereo window. | [a virtual machine with a 3D display](stereo-vm.md) |
| **hibernate-bench** | Checks hibernation under Secure Boot in a virtual machine, with failing expectations recorded. | [hibernate-bench](../tools/hibernate-bench/README.md) |
| **The measurements** | What stereo costs KWin on a 2016 laptop: 24 fps in every desktop case, 2D and 3D. | [hardware](hardware.md); [the measurement](measurements/kwin-stereo-cost-a10-2026-10-23.md) |
| **Our branches on KDE's GitLab** | Every KDE change as a branch of the edition's fork on invent.kde.org, built and tested by KDE's own CI before it is proposed upstream. | [KDE branches](kde-branches.md) |
| **Performance is information, not a gate** | Stereo work is judged by running correctly to the specification; its cost is measured and reported, never a speed target that holds the work. | [the skill, what counts as proof](../skills/sparky-stereo/SKILL.md#part-two-what-counts-as-proof) |
| **Evidence over authority** | How a project keeps trust when contributions become cheap: judge the artefact, not the author. | [evidence over authority](evidence-over-authority.md) |

## 9. The edition's proposals and registrations

Never presented as standards; each with where it was proposed and its status on 4 November 2026.

| Name | What it proposes | Where | Status |
|---|---|---|---|
| **Matroska StereoMode 15 to 20** | Packed picture-and-depth layouts: picture and depth side by side or top and bottom in either order, four rows with graphics and graphics depth, four quarters with background and background depth. | [IANA Matroska registry](https://www.iana.org/assignments/matroska), reference [stereo-layer v1.9.0](https://github.com/Sparky-OS/stereo-layer/blob/v1.9.0/docs/depth-marks.md) | assigned 26 October 2026, Specification Required, change controller Daniel Ramos |
| **Matroska TrackPlaneType 3 to 5** | Depth of the left eye plane, of the right eye plane and of the background plane, in `TrackCombinePlanes`. | same registry | assigned 20 October 2026, First Come First Served |
| **SVGStereo** | A mark for SVG, which has none of its own: `svgstereo:layout="sideBySideLeftFirst"` on the root, and `svgstereo:depth` with the three planes for single-view drawings. | [SVGStereo](https://github.com/Sparky-OS/svgstereo); [WICG proposals #316](https://github.com/WICG/proposals/issues/316) | proposal, opened 1 November 2026 |
| **Dynamic Procedural Foveated Rendering (DPFR)** | Procedures first, the image last: procedural layers evaluated every frame at the detail each part of each eye needs, one high-resolution texture per surface as the last layer; in Portuguese, Renderização Foveada Procedural Dinâmica. | [DPFR](dynamic-procedural-foveated-rendering.md); [glTF #2696](https://github.com/KhronosGroup/glTF/issues/2696) | proposal, named 25 October 2026; [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#dynamic-procedural-foveated-rendering-dpfr) |
| **Spatial Roaming Network (SRN)** | A cellular model for finding places, moving between them and receiving their content near the visitor: cells real and virtual, irradiators, handover, roaming, edge delivery; in Portuguese, Rede de Roaming Espacial. | [SRN](spatial-roaming-network.md) | proposal, named 28 October 2026; [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#spatial-roaming-network-srn) |
| **The depth words for the web** | Plain depth words (sunk, screen, popped) and depth limits the person sets, for css-spatial. | [WebKit/explainers #163](https://github.com/WebKit/explainers/issues/163) | proposal, opened 4 November 2026 |
| **kde-stereo-content-v1** | The declaration protocol, the edition's addition to plasma-wayland-protocols, with Stereo KWin as its reference implementation; an adopting compositor keeps the KDE name after its own prefix. | [develop on an ordinary monitor](develop-3d-on-an-ordinary-monitor.md) | built; the Wayland community's own protocol, xx-stereoscopy-v1, is in review at [wayland-protocols !533](https://gitlab.freedesktop.org/wayland/wayland-protocols/-/merge_requests/533) |
| **Native X11 child placement** | `_KDE_NET_WM_STEREO_CONTENT_CHILD_PLACE`, support version 8. | [house formats](house-formats.md#native-x11-child-placement); [stereo-layer](https://github.com/Sparky-OS/stereo-layer/blob/main/docs/x11-child-place.md) | proposal |
| **kde-stereo-hdr-content** | Stereo and HDR in one declaration. | [stereo and HDR in one declaration](stereo-hdr-content.md) | design |
| **A side-by-side-only sink profile** | Two letters of 27 October 2026 to HDMI Licensing Administrator and the Wi-Fi Alliance, asking for a low-cost, certifiable 3D profile for single-panel headsets, at the panel's native timing. | [the second stereo report](https://www.w3.org/publications/spec-generator/?type=respec&url=https://raw.githubusercontent.com/w3c-cg/pm-kr/main/reports/source/stereo-3d-closed-stacks-open-standards.html) | petitions; the Wi-Fi Alliance answered it has no current plans |
| **The W3C work** | Daniel chairs the PM-KR Community Group with Milton Ponson; the two stereo reports, the Media and Entertainment IG talk of 13 October 2026, the TPAC 2026 inputs and the Web of Worlds Task Force map are individual input there. | [README, where it is going](../README.md#where-it-is-going); [PM-KR](https://github.com/w3c-cg/pm-kr) | individual input, not group decisions |
| **Merged outside Sparky Stereo** | The one list of changes merged in other projects, each with the maintainer who merged it: 24 changes in 14 projects by 15 maintainers between 16 September and 4 November 2026, and 7 in review. | [upstream merges](upstream-merges.md) | |

## 10. Where each name is defined elsewhere

The [PM-KR glossary](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md) holds, for every name above that a specification also has, the clause, the body that owns the text and where to get it:

- the views and their names in H.264, H.265, H.274, ISO/IEC 14496-12, HEIF, RFC 9559, OpenEXR and WebXR Layers ([view, eye, constituent frame](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#view-eye-constituent-frame));
- one table of every layout against every specification's name for it ([layout, packing, arrangement](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#layout-packing-arrangement)) and the eye order ([eye order](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#eye-order));
- the depth planes, parallax and the picture with its depth ([depth](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#5-depth));
- the display families and their links, HDMI, DisplayPort, CTA-861, OpenXR, DisplayXR and Miracast ([outputs](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#outputs-every-display-family));
- colour and HDR ([colour and HDR](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#7-colour-and-hdr));
- the still formats, containers, streams and graphics APIs ([files, containers, streams and APIs](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#8-files-containers-streams-and-apis));
- the registries ([registries](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#9-registries));
- the bodies and groups, with the price of each paid text and the free twins ([the bodies and groups](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#10-the-bodies-and-groups-and-where-to-get-their-texts));
- the knowledge layer's own terms: PM-KR, procedure, node, the four layers, dual-client equivalence, provenance by roles, the Synthetic User, the Web of Worlds ([knowledge stored once](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#1-knowledge-stored-once-pm-krs-own-terms), [the Web of Worlds](https://github.com/w3c-cg/pm-kr/blob/main/glossary/README.md#3-the-web-of-worlds)).

The standards themselves, with primary references and the implementations useful for cross-checking, are on awesome-stereoscopy's [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md).

## Credits

Named from each project's own records.

- Sparky Stereo OS: Daniel Ramos (Capitain Jack), the edition's architect; SparkyLinux: Paweł "pavroo" Pijanowski; the people and projects the edition builds on, in [ATTRIBUTIONS.md](../ATTRIBUTIONS.md).
- The two human contributors so far: Jeromy Streets (org.kde.video, the video wallpaper) and Eff (effcol, wiz3D).
- The AI partners, by lab and CRediT role: [AI provenance](ai-provenance.md).
- The maintainers who merged the edition's changes, each named on [Merged outside Sparky Stereo](upstream-merges.md).
- The W3C side: Milton Ponson, co-chair of PM-KR; Dong-Young Lee (LG Electronics), who reviewed the first stereo report.
- Anaglyph: Eric Dubois, ICASSP 2001; the depth comfort literature: Shibata, Kim, Hoffman and Banks (Journal of Vision, 2011).
- The VKMS bench builds on Louis Chauvet's VKMS series and José Expósito's configfs work.
- The Linux kernel's HDMI 3D code: Intel's i915 since Linux 3.13 (2013), and the DRM developers who wrote `drm_edid.c`.

AI partners were leveraged in the production of this work.

HDMI®, HDMI® High-Definition Multimedia Interface and the HDMI® Logo are trademarks or registered trademarks of HDMI Licensing Administrator, Inc.
