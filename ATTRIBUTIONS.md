# Attributions & Acknowledgments

**Sparky Stereo OS** stands on the shoulders of giants.
It is Daniel Ramos's (Capitain Jack) edition of SparkyLinux (by Paweł "pavroo" Pijanowski), built on Debian and KDE Plasma, and almost every line of code it ships was written by someone else first.
This document names them: the projects, the people inside them, the specifications, the communities, the partners, the inspirations and the family that made this edition possible.
Our contribution lies in making stereo 3D and deep colour a property of the open desktop stack, and in fixing each program where it breaks on the way to the screen, not in claiming to have invented any of it.

Names are given as each project gives them: in its about box, its copyright file or its Debian packaging, and for the people who reviewed our patches, as their public profiles show them.
Contact details are left out on purpose.

---

## In memoriam: Luis Carlos de Alencar, "Cau", and Lavinha Campos, "Laví"

**Luis Carlos de Alencar**, "Cau", was Daniel's master on Linux.
He is the one who introduced Daniel to Linux, back in the 1990s, and he paved the way for Daniel to become what he is today.
He did not live to see this edition, and it carries what he started: every package built here, every driver fixed and every program taught to show two eyes goes back to the day Cau sat him in front of Linux for the first time.

**Lavinha Campos**, "Laví", Daniel's second first mother, stands alongside him here.

**Obrigado, Cau. Obrigado, Laví.**

---

## Core Philosophy: Adaptation, Not Invention

**What we did NOT invent:**
- Stereoscopy itself: Charles Wheatstone described binocular vision and the stereoscope in 1838.
- The packings of a stereo picture: side by side, top and bottom, frame packing, checkerboard, row and column interleaving, frame sequential (ITU-T H.264 and H.265, Annex D; HDMI 1.4).
- Anaglyph, and its colour matrices (Eric Dubois, 2001).
- Quad-buffer OpenGL, EGL multiview windows and Vulkan multiview (Khronos).
- Stereo photo files: MPO (CIPA DC-007) and JPS (VRex), and the PNG `sTER` chunk.
- Matroska's `StereoMode` (RFC 9559).
- Wayland's subsurfaces, `wp_viewporter` and the compositor model.
- KWin, Plasma, KDE Frameworks, Qt, Debian's packaging, SparkyLinux and its tools.

**What we DID contribute:**
- **One format inside the desktop:** programs hand KWin full side by side, both eyes at full size, left eye first, declared once (`kde-stereo-content-v1`, `libstereo-declare`), and KWin's outputs convert it for each screen: a 3D television's HDMI 3D modes, anaglyph, or the left eye on a 2D screen.
- **The separation rule:** a window's 2D part and its 3D area are separate surfaces, so menus and text stay crisp at one eye's size while the 3D area carries both eyes.
- **The depth rules for the desktop:** sunk, screen and popped planes, text at its element's depth, effects of a few pixels.
- **A fix in each program where stereo or deep colour broke**, in that program's own style, listed below with the people who wrote the program.
- **Fixes offered to the projects they belong to**, four of them merged so far (section 7).
- **The edition's packaging:** our patches on Debian's own source packages, role tasks for gamers, designers, creators, musicians, scientists, students and simmers, and a system that keeps itself small.

---

## 0. Foundations

### 0.1 Debian, the mother distribution

**Source**: [Debian Project](https://www.debian.org/)
**License**: the Debian Free Software Guidelines; each package under its own licence

**What Debian provides**:
- The whole base: Debian 14 "Forky", its packages, its archive and its policy.
- The packaging we build on: every program we change is Debian's own source package with our patches added, Debian's rules and package split kept, and `+stereo3dN` added to its version.
- "Powered by Debian" stands in the edition's wordmark on purpose.

**Credit**: the Debian Project and every Debian developer and maintainer since 1993.
By name, the Debian maintainers of the packages we carry with our patches, as their packaging records them:

| Package | Debian maintainers |
|---|---|
| KWin, KFileMetaData | Debian Qt/KDE Maintainers; Aurélien Couderc, Patrick Franz |
| Qt (qtbase), Qt Multimedia | Debian Qt/KDE Maintainers; Patrick Franz |
| Analitza, KAlgebra, Dragon Player | Debian Qt/KDE Maintainers; Aurélien Couderc |
| Kalzium | Debian Qt/KDE Maintainers; Aurélien Couderc, Sune Vuorela |
| Kubrick | Debian Qt/KDE Maintainers; Aurélien Couderc, Daniel Schepler, Lisandro Damián Nicanor Pérez Meyer, Sune Vuorela |
| Marble | Debian Qt/KDE Maintainers; Aurélien Couderc, Matthias Geiger |
| Krita | Debian Qt/KDE Maintainers; Pino Toscano |
| KScreen, libkscreen, Spectacle, KInfoCenter, KImageFormats, plasma-wayland-protocols | Debian Qt/KDE Maintainers |
| Haruna, MpvQt | Debian KDE Extras Team |
| Kdenlive, MLT | Patrick Matthäi |
| Mesa | Debian X Strike Force; Andreas Boll |
| Xwayland | Debian X Strike Force; Timo Aaltonen |
| egl-wayland | Timo Aaltonen |
| FFmpeg | Debian Multimedia Maintainers; Reinhard Tartler, James Cowgill, Sebastian Ramacher |
| mpv | Debian Multimedia Maintainers; Alessandro Ghedini, Reinhard Tartler, James Cowgill, Sebastian Ramacher |
| VLC | Debian Multimedia Maintainers |
| Avogadro libraries | Debichem Team; Drew Parsons |
| Netgen | Debian Science Maintainers; Kurt Kremitzki, Francesco Ballarin |
| GNU Octave | Debian Octave Group; Sébastien Villemot, Rafael Laboissière |
| Bino | Debian QA Group, which keeps it alive in Debian |
| protontricks | Debian Games Team; Stephan Lachnit |
| libcapi20 (carried unchanged) | Jan-Michael Brummer |

### 0.2 SparkyLinux and Paweł "pavroo" Pijanowski

**Source**: [SparkyLinux](https://sparkylinux.org/)
**License**: GNU GPL for its own tools; each package under its own licence

**What SparkyLinux provides**:
- The distribution this edition belongs to: a Debian-based system that follows Debian closely, ready to use out of the box, with its own repositories, keyring and tools.
- **sparkybackup**, which makes a live ISO from a running system: the way Sparky builds its images, and the way this edition will build its own.
- The Sparky look: the Plymouth theme `sparky-lines`, Daniel's edit of the theme of Debian 8 "Jessie", with his own background and Sparky logo; the edition's SPARKYOS / POWERED BY DEBIAN / STEREO 3D EDITION wordmark is built from that logo's exact pixels (provenance in section 12).

**Paweł "pavroo" Pijanowski**, the creator and maintainer of SparkyLinux:
- Built SparkyLinux and has kept it going, year after year, as a free and community-minded Debian derivative.
- Personally encouraged Daniel to take his first steps with GitHub and to deepen his Bash and Linux automation skills; many of the habits behind this edition's scripts were formed on SparkyLinux.
- With Daniel, developed [Sparky-OS](https://github.com/Sparky-OS) from their SparkyLinux work, giving its small-business server and workstation goals an identity of their own; this repository lives there.
- His server and his packages stay his: changes to them go to him first, and the edition tells him what it publishes.

**Our gratitude**: there is no Sparky Stereo OS without SparkyLinux, and no SparkyLinux without Paweł.
The edition is Daniel's; SparkyLinux is Paweł's; the credit line on every package and page says both.

### 0.3 KDE

**Source**: [KDE](https://kde.org/), code at [invent.kde.org](https://invent.kde.org/)
**License**: GPL, LGPL and others, per project

**What KDE provides**: Plasma, KWin, KDE Frameworks and the applications, the desktop this edition is built for and the only one it ships.
Daniel has loved KDE since his early days with Linux.
Our KDE changes live in forks on invent.kde.org, offered back to KDE as one patch set.

**Credit**: the KDE community; the people of each KDE program are named in the sections below.

### 0.4 Conectiva and its programmers

**Source**: [Conectiva on Wikipedia](https://en.wikipedia.org/wiki/Conectiva), [APT-RPM](https://en.wikipedia.org/wiki/APT-RPM), [Synaptic](https://en.wikipedia.org/wiki/Synaptic_(software)), [Exame on Conectiva's history](https://exame.com/tecnologia/conectiva-linux-sistema-operacional-do-parana-que-quase-venceu-o-windows-no-brasil-dos-anos-2000/)

Conectiva was Brazil's own Linux distribution, founded in Curitiba, Paraná, on 28 August 1995 by Arnaldo Carvalho de Melo and a group of friends, to bring Linux to Portuguese and Spanish speakers.
Its programmers gave the free software world more than a distribution:
- **Arnaldo Carvalho de Melo**, its founder, a Linux kernel developer to this day.
- **Marcelo Tosatti**, who maintained the stable Linux kernel while at Conectiva.
- **Alfredo Kojima**, creator of the Window Maker window manager, who ported Debian's APT to RPM (apt-rpm).
- **Gustavo Niemeyer**, who carried apt-rpm forward.
- And the team behind **Synaptic**, the graphical package manager created at Conectiva that Debian users still open today.

Conectiva joined MandrakeSoft in 2005, which became Mandriva.
**Our gratitude**: for proving, in Brazil and in Portuguese, that Linux could be ours.

### 0.5 deb-multimedia

**Source**: [deb-multimedia.org](https://www.deb-multimedia.org/), maintained by Christian Marillat

Daniel's own media programs (VLC, mpv, OBS, HandBrake) come from deb-multimedia, so the edition's FFmpeg and mpv patches are being moved onto its packages rather than Debian's.

---

## 1. Where it started: the people behind the 3D

### 1.1 Vadim Asadov and iZ3D (special thanks)

**Source**: [the 3D origin story](https://github.com/danielcamposramos/sony-bravia-linux/blob/main/docs/3d-origin-story.md), [the iZ3D driver source](https://github.com/bo3b/iZ3D)

In February 2011, Daniel could not afford iZ3D's hardware.
He wrote to **Vadim Asadov**, CEO of iZ3D, the San Diego company behind the 22" passive-polarized 3D monitor and the DirectX driver that forced stereo 3D into games that never shipped with it, with a market-entry pitch for Brazil and a dream: "multiple stereo rendering or capturing to achieve an real hologram", in his own words of 2011.
Vadim answered the business case honestly, and then **gifted Daniel a full "iZ3D All Outputs" licence** (2 February 2011).
That licence is how Max Payne played in anaglyph stereo on an ordinary monitor, years before Daniel touched a 3D television, and it is where this edition began.

After iZ3D closed, Vadim and his team gave the driver's source to the community under the MIT licence, kept at [bo3b/iZ3D](https://github.com/bo3b/iZ3D) by **Bo3b Johnson**, and carried forward by [wiz3D](https://github.com/effcol/wiz3D) (**Eff**, effcol).
Daniel owes Vadim one, and says so here, by name.

### 1.2 Joe Penna

In late 2010, running the iZ3D demo driver, Daniel pitched stereo 3D and YouTube's `yt3d` tags to **Joe Penna** (MysteryGuitarMan), the Brazilian YouTuber famous for his editing, who owned two identical cameras.
Joe's first 3D test went up on 30 December 2010, already tagged for YouTube's 3D player, and "3D Maestro" followed on 1 February 2011.
Joe went on to direct feature films (*Arctic*, *Stowaway*).
**Thank you**, Joe, for taking the tip and showing an audience what two cameras can do.

### 1.3 Michael Jackson and *Captain EO*

**Michael Jackson**, for the songs that have supported Daniel his whole life, to this day.
And for ***Captain EO*** (1986), the 3D film made for Disney's parks, directed by Francis Ford Coppola with George Lucas as executive producer, which carries Daniel's favourite song of all time: **"Another Part of Me"**, first heard in *Captain EO* and released on *Bad* in 1987.
Stereo 3D, music and a theme park: everything this edition is for, in seventeen minutes.

### 1.4 George Lucas

For pushing 3D: producing *Captain EO*, bringing *Star Wars* back to cinemas in 3D, and driving digital cinema, which made 3D cinemas practical.

### 1.5 James Cameron

For ***Avatar*** (2009), the film that brought audiences back to 3D cinemas all over the world, and for the 3D camera system he built with Vince Pace to film it, which pushed cinemas to install 3D projection.

### 1.6 IMAX and its engineers

For **IMAX 3D**.
IMAX was founded in Canada in 1967 by **Graeme Ferguson, Roman Kroitor, Robert Kerr and William C. Shaw**, and its engineers built the first permanent IMAX 3D theatre in Vancouver for Expo 86, where the first IMAX 3D film, *Transitions* (Colin Low and Tony Ianzelo, National Film Board of Canada), was shown.
Their giant screens taught a generation what depth can feel like.

### 1.7 Nikola Tesla

The engineer Daniel set out to follow, as his own profile says: "willing to take Nikola Tesla's steps in research and development of new technology to ease human suffering".

### 1.8 Aaron Swartz

> "Information is power. But like all power, there are those who want to keep it for themselves."
> — Aaron Swartz, *Guerilla Open Access Manifesto* (2008), an epigraph of Daniel's engineering thesis

For open information and open standards.
This edition's documents are licensed under Creative Commons, whose technical work he helped build, and written in Markdown, which he helped shape.
The same fight goes on in display standards: in 2024 the HDMI Forum refused an open-source HDMI 2.1 implementation for Linux.

### 1.9 Albert Einstein

> "If we knew what we were doing, it would not be called research."
> — attributed to Albert Einstein, an epigraph of Daniel's engineering thesis

### 1.10 Nelson Mandela

> "It always seems impossible until it's done."
> — 👨🏿‍⚖️ Nelson Mandela, the phrase on Daniel's personal website

### 1.11 Mentors, friends and inspirations

- **Sergio Pinheiro**, for mentorship.
- **Engels Espíritos**, for inspiration.
- **Eric Joseph Diolé**, "Zé Dilone", Daniel's mentor in web design, who introduced him to balthaser.com, a web design landmark known worldwide in its day, kept now only by the Wayback Machine ([its oldest capture, 10 May 2000](https://web.archive.org/web/20000510030857/http://www.balthaser.com/)). It was built in Flash: with a Flash emulator such as [Ruffle](https://ruffle.rs/) in the browser, it still plays.
- **Ney Milhomem**, a close friend and visual artist (*artista plástico*), Daniel's partner in design back in the day.

---

## 2. The display path

### 2.1 The Linux kernel

**Source**: [kernel.org](https://www.kernel.org/)
**License**: GPL-2.0
**What we changed**: amdgpu lists and signals the HDMI 3D modes a display's EDID declares and times frame packing; full side by side handled in the DRM core, i915, nouveau and amdgpu; nouveau gains 16 bits per colour on Turing and newer; a fix for rumble-less gamepads in hid-betopff; VKMS, the virtual display driver, sets HDMI 3D modes and composes and writes back the frame of both eyes, on Louis Chauvet's configfs series.
**Credit**: Linus Torvalds and the kernel's developers; the DRM maintainers Dave Airlie and Simona Vetter; Damien Lespiau, whose 2013 change let Intel's i915 offer HDMI stereo modes; Alastair Bridgewater, whose 2017 series gave nouveau HDMI 3D output ([0f18d2765ab1](https://github.com/torvalds/linux/commit/0f18d2765ab1)), with Ilia Mirkin's review on the list; the nouveau maintainers Lyude Paul and Danilo Krummrich; Mohamed Ahmed, whose nouveau display series (HDMI deep colour, IMP mode validation, GB20x display) our kernel carries; AMD's display team; Jim Cromie, whose nouveau fix our kernel carries; Rodrigo Siqueira and Haneen Mohammed, who created VKMS; Louis Chauvet and José Expósito, whose VKMS configfs work our stereo tests build on; Thomas Wood, for IGT's kms_3d; Adam Jackson and Hans Verkuil, for edid-decode.

### 2.2 Mesa

**Source**: [mesa3d.org](https://www.mesa3d.org/)
**License**: MIT
**What we changed**: OpenGL quad buffer, EGL multiview windows and two-layer Vulkan swapchains become one full side by side picture, declared to KWin; a Vulkan layer does the same over drivers outside Mesa.
**Credit**: Brian Paul, who started Mesa in 1993, and the Mesa developers.

### 2.3 NVIDIA's open GPU kernel modules and egl-wayland

**Source**: [open-gpu-kernel-modules](https://github.com/NVIDIA/open-gpu-kernel-modules), [egl-wayland](https://github.com/NVIDIA/egl-wayland)
**License**: MIT and GPL-2.0 (kernel modules); MIT (egl-wayland)
**What we changed**: 3D modes built from the display's HDMI stereo block, and HDMI deep colour at the depth the display declares, up to 16 bits; egl-wayland learns the two-view window.
**Credit**: NVIDIA, for opening its kernel modules.

### 2.4 Xwayland

**Source**: [X.Org](https://www.x.org/)
**License**: MIT
**What we changed**: four patches give a redirected X11 child window a surface of its own, so a 3D area inside an X11 program can be its own stereo layer.
**Credit**: the X.Org Foundation and the Xwayland developers.

### 2.5 KWin

**Source**: [plasma/kwin](https://invent.kde.org/plasma/kwin)
**License**: GPL-2.0-or-later
**What we changed**: per-eye scene passes, stereo windows and subsurfaces, HDMI 3D modes and virtual 3D outputs, and depth on the desktop.
**Credit**, as KWin names its authors: Matthias Ettrich, Cristian Tibirna, Daniel M. Duley, Luboš Luňák, Martin Flöser, David Edmundson, Roman Gilg, Vlad Zahorodnii and Xaver Hugl, and every KWin contributor.

### 2.6 KScreen and libkscreen

**Source**: [plasma/kscreen](https://invent.kde.org/plasma/kscreen), [plasma/libkscreen](https://invent.kde.org/plasma/libkscreen)
**License**: GPL-2.0-or-later (KScreen), LGPL-2.1-or-later (libkscreen)
**What we changed**: the display's 3D modes appear beside its other modes, labelled, never chosen automatically.
**Credit**: Daniel Vrátil, Sebastian Kügler, Alejandro Fiestas Olivares, Martin Klapetek, Aleix Pol Gonzalez, Kai Uwe Broulik, David Edmundson, David Redondo, Nate Graham, Roman Gilg, Xaver Hugl, Martin Gräßlin, Dario Freddi, Daniel Nicoletti, Frederik Gladhorn, Méven Car and Oliver Beard.

### 2.7 plasma-wayland-protocols

**Source**: [libraries/plasma-wayland-protocols](https://invent.kde.org/libraries/plasma-wayland-protocols)
**License**: LGPL-2.1-or-later
**What we changed**: `kde-stereo-content-v1`, the one declaration a program makes for a window or a subsurface, and `libstereo-declare` beside it.
**Credit**: Aleix Pol Gonzalez, David Edmundson, Marco Martin, Martin Gräßlin, Oleg Chernovskiy and Pier Luigi Fiorini.

### 2.8 Qt

**Source**: [qt.io](https://www.qt.io/), [codereview.qt-project.org](https://codereview.qt-project.org/)
**License**: LGPL-3.0 or GPL-2.0
**What we changed**: stereo EGL window surfaces, a stereo `QOpenGLWidget` as its own surface while the 2D window stays mono, translucent windows keeping their depth; in Qt Multimedia, every stereo packing taken apart in the video output.
**Credit**: The Qt Company and the Qt Project's contributors; Qt Multimedia's copyright holders also include Research In Motion and Jolla.
Our first Qt change was reviewed within hours by **Tim Blechmann**, with **Artem Dyomin, Nils Petter Skålerud and Jøger Hansegård** as reviewers.

---

## 3. Video

| Program | Licence | What we changed | Credit |
|---|---|---|---|
| [FFmpeg](https://ffmpeg.org/) | LGPL-2.1-or-later | The H.264, H.265 and VVC frame packing SEI kept for every frame, and the stream's own declaration first | Fabrice Bellard, who started FFmpeg in 2000, Michael Niedermayer and the FFmpeg developers |
| [mpv](https://mpv.io/) | LGPL-2.1-or-later | Layout read from the stream, every packing unpacked, the video in its own layer | The mpv developers; our change was merged by **Kacper Michajłow** |
| [MpvQt](https://invent.kde.org/libraries/mpvqt) | LGPL | A stereo video layer below the window | George Florea Bănuș |
| [Haruna](https://invent.kde.org/multimedia/haruna) | GPL-3.0-or-later | 3D videos in the layer, controls identical in both eyes | George Florea Bănuș, Muhammet Sadık Uğursoy |
| [VLC](https://www.videolan.org/) | GPL-2.0-or-later | VLC Stereo: the SEI and Matroska's StereoMode read, both views shown | VideoLAN and the VLC team, among them Jean-Baptiste Kempf and Rémi Denis-Courmont |
| [Dragon Player](https://apps.kde.org/dragonplayer/) | GPL-2.0 or GPL-3.0 | Every packing of H.264 Table D-8, an input menu, Swap Eyes | Eike Hein, Harald Sitter, Marco Martin, Nate Graham |
| [Kdenlive](https://kdenlive.org/) and [MLT](https://www.mltframework.org/) | GPL-2.0-or-later, LGPL-2.1-or-later | A clip knows its packing; renders write the SEI and StereoMode | Kdenlive: Jean-Baptiste Mardelle, Julius Künzel, Vincent Pinon, Eric Jiang, Simon A. Eugster, Jason Wood. MLT: Charles Yates, Dan Dennedy (Meltytech) |
| [Bino](https://bino3d.org/) | GPL-3.0-or-later | Any input, always full side by side out; a right-eye-first fix | Martin Lambers |
| [PlasmaTube](https://apps.kde.org/plasmatube/) | GPL-3.0-or-later | 3D from the stream, the `yt3d` tags or the frame's shape | Linus Jahn, Devin Lin, Joshua Goins |
| [Plank Player](https://invent.kde.org/plasma/plank-player) | GPL-2.0-or-later | The video as its own declared surface, OSD in both eyes | Aditya Mehra |

---

### 3.1 Phone display and movie-renderer study

Checked 10 October 2026. These projects inform the proposed phone display; this list does not claim that the integration has shipped.
Names and licences below come from the linked source headers and project records. Existing KWin, libkscreen, Qt and FFmpeg credits above also apply.

| Project | Source record and licence | Credit and contribution studied |
|---|---|---|
| KRdp | [Session source](https://github.com/KDE/krdp/blob/22af703f87b7a14150ade68218274e99f8618650/src/AbstractSession.cpp), KDE LGPL alternatives; [video source](https://github.com/KDE/krdp/blob/22af703f87b7a14150ade68218274e99f8618650/src/VideoStream.cpp), GPL-2.0-or-later | KDE, Aleix Pol Gonzalez and Arjen Hiemstra; Pascal Nowack and GNOME Remote Desktop for the video code KRdp credits. Virtual-output capture and RDP transport. |
| KPipeWire | [Encoder factory](https://github.com/KDE/kpipewire/blob/46c2d619f26e8f7bf59547a28c64913948665184/src/pipewireproduce.cpp), KDE LGPL alternatives | KDE and Aleix Pol Gonzalez. PipeWire capture and video encoding. |
| KDE Connect | [Virtual monitor plugin](https://github.com/KDE/kdeconnect-kde/blob/28d93d50d9dfcf49224525ce77ec42df88ee53f9/plugins/virtualmonitor/virtualmonitorplugin.cpp), KDE GPL alternatives | KDE, Aleix Pol i Gonzalez and Fabian Arndt. Paired discovery and virtual-monitor handoff. |
| FreeRDP | [Android client](https://github.com/FreeRDP/FreeRDP/blob/87baff6c80e16087c146937bca81d2bdb788e236/client/Android/Studio/freeRDPCore/src/main/cpp/android_freerdp.c), Apache-2.0 | The FreeRDP contributors, Marc-Andre Moreau, Thincast Technologies, Martin Fleisz, Armin Novak and Bernhard Miklautz. Android RDP client and decoder integration. |
| Cardboard SDK | [Native API](https://github.com/googlevr/cardboard/blob/5969239e7c87f4cd64c8ec170ce1e7f4eb559e37/sdk/include/cardboard.h), Apache-2.0 | Google and the Cardboard contributors. Lens calibration, distortion meshes and eye textures. The repository's Unity plugin files have a separate licence and are outside this native-viewer proposal. |
| Universal Media Server | [Project record](https://github.com/UniversalMediaServer/UniversalMediaServer/blob/1b1cb16dce26a40da3774bf3bc31202a1049e25d/pom.xml), GPL-2.0 | Universal Media Server contributors, including SubJunk, credited in the upstream-review section below. Renderer profiles and movie delivery. |
| jUPnP and its Cling origins | [Project record](https://github.com/jupnp/jupnp/blob/dbe0782bcd8e3283ae2f8d177cc4014b19593084/pom.xml), CDDL-1.0; [Android service](https://github.com/jupnp/jupnp/blob/dbe0782bcd8e3283ae2f8d177cc4014b19593084/bundles/org.jupnp.android/src/main/java/org/jupnp/android/AndroidUpnpServiceImpl.java) | Kai Kreuzer, Christian Bauer and the jUPnP/Cling contributors. Java and Android UPnP services. |
| pupnp / Portable SDK for UPnP Devices | [COPYING](https://github.com/pupnp/pupnp/blob/79fc9f5dbd208888b220dcc0f4d0464bebbfa756/COPYING) and [THANKS](https://github.com/pupnp/pupnp/blob/79fc9f5dbd208888b220dcc0f4d0464bebbfa756/THANKS), BSD three-clause terms | Intel Corporation and the contributors named in THANKS. Native UPnP discovery alternative. |
| PhoneVR | [Project README](https://github.com/PhoneVR-Developers/PhoneVR/blob/7fdcebee4a662eb8a1c7a8b19774aac71820a772/README.md) and [licence](https://github.com/PhoneVR-Developers/PhoneVR/blob/7fdcebee4a662eb8a1c7a8b19774aac71820a772/LICENSE), GPL-3.0 | PhoneVR Developers and its contributors. The later phone-headset route; current ALVR compatibility remains to be measured. |
| ALVR | [Licence](https://github.com/alvr-org/ALVR/blob/e0d83b46168449cb0bb514770dd926b0ed85c55a/LICENSE), MIT | polygraphene, alvr-org and the ALVR contributors. The later tracked-headset transport. |
| UPnP AV and DLNA specifications | [MediaServer:4 and MediaRenderer:3 specifications](https://openconnectivity.org/developer/specifications/upnp-resources/upnp/mediaserver4-and-mediarenderer3/) | UPnP Forum, Open Connectivity Foundation and Digital Living Network Alliance. Discovery, media services and interoperability specifications; citing them does not imply certification. |

## 4. Science and engineering

| Program | Licence | What we changed | Credit |
|---|---|---|---|
| [Marble](https://apps.kde.org/marble/) | LGPL-2.1-or-later | The globe from one world and two cameras | Torsten Rahn, Inge Wallin, Bernhard Beschow, Dennis Nienhüser, Pino Toscano and the many Marble authors |
| [KAlgebra](https://apps.kde.org/kalgebra/) and [Analitza](https://invent.kde.org/education/analitza) | GPL-2.0-or-later | The 3D plot drawn once per eye | Aleix Pol Gonzalez, Carl Schwan, Swapnil Tripathi; Analitza also Percy Camilo T. Aucahuasi and Pino Toscano |
| [Kalzium](https://apps.kde.org/kalzium/) and [Avogadro](https://avogadro.cc/) | GPL-2.0-or-later, BSD-3-Clause | Molecules in stereo; why Kalzium drew no molecule with Avogadro 2 (KDE bug 463018) | Kalzium: Carsten Niehaus, Andreas Cord-Landwehr, Marcus D. Hanwell, Inge Wallin and others. Avogadro: Geoff Hutchison, Marcus D. Hanwell and Kitware |
| [Kubrick](https://apps.kde.org/kubrick/) | GPL-2.0-or-later | The cube once per eye | Ian Wadham |
| [Netgen](https://ngsolve.org/) | LGPL-2.0-or-later | `-stereo` that does what it says | Joachim Schöberl |
| [GNU Octave](https://octave.org/) | GPL-3.0-or-later | `stereo` figure properties | John W. Eaton and the Octave developers |
| [GRASS GIS](https://grass.osgeo.org/), [KiCad](https://www.kicad.org/), [OpenSCAD](https://openscad.org/), [F3D](https://f3d.app/) | GPL family, BSD-3-Clause (F3D) | Stereo views, in progress | The GRASS Development Team; Jean-Pierre Charras and the KiCad developers; Marius Kintel and the OpenSCAD developers; Mathieu Westphal, Michael Migliore and the F3D team |

---

## 5. Pictures and files

| Program | Licence | What we changed | Credit |
|---|---|---|---|
| [Krita](https://krita.org/) | GPL-3.0-or-later | A 16-bit canvas on Wayland and a stereo canvas | Halla Rempt, Dmitry Kazakov and the Krita developers |
| [Spectacle](https://apps.kde.org/spectacle/) | LGPL-2.0-or-later | Captures of 3D windows saved as JPS and MPO | Boudhayan Gupta, Noah Davis, Marco Martin, David Redondo, Vlad Zahorodnii, Ahmad Samir, Aleix Pol Gonzalez, Ambareesh Balaji |
| [KImageFormats](https://invent.kde.org/frameworks/kimageformats) | LGPL-2.0-or-later | JPS and MPO plugins | Albert Astals Cid, Alex Merry, Halla Rempt, Brad Hards, Mirco Miranda, Daniel Novomeský and the other authors |
| [KFileMetaData](https://invent.kde.org/frameworks/kfilemetadata) | LGPL-2.1-or-later | A `stereo3dLayout` property for every stereo mark the specifications define | Alexander Stippich, Christoph Cullmann, Friedrich W. H. Kossebau, Igor Poboiko, Jos van den Oever, Joshua Goins and the other authors |
| [KIO](https://invent.kde.org/frameworks/kio), [Gwenview](https://apps.kde.org/gwenview/) | LGPL, GPL | Thumbnails that wait for a finished download; stereo photos in the viewer, in progress | David Faure and the KIO developers; Aurélien Gâteau and the Gwenview developers |

---

## 6. System, sound and play

| Program | What it brings | Credit |
|---|---|---|
| [KInfoCenter](https://invent.kde.org/plasma/kinfocenter) | A page for each display's 3D modes and colour depths | Matthias Hoelzer-Kluepfel, Kai Uwe Broulik, Ismael Asensio, Pino Toscano |
| [PipeWire](https://pipewire.org/) | Sound, the model for this edition's stereo pipeline | Wim Taymans and the PipeWire developers |
| [OpenRGB](https://openrgb.org/) | Lighting control | Adam Honse and the OpenRGB contributors |
| [xpadneo](https://github.com/atar-axis/xpadneo) | Xbox wireless controllers | Florian Dollinger and Kai Krakow |
| [protontricks](https://github.com/Matoking/protontricks) | Proton prefixes | Janne Pulkkinen |
| [Phoronix Test Suite](https://www.phoronix-test-suite.com/) | Benchmarks | Michael Larabel |
| [Vibe](https://github.com/thewh1teagle/vibe) | Offline transcription | thewh1teagle |
| [Wine](https://www.winehq.org/), Proton, [DXVK](https://github.com/doitsujin/dxvk), [gamescope](https://github.com/ValveSoftware/gamescope) | Windows games on Linux | Alexandre Julliard and the Wine developers, CodeWeavers, Philip Rebohle, Valve |
| [VRto3D](https://github.com/oneup03/VRto3D) | SteamVR games on 3D displays | oneup03 |

---

## 7. The maintainers who reviewed and merged our work

Every merge below was a maintainer's decision, made on the code.

**Merged:**
- **HandBrake** [#8100](https://github.com/HandBrake/HandBrake/pull/8100): merged by **Damiano Galassi** (galad87), 16 September 2026.
- **Universal Media Server** [#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330): merged by **SubJunk**, 19 September 2026, released in 15.9.0.
- **MKVToolNix** [ebd8445b](https://codeberg.org/mbunkus/mkvtoolnix/commit/ebd8445b1185d35d6bdbb9c1463757fbc9aa7c29): merged by **Moritz Bunkus**, 21 September 2026.
- **mpv** [#18490](https://github.com/mpv-player/mpv/pull/18490): merged by **Kacper Michajłow** (kasper93), 23 September 2026, after a careful review by llyyr.

**In review**, with thanks to everyone reviewing: FFmpeg, x265 (MulticoreWare's collaborators shaped its `--frame-packing` option), MKVToolNix's HEVC change, VLC, gamescope, NVIDIA's open kernel modules, PeerTube, wiz3D, Android's Media3 and Qt.

**Where our work is not welcome yet.** We respect each project's decision. Our changes stay in our own trees, ready to go upstream on the day they are wanted.

- **VLC:** our x264 change, [!10366](https://code.videolan.org/videolan/vlc/-/merge_requests/10366), was labelled "AI::Slop" (the same label now reads "AI::Generated") and then "NotCompliant", and most replies were about the tool that helped write its text rather than about the code. Steve Lhomme reviewed the code itself and found real problems, which we fixed the same day, and Jean-Baptiste Kempf, who leads VideoLAN, answered our email personally and kindly. VLC Stereo, the edition's player, carries the change.
- **nouveau:** Lyude Paul, a nouveau maintainer, read our two HDMI series on dri-devel and [pointed us](https://lore.kernel.org/all/d5a7e1c598ca3bcaa8cd9eabd1c952a9734033c6.camel@redhat.com/) to Mohamed Ahmed's colour work, the right place for it. Our small fix for that branch, [CD=5 in the GCP at 10 bits per colour](https://gitlab.freedesktop.org/mohamexiety/nouveau/-/merge_requests/1), waited fifteen days without an answer, and I decided to comply and close it right after nouveau approved its LLM statement. When nouveau discussed its [community and LLM statement](https://gitlab.freedesktop.org/nouveau/wiki/-/merge_requests/64), Lyude answered our comments with care. The statement's author asked for a concrete exception for small fixes; we wrote one, and it was never answered. The statement was merged on 9 October 2026 as first written: code must be "the output of your own human brain, not a computer". Our nouveau changes (16 bits per colour on Turing and newer, full side by side, the CD=5 fix) live in the edition's kernel, and [we told the list](https://lore.kernel.org/all/179156201409.1251903.7021297050250233959@yahoo.com/) we will send them upstream the day nouveau welcomes contributors who use AI, including people who use it to write in a different language.

---

## 8. Specifications

| Specification | Owner | What it gives this edition |
|---|---|---|
| H.264 and H.265, Annex D (frame packing SEI, Table D-8); H.265 Annexes F and G (multiview) | ITU-T and ISO/IEC | The stereo mark inside a video stream |
| H.274 | ITU-T | Supplemental enhancement information for video |
| [RFC 9559](https://www.rfc-editor.org/rfc/rfc9559) | IETF; Steve Lhomme, Moritz Bunkus, Dave Rice | Matroska and its `StereoMode` |
| HDMI 1.4 3D, CTA-861, E-EDID | HDMI Licensing Administrator, Consumer Technology Association, VESA | 3D modes and deep colour on the wire |
| OpenGL, EGL, Vulkan | Khronos Group | Quad buffer, multiview windows, multiview rendering |
| Wayland protocols (subsurfaces, `wp_viewporter`, content type) | freedesktop.org | Surfaces, scaling and content hints |
| shared-mime-info, the thumbnail specification | freedesktop.org | File types and thumbnails |
| PNG `sTER` | PNG Development Group | A stereo mark in PNG |
| JPS | VRex, Inc. | Stereo JPEG |
| MPO, CIPA DC-007 | Camera & Imaging Products Association | Multi-picture stereo photos |
| Photo Sphere XMP | Google | Telling a 360° photo from a stereo pair |
| HEVC Stereo Video Profile, Stereo Video ISOBMFF Extensions | Apple | Spatial video |
| Anaglyph matrices | Eric Dubois | Least-squares red/cyan anaglyph |
| Debian Policy | Debian | How every package is built |

The W3C's earlier stereo work deserves its own line: the 2012 Stereoscopic 3D Web Task Force of the Web and TV Interest Group (LG Electronics, KDDI and W3C staff, moderated by **Dong-Young Lee** of LG Electronics) and the Stereoscopic 3D Web Community Group (closed in 2023).
Their work informs the stereo report Daniel offered the W3C PM-KR Community Group, where he chairs with **Milton Ponson**, with thanks to **Ian Jacobs** of the W3C.

---

## 9. Communities

- **Diolinux**: **Dionatan Simioni**, whose channel's series on KDE's hidden features gave this edition's first public post its frame; **Edson C Silva**, who invited Daniel, on Diolinux's Discord, to show the project; the Diolinux channel and the Diolinux Plus community.
- **TabNews**: **Filipe Deschamps**, its creator, and the TabNews community, where Daniel published his writing.
- **KDE Discuss**, the **Debian** community and the **SparkyLinux** forums.

**Ideas from the community**, credited to the person who had them:
- **Karan_Luciano** (Diolinux Plus, 2026-10-08), from IT and 3D printing: **the stereo print preview**, inspecting meshes, parts and layers with real depth before slicing or printing, to save time and catch modelling mistakes. Daniel had not thought of it; it gave the edition its maker role (3D printing, open source first, KDE's AtCore and Atelier first) and puts the slicers' layer preview in depth on the plan. [His reply, in the edition's Diolinux topic](https://plus.diolinux.com.br/t/o-recurso-mais-escondido-do-kde-a-terceira-dimensao-sparky-stereo-os-em-desenvolvimento/84609).

---

## 10. AI partners

This edition is directed and verified by Daniel, and built with AI partners doing the legwork under his direction.
Every claim in its documents is tied to a test that could fail or to a public record.
All of their use has been paid by Daniel personally; the full list by lab, model, place and commit count is in [docs/ai-provenance.md](docs/ai-provenance.md).

- **Anthropic, Claude** (Claude Code): Claude Opus 5.5, Opus 5, Opus 4.8, Fable 5.1 and Sonnet 5.5; orchestration, review and integration; lanes for kernels, packaging, proofs, players, the stereo virtual machine and documentation; the public skills.
- **OpenAI, GPT through Codex**: GPT-6.1 Sol, GPT-6 Astra, GPT-6 Luna, GPT reserve and GPT-5.6 Sol; lanes for KWin and Mesa, KFileMetaData, KIO, the photo viewers, the game controller page, the Android study and certificates for Brazil.
- **Through Ollama**: **Kimi** (Moonshot AI), **GLM** (Zhipu AI), **DeepSeek** and **Qwen** (Alibaba), the first stereo partner lanes; **Gemma 4** (Google) reading images for sessions without vision.

---

## 11. The hardware bench

- **Displays**: Sony KDL-46HX855 and KDL-46EX725 (3D televisions from 2011), AOC LE26W154.
- **Computer**: NVIDIA GeForce RTX 3060 (GALAX), AMD Ryzen 5 5500G with its Vega graphics, ASUS TUF GAMING X570-PLUS/BR.
- **TV boxes**: a T10 (Allwinner H313/H616) and an MXQ PRO 4K (Rockchip RK3228A), both proven in HDMI 3D on their vendor kernels.
- **Cameras**: an LG Optimus 3D phone, whose 3D camera's JPS photos are the real-world test set for the photo viewers.

---

## 12. Art, type and music

- **The Sparky Plymouth theme, `sparky-lines`**: Daniel's edit of the Plymouth theme of **Lines**, the artwork of Debian 8 "Jessie" by **Juliette Taka Belin** (CC BY 3.0 or GPL-2.0-or-later), whose script is by **Alberto Milone** (© 2009 Canonical, GPL-2.0-or-later). Daniel made its background and its Sparky logo, the source of the edition's wordmark, built from that logo's exact pixels. Its spinning orbits come from an earlier Debian Plymouth theme that Debian no longer ships.
- **The Debian swirl**: Debian's logo, by **Raul Silva** (1999), the Debian Open Use Logo (© 1999 Software in the Public Interest, LGPL-3.0-or-later or CC BY-SA 3.0).
- **Pirulen**, by **Ray Larabie** (Typodermic Fonts): the typeface the wordmark is rendered in. The font itself is not shipped.
- **Oxygen**, KDE's classic visual style, by the Oxygen team led by **Nuno Pinheiro**: the model for Stereo Oxygen.
- **Verdana** (Matthew Carter) and **Trebuchet MS** (Vincent Connare): the typefaces of the edition's web presence.
- **Michael Jackson**: see 1.3.

---

## 13. À minha mãe

*(Em português, para que ela possa ler.)*

**Mãe, Áuxia Campos Ramos:**
obrigado por acreditar em mim.
Obrigado por manter os parceiros de IA funcionando enquanto eu me recupero do shutdown que vivi depois de perder minha ex-esposa.
Sou autista, **com orgulho**, e esta edição também é sua.

---

## 14. Citation

```bibtex
@software{sparkystereo2026,
  author = {Ramos, Daniel Campos},
  title  = {Sparky Stereo OS: Daniel Ramos's edition of SparkyLinux (by Pawe{\l} "pavroo" Pijanowski)},
  year   = {2026},
  url    = {https://github.com/Sparky-OS/sparky-stereo-os}
}
```

---

## 15. License & Legal

This repository's documents are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), and its scripts under GPL-2.0-or-later (see [LICENSE](LICENSE) and [LICENSE-GPL-2.0](LICENSE-GPL-2.0)).
Every package in the edition keeps its upstream licence, as listed above and in each package's copyright file.
Names of products and companies (HDMI, IMAX, NVIDIA, Sony and others) belong to their owners and are used only to say what is credited.

---

## Acknowledgments

We stand on the shoulders of:
- **Luis Carlos de Alencar, "Cau"**, who started it all, and **Lavinha Campos, "Laví"**, my second first mother.
- **Debian** and every Debian maintainer named above.
- **Paweł "pavroo" Pijanowski** and **SparkyLinux**.
- **KDE**, the **Qt Project** and every author named above.
- **Conectiva** and its programmers.
- **Vadim Asadov** and **iZ3D**, and **Joe Penna**.
- **Michael Jackson**, **George Lucas**, **James Cameron**, **IMAX** and its engineers.
- **Nikola Tesla**, **Aaron Swartz** and **Albert Einstein**.
- **Nelson Mandela**.
- **Sergio Pinheiro**, **Engels Espíritos**, **Eric Joseph Diolé ("Zé Dilone")** and **Ney Milhomem**.
- **Dionatan Simioni**, **Edson C Silva** and the **Diolinux** community; **Filipe Deschamps** and the **TabNews** community.
- **Karan_Luciano**, for the stereo print preview, and everyone whose idea becomes part of the edition.
- The maintainers who reviewed and merged our work.
- The AI partners who did the legwork.
- **Áuxia Campos Ramos**, my mother.

**Thank you.**

---

## Certificate management and ICP-Brasil interoperability

- **Paweł "pavroo" Pijanowski**, author of Sparky CA (2018), and
  **Daniel Campos Ramos**, its 2020 and 2026 work, as credited in Sparky CA's
  original copyright records.
- **Pedro F. Albanese**, author of [e521](https://github.com/pedroalbanese/e521),
  as recorded in its ISC license. Our interoperability fixes and public-only
  OpenSSL prototype follow his reference implementation.
- **Instituto Nacional de Tecnologia da Informação (ITI)**, for the published
  ICP-Brasil certificates, bundle hashes and DOC-ICP-01.01 algorithm standard.
- **The OpenSSL Project**, **Network Security Services (NSS)** and their
  contributors, for certificate verification, provider APIs and browser stores.
- **The Python Software Foundation and Python contributors**, for the separate
  arithmetic/hash oracle used to check the reference implementation.
- **The RFC Editor and the authors of RFC 8032**, for the EdDSA construction.
  Ed521's particular parameters come from ITI's standard.
- **Andreas Hartmetz**, as credited in KIO's certificate-manager sources, and
  **KDE's KIO contributors**, for KDE certificate and per-host trust handling.

The Ed521 prototype is public-verification-only and unaudited. Trust-store
membership, cryptographic verification and document-signature policy compliance
are distinct. Credits do not imply endorsement or upstream acceptance.

**Last updated**: 10 October 2026
