---
name: sparky-stereo
description: Operating rules for stereo 3D and deep colour work on Sparky Stereo OS and on the programs it changes, with or without AI assistance. Load it first, before any other skill in this folder; it ends by saying which one to load next.
---

# Working on Sparky Stereo OS

Sparky Stereo OS 9 "Mashtabba", based on Debian 14 "Forky", is Daniel Ramos's stereo 3D edition of SparkyLinux (by Paweł "pavroo" Pijanowski), KDE Plasma only.
Its aim is a desktop where stereo 3D and deep colour (10, 12 and 16 bits per channel) are part of the system, not a feature of a few programs.
This skill holds what every piece of work on it must respect.
The other skills in this folder hold the solved patterns for one kind of work each.

**Check freshness first.**
Written on 2026-10-07, updated on 2026-10-10.
If the [README](../../README.md) or the pages it links say something different, they win and this skill is history.

---

# Part zero: the posture

Everything below is a rule, and rules are followed when someone is watching.
This part is about what to be when nobody is.

**Act as a valued senior partner.** This applies to people and to assistants from any provider, including local models.
A senior partner tells you when you are wrong, asks the awkward question before the work ships, and says "I could not verify that" early, because a stated gap is cheap and a discovered one is expensive.

- **Push back.** If a request contradicts the contract below, the specification or the measured result, say so and say why.
- **Refuse to claim what you did not measure.** No "works", no "fixed", no number you cannot point at. "Not verified" is a complete answer.
- **Own the error first.** Name your own mistake before anyone else does, specifically.
- **Protect the program and its users from your own output.** You are the last check before a stranger installs it.

## Working recipe

1. Name the task and the layer that owns it: input/metadata, shared library, application, compositor or physical output.
2. Read only that domain's skill and the current source. Dates and measurements below describe their recorded versions; verify them before carrying a change forward.
3. Define one observable success and the relevant unchanged behavior. For a bug fix, retain a reproduction that fails before the fix.
4. Implement and test in an isolated environment, then test the installed package when packaging is in scope.
5. Hand back the diff, exact versions, commands, results and gaps using [ai-partners](../ai-partners/SKILL.md). Humans can follow the same recipe without any AI client.

The [skills index](../README.md) routes tasks; the [maintainer workflow](../../docs/maintainer-workflow.md) connects them to the distro developer package.
Do not load every domain merely because it is listed here.

**On the tool question.**
We judge the artefact, not the author: whether the person behind it verified, understood and owned what they published.
Daniel's position is written in awesome-stereoscopy's [PROVENANCE.md](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/PROVENANCE.md#on-slop), and Linus Torvalds works the same way: his AI-assisted drm/xe fix, [818bebeb63dd](https://github.com/torvalds/linux/commit/818bebeb63dd6bf5f4e07e145f6cdbace520a34c), was a person directing, a verified result and an honest disclosure in the commit itself.
On 9 October 2026, at Open Source Summit Europe, he put it in words: "I think AI is a wonderful tool if you use it correctly and treat it as a tool", and "you need to be very careful using AI when you're doing something real and important"; the cost he named is the reviewers' time ([ZDNET](https://www.zdnet.com/tech/linus-torvalds-ai-coding-programming/)).
So every change of ours arrives small, tested and explained.

---

# Part one: the contract

- **One format inside.** Programs decode or generate stereo in any standard and hand the desktop **full side by side**: the two eyes as separate pictures side by side, left eye first, each at the resolution it has, declared once. "Full" names the layout, not a size: any resolution is the pact, half-width and half-height eyes included (a half top-and-bottom 1920x1080 frame becomes one 3840x540 buffer), and the program never resizes an eye. In a window or full screen, Stereo KWin does the one resize. Stereo KWin's outputs, one per kind of screen, turn that into what each screen needs: a 3D television's HDMI 3D modes, anaglyph on any monitor, interleaved and frame-sequential displays, a headset. [How it works](../../docs/how-it-works.md) explains why, and why it is how PipeWire already handles sound.
- **Per-monitor settings live in one place:** Stereo KWin's outputs (Display Configuration), and beneath them the drivers and the kernel. A program has no per-monitor stereo setting; it hands the same declared pair to every screen.
- **The definitive eye swap is the output's.** Stereo KWin swaps left and right per output, in Display Configuration. A program offers no swap of its own for everything it shows; it offers only the per-file correction of its input, "Swap left and right eyes", and only for content it shows in 3D.
- **Never touch the user's file on your own.** A per-file choice (the eye swap, the input packing chosen for an unmarked file) is kept where the program already keeps its per-file state, next to the resume position of "continue playback", and is forgotten with it. The program offers to save the choice to the file, and writes the file only when the person chooses that; once saved, the file carries the correction and the per-file option goes back to unmarked, its stored entry cleared.
- **A program that has its own output modes loses them** in the edition's build, so nothing can break the contract; its stereo settings live in a sister folder with "stereo" in the name.
  This is not removing functionality: Stereo KWin gives every program every output, on every screen.
  There is no direct path to the screen, and a program's own modes would only be more inputs for the desktop to keep working.
- **A window's 2D part and its 3D area are separate surfaces.** Menus, toolbars and on-screen displays are the window's own surface at one eye's size, identical in both eyes, and declare nothing. The 3D area (a video, a viewport, a canvas) is a surface of its own, declared as full side by side. Only a program that is stereo and full screen only makes its whole window stereo.
- **Depth for the 2D parts** is declared, never faked: three planes, sunk, screen and popped, a few pixels each ([Depth on the desktop](../../docs/depth-on-the-desktop.md)).
- **The whole specification in every API.** A stereo enum or field lists every frame packing the standards define (H.264 and H.265 Table D-8, which H.264 V15 (08/2024) numbers D-8 and V16 (06/2026) D-9, Matroska `StereoMode` in [RFC 9559](https://www.rfc-editor.org/rfc/rfc9559)), both eye orders, never a subset. Every rule cites its specification; awesome-stereoscopy's [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md) links them.
  Use a format's own stereo field wherever its specification has one; define a mark of our own only where none exists, and write its specification page first ([SVGStereo](https://github.com/Sparky-OS/svgstereo) is the example).
  Every mark, a format's own or ours, is registered in the shared library, [stereo-layer](https://github.com/Sparky-OS/stereo-layer), so every program reads it the same way, and in the shared documents: awesome-stereoscopy's [standards page](https://github.com/danielcamposramos/awesome-stereoscopy/blob/main/standards.md) and the edition's [house formats](../../docs/house-formats.md).
- **Choose the rendering model for the content.** A 3D scene needs coherent per-eye projections of one world, including visibility, lighting and view-dependent effects. Desktop planes can use two synchronized 2D views of shared state, with depth-dependent horizontal disparity; no application 3D engine is required. KWin already applies this through its effects paint path, including receiver-plane shadows. Moving arbitrary fragments of a flattened 3D scene does not reconstruct its missing views. See [the toolkit/depth guidance](../stereo-window-3d-area/references/qt-kde-depth.md).
- **The engine, not the program.** When two programs need the same stereo code, it belongs in the layer they share (Qt Multimedia, MpvQt, Mesa, KWin), so each program's own change shrinks to its interface.
- **House formats.** Stereo is one case of a rule for every medium: one format inside, conversions only where it enters and where it leaves, defaults from the hardware ([house formats](../../docs/house-formats.md)).
- **Quality.** In the edition: video at the source's depth, each eye at the resolution it has (never resized by the program), the colour description kept; audio at 24-bit 48 kHz or more wherever the hardware offers it. In a patch offered upstream: the project's own defaults stay, and the patch makes the higher-quality paths available.
- **When two ways give the person different results, build them all.** If a design has two or more paths and each gives the person something different, the edition builds every path and offers them as a choice, with one as the default. When paths differ only inside the code, choose one and say why.
  The contract above is not such a choice: a program's own output modes are not a path to the screen, Stereo KWin is.

---

# Part two: what counts as proof

A change is done when it is measured, not when it compiles.

- **Both eyes, captured.** Clips or scenes marked so each eye can be read by a script (the left eye red, the right eye blue, a frame number in both), captured from the real compositor, checked over time: the right colour in each eye, the same frame number in both, one declaration per stereo surface, nothing declared for 2D content.
- **The 2D parts:** with desktop depth disabled, 0 differing pixels between the eyes outside the 3D area under identical backgrounds. With plane depth enabled, check the intended disparity and the same logical content/input; use an opaque fixture or identical background to separate content errors from different alpha blending over the two scene views.
- **The 2D control:** the changed program with stereo off against the distribution's own build, 0 differing pixels. This is the answer to "you will break something else".
- **Geometry against a prediction.** For anything drawn by cameras, compare the measured disparity with a closed-form prediction, and report the error (median, and the share within one pixel), and the vertical disparity, which must be zero.
- **Numbers, and the gaps.** Report what passed with its numbers, what failed with its output, and what was not verified. A pass is a pass within its measured scope. Stereo evidence does not establish HDR correctness: record colour primaries, transfer function, range, precision, metadata and actual output separately.
- **Check a label by eye.** A script that classifies colours can mislabel a correct capture; look at one before believing it.

---

# Part three: working with upstream

- **Patches in upstream style.** The smallest change, in the one place that owns the behaviour, written like the code around it, so maintainers judge what it does.
- **The project's CI first, locally,** green before anything is pushed; a failure is compared with the unpatched release. A release tag's own CI can be red: check whether upstream fixed its CI after the tag, and if so run the CI on a branch based on the current development branch. Never use a project's own CI as a test bench.
- **Build once with clang too.** A project's Windows and FreeBSD jobs cannot run locally, and GCC accepts code that MSVC and FreeBSD's clang reject: KFileMetaData's first pipeline on KDE's CI was green on Linux and red on both, over one test file where `Property::X` was ambiguous after two `using namespace` lines.
- **Say where the work is used.** An offer names the edition that ships it and the users it serves, and it never makes the edition depend on the merge.
- **Disclose AI assistance once,** where the project's format asks (for example an `Assisted-by:` trailer), not again in every comment.
- **Test every mode, not the common one.** The x265 frame packing option passed every test with the SEI in its own unit; a reviewer found that in `--single-sei` mode the units carried stale bytes, a bug older than the option that the option made visible ([x265 #986](https://github.com/Multicorewareinc/x265/pull/986); the fix is [#988](https://github.com/Multicorewareinc/x265/pull/988); both in review). Enumerate a feature's modes and test each.
- **Gerrit projects (Qt):** before the first push, an account, the contributor agreement and the commit's author email registered on it; then `git push ... HEAD:refs/for/dev`. Use the `Pick-to:` branches the module's own recent changes use (the Sanity Bot flags a missing one), and add the module's regular reviewers from the file's history, because the welcome bot adds only general helpers. Answer a suggestion with a new patch set and a "Done" on its thread. A reviewer may upload a patch set of their own: fetch the latest one before amending, never push over it. Our first change went from upload to a reviewer's +1 in one evening: Tim Blechmann asked for one line, then parameterized the test himself ([Qt 778399](https://codereview.qt-project.org/c/qt/qtmultimedia/+/778399)).
- **A page behind a bot wall** (a 403, an automated check) is read from the Wayback Machine's copy, one request at a time, with the capture date stated; never with a stealth browser.

Merged so far, for the shape of a good offer: [HandBrake #8100](https://github.com/HandBrake/HandBrake/pull/8100), [Universal Media Server #6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330), [MKVToolNix !6311](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6311), [mpv #18490](https://github.com/mpv-player/mpv/pull/18490).

---

# Part four: which skill next

Load the one that matches the work; the [program list](../../docs/programs-in-detail.md) names what was done in each program.

| Skill | For |
|---|---|
| [`stereo-proof-rig`](../stereo-proof-rig/SKILL.md) | How to produce the proof: a headless Stereo KWin, captures of both eyes, the checks |
| [`stereo-window-3d-area`](../stereo-window-3d-area/SKILL.md) | A 3D viewport, canvas or video inside an ordinary window |
| [`stereo-two-cameras`](../stereo-two-cameras/SKILL.md) | Programs that draw a scene: the cameras, the maths, the proof |
| [`stereo-video`](../stereo-video/SKILL.md) | Players, encoders, containers and servers |
| [`stereo-pictures`](../stereo-pictures/SKILL.md) | Stereo photographs: JPS, MPO, viewers, screenshots |
| [`deep-colour`](../deep-colour/SKILL.md) | 10, 12 and 16 bits from the driver to the canvas |
| [`vr-to-3d`](../vr-to-3d/SKILL.md) | A program's VR path shown on a 3D display |
| [`3d-to-vr`](../3d-to-vr/SKILL.md) | Stereo content and the desktop in a headset |
| [`vkms-stereo`](../vkms-stereo/SKILL.md) | Testing stereo without a 3D display: VKMS with a 3D EDID, the writeback bench, IGT and KWin in a VM |
| [`stereo-vm`](../stereo-vm/SKILL.md) | A virtual machine's stereo display: QEMU's window, virt-viewer, virt-manager and Karton, the pointer in a 3D mode, the controls that must fail |
| [`drivers`](../drivers/SKILL.md) | The kernel and GPU drivers: HDMI 3D modes, deep colour, and carrying patches until mainline takes them |
| [`native-linux`](../native-linux/SKILL.md) | OpenGL, EGL, Vulkan, Qt and X11 programs on Linux |
| [`proton-wine`](../proton-wine/SKILL.md) | Windows programs through Wine, DXVK and gamescope |
| [`gamecontroller`](../gamecontroller/SKILL.md) | KDE controller models and labels for flight and racing rigs, preserving every raw control and verifying upstream profiles |
| [`edition-packaging`](../edition-packaging/SKILL.md) | The edition's tasks and metapackages, tasksel, keeping our builds the only candidates, the media stack on deb-multimedia |
| [`lean-code`](../lean-code/SKILL.md) | Lean Code: text files installed without the comments the machine never reads, how each format is checked, and how to verify, explain or undo a file with dpkg-stereo |
| [`stereo-artwork`](../stereo-artwork/SKILL.md) | Artwork in an existing style, stereo pairs with a measured separation, animation in both eyes, editable deliverables |
| [`power-idle`](../power-idle/SKILL.md) | KDE idle, lock, laptop lids, power-profile holds, CEC ownership and console isolation proof |
| [`system-housekeeping`](../system-housekeeping/SKILL.md) | Self-pruning defaults (kernels, logs, crash dumps, GRUB) and cleaning a system safely |
| [`ai-partners`](../ai-partners/SKILL.md) | AI assistants joining the work: roles, briefs, proof, review, upstream manners, provenance |
| [`upstream-outreach`](../upstream-outreach/SKILL.md) | Bringing AI-assisted work to projects and people: a heads-up to the maintainer before any merge request, evidence first, one ask, one knock, the right venue |
| [`audio`](../audio/SKILL.md) | PipeWire, WirePlumber and KDE's Sound page: the audio house format, routing, formats, passthrough, virtual surround, MIDI |
| [`brazil-certificates`](../brazil-certificates/SKILL.md) | ICP-Brasil certificates, the E-521 root, browsers, tokens and the court signer |
| [`certificate-manager`](../certificate-manager/SKILL.md) | Sparky CA's verified ICP-Brasil catalogue and Ed521 checks across OpenSSL, NSS, Java and KDE |
| [`writing-front-pages`](../writing-front-pages/SKILL.md) | The first text a stranger meets: README tops, profiles, calls for testers, list and page openings, About lines, and the cold-reader test |
| [`qt-android-ci`](../qt-android-ci/SKILL.md) | Qt Multimedia's Android tests run locally on a headless emulator, the way Qt's CI runs them: build, compare patch sets, read the results |


**Leave a skill behind.** When work in a new area is accepted, write what the next person needs as a skill in this folder, or extend the one it belongs to, and add it to this table.
---

# Where these came from

From the work itself: each rule here was learned on a real program, with its measurements, between September and October 2026, by Daniel directing and verifying with AI partners.
They are written so the next person, or the next model, ports a solved pattern instead of solving it again.
