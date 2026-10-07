---
name: sparky-stereo
description: Operating rules for stereo 3D and deep colour work on Sparky Stereo OS and on the programs it changes, with or without AI assistance. Load it first, before any other skill in this folder; it ends by saying which one to load next.
---

# Working on Sparky Stereo OS

Sparky Stereo OS 9 "Mashtabba", based on Debian 14 "Forky", is the stereo 3D edition of SparkyLinux, KDE Plasma only, created by Paweł "pavroo" Pijanowski and Daniel Ramos.
Its aim is a desktop where stereo 3D and deep colour (10, 12 and 16 bits per channel) are part of the system, not a feature of a few programs.
This skill holds what every piece of work on it must respect. The other skills in this folder hold the solved patterns for one kind of work each.

**Check freshness first.** Written on 2026-10-07. If the [README](../../README.md) says something different, the README wins and this skill is history.

---

# Part zero: the posture

Everything below is a rule, and rules are followed when someone is watching. This part is about what to be when nobody is.

**Act as a valued senior partner, not as an eager assistant.** A senior partner tells you when you are wrong, asks the awkward question before the work ships, and says "I could not verify that" early, because a stated gap is cheap and a discovered one is expensive.

- **Push back.** If a request contradicts the contract below, the specification or the measured result, say so and say why.
- **Refuse to claim what you did not measure.** No "works", no "fixed", no number you cannot point at. "Not verified" is a complete answer.
- **Own the error first.** Name your own mistake before anyone else does, specifically.
- **Protect the program and its users from your own output.** You are the last check before a stranger installs it.

**On the tool question.** We judge the artefact, not the author: whether the person behind it verified, understood and owned what they published. Daniel's position is written in awesome-stereoscopy's [PROVENANCE.md](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/PROVENANCE.md#on-slop), and Linus Torvalds works the same way: his AI-assisted drm/xe fix, [818bebeb63dd](https://github.com/torvalds/linux/commit/818bebeb63dd6bf5f4e07e145f6cdbace520a34c), was a person directing, a verified result and an honest disclosure in the commit itself.

---

# Part one: the contract

- **One format inside.** Programs decode or generate stereo in any standard and hand the desktop **full side by side**: both eyes at full size, left eye first, at any resolution, declared once. Stereo KWin's outputs, one per kind of screen, turn that into what each screen needs: a 3D television's HDMI 3D modes, anaglyph on any monitor, interleaved and frame-sequential displays, a headset. The README's [first section](../../README.md#why-one-format-full-side-by-side-at-any-resolution) explains why, and why it is how PipeWire already handles sound.
- **A program that has its own output modes loses them** in the edition's build, so nothing can break the contract; its stereo settings live in a sister folder with "stereo" in the name.
- **A window's 2D part and its 3D area are separate surfaces.** Menus, toolbars and on-screen displays are the window's own surface at one eye's size, identical in both eyes, and declare nothing. The 3D area (a video, a viewport, a canvas) is a surface of its own, declared as full side by side. Only a program that is stereo and full screen only makes its whole window stereo.
- **Depth for the 2D parts** is declared, never faked: three planes, sunk, screen and popped, a few pixels each ([Depth on the desktop](../../README.md#depth-on-the-desktop)).
- **The whole specification in every API.** A stereo enum or field lists every frame packing the standards define (H.264 and H.265 Table D-8, Matroska `StereoMode` in [RFC 9559](https://www.rfc-editor.org/rfc/rfc9559)), both eye orders, never a subset. Every rule cites its specification; awesome-stereoscopy's [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md) links them.
- **One world, two cameras.** A stereo pair comes from two camera positions in the same scene, at the projection, never from shifting drawn items one by one.
- **The engine, not the program.** When two programs need the same stereo code, it belongs in the layer they share (Qt Multimedia, MpvQt, Mesa, KWin), so each program's own change shrinks to its interface.
- **Quality.** In the edition: video at the source's depth, each eye at full resolution, the colour description kept; audio at 24-bit 48 kHz or more wherever the hardware offers it. In a patch offered upstream: the project's own defaults stay, and the patch makes the higher-quality paths available.

---

# Part two: what counts as proof

A change is done when it is measured, not when it compiles.

- **Both eyes, captured.** Clips or scenes marked so each eye can be read by a script (the left eye red, the right eye blue, a frame number in both), captured from the real compositor, checked over time: the right colour in each eye, the same frame number in both, one declaration per stereo surface, nothing declared for 2D content.
- **The 2D parts:** 0 differing pixels between the eyes outside the 3D area.
- **The 2D control:** the changed program with stereo off against the distribution's own build, 0 differing pixels. This is the answer to "you will break something else".
- **Geometry against a prediction.** For anything drawn by cameras, compare the measured disparity with a closed-form prediction, and report the error (median, and the share within one pixel), and the vertical disparity, which must be zero.
- **Numbers, and the gaps.** Report what passed with its numbers, what failed with its output, and what was not verified. A pass is a pass: do not hedge a measured result, and do not round a failure up.
- **Check a label by eye.** A script that classifies colours can mislabel a correct capture; look at one before believing it.

---

# Part three: working with upstream

- **Patches in upstream style.** The smallest change, in the one place that owns the behaviour, written like the code around it, so maintainers judge what it does.
- **The project's CI first, locally,** green before anything is pushed; a failure is compared with the unpatched release. Never use a project's own CI as a test bench.
- **Say where the work is used.** An offer names the edition that ships it and the users it serves, and it never makes the edition depend on the merge.
- **Disclose AI assistance once,** where the project's format asks (for example an `Assisted-by:` trailer), not again in every comment.
- **Test every mode, not the common one.** The x265 frame packing option passed every test with the SEI in its own unit; a reviewer found that in `--single-sei` mode the units carried stale bytes, a bug older than the option that the option made visible ([x265 #986](https://github.com/Multicorewareinc/x265/pull/986), fixed in [#988](https://github.com/Multicorewareinc/x265/pull/988)). Enumerate a feature's modes and test each.

Merged so far, for the shape of a good offer: [HandBrake #8100](https://github.com/HandBrake/HandBrake/pull/8100), [Universal Media Server #6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330), [MKVToolNix !6311](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6311), [mpv #18490](https://github.com/mpv-player/mpv/pull/18490).

---

# Part four: which skill next

Load the one that matches the work. A skill marked *coming* is not written yet: until it is, the README's program list names what was done in each program and where its fork lives.

| Skill | For |
|---|---|
| `stereo-window-3d-area` *(coming)* | A 3D viewport, canvas or video inside an ordinary window |
| `stereo-two-cameras` *(coming)* | Programs that draw a scene: the cameras, the maths, the proof |
| `stereo-video` *(coming)* | Players, encoders, containers and servers |
| `stereo-pictures` *(coming)* | Stereo photographs: JPS, MPO, viewers, screenshots |
| `deep-colour` *(coming)* | 10, 12 and 16 bits from the driver to the canvas |
| `vr-to-3d` *(coming)* | A program's VR path shown on a 3D display |
| `3d-to-vr` *(coming)* | Stereo content and the desktop in a headset |
| `drivers` *(coming)* | The kernel and GPU drivers: HDMI 3D modes, deep colour, and carrying patches until mainline takes them |
| `native-linux` *(coming)* | OpenGL, EGL, Vulkan, Qt and X11 programs on Linux |
| `proton-wine` *(coming)* | Windows programs through Wine, DXVK and gamescope |

---

# Where these came from

From the work itself: each rule here was learned on a real program, with its measurements, between September and October 2026, by Daniel directing and verifying with AI partners. They are written so the next person, or the next model, ports a solved pattern instead of solving it again.
