# Worked example: the edition's stereo 3D view read against this skill (ORDER 903, 2026-11-25)

**For** whoever prepares FreeCAD's stereo view for `main`, and for anyone who wants to see the skill's review done on a real change: the four patches the edition carries on FreeCAD 1.1.3 (Sparky-OS/sparky-stereo-os-build, `sparky-os/packages/freecad/patches/0001` to `0004`, 1,854 changed lines), every finding with the rule it comes from, what is general for FreeCAD and what stays the edition's, and what `main` looks like for this work today.

The method: the patches as commits on the 1.1.3 tag (`git am --keep-cr`), then `scripts/review-diff.py 1.1.3 HEAD` (66 findings, 53 on must rules), `scripts/freecad-checks.sh` (clang-format), a reading of each hunk against the [rules](freecad-rules-as-read.md) and the [viewer's forms](viewer-code-as-its-maintainers-write-it.md), and `git apply` on `main` 8861f26a7c.
The design behind the patches is in [stereo-two-cameras, a Coin3D view in a Qt graphics view](../../stereo-two-cameras/references/coin-quarter-view-freecad.md).

## What `main` looks like for this work

- **Removed by pull request 30634** ("Remove stereo views", Grzegorz Kwacz, merged 2026-06-09 by Benjamin Nauck, labelled `Approved: UI/UX` and `Approved: Code Quality`): the View, Stereo menu; the commands `Std_ViewIvStereoRedGreen`, `Std_ViewIvStereoQuadBuff`, `Std_ViewIvStereoInterleavedRows`, `Std_ViewIvStereoInterleavedColumns`, `Std_ViewIvStereoOff`; the Python methods `setStereoType`, `getStereoType`, `listStereoTypes` and their stubs in `FreeCADGui._View3DInventor.pyi` ("Note that it is a breaking Python API change"); the `SetStereo...` view messages; the axis cross's grey colours in stereo; five icons and their shortcuts.
  It closed issues 27816 (interleaved rows or columns freeze FreeCAD), 21496 (orthographic red/cyan flickers) and the author's own 30633.
  In the thread, Turan Furkan Topak (Reqrefusion) wanted the feature kept; Kacper Donat: "It either should be fixed or removed and I am in favor of full removal. If anything it would be better to have something more modern like VR support."; Benjamin Nauck asked to keep Quarter's own stereo code, which "exists upstream".
- **Still on `main`:** Quarter's whole stereo API (`QuarterWidget::StereoMode`, `setStereoMode`, `stereoModeActions`, its context menu), the "Eye to eye distance" preference (`PreferencePages/DlgSettings3DView.ui`, `View3DSettings.cpp` line 353, `EyeDistance`), and an orphan `qApp->translate("Workbench", "&Stereo")` in `Workbench.cpp` line 598.
- **The viewer since 1.1** (155 commits on the files the patches touch, 2025-11-05 to 2026-11-25): the GL compositing and Quarter's legacy GL state removed (tritao, 2026-01-10), the navigation cube a Coin node, the render-action scene path isolated and the live viewport captured through `QOpenGLWidget` (João Matos, July 2026), a frame-rate limiter in Quarter (31830), Rift support removed (30652), view messages migrated to methods (32116), headers to `#pragma once` (27154).
- **The patches on `main`:** `git apply --check` fails for all four.
  With `--reject`, in order: 0001 loses 25 hunks in 8 files (`CMakeLists.txt` 3, `CommandView.cpp` 3, `Quarter/QuarterWidget.cpp` 1, `View3DInventor.cpp` 2, `View3DInventorViewer.cpp` 9 of 12, `View3DInventorViewer.h` 3, `View3DPy.cpp` 3, `Workbench.cpp` 1) and applies its four new files, `QuarterWidget.h`, `View3DSettings.cpp` and the preference page; 0002 loses 3 (the two `CMakeLists.txt`); 0003 applies on top; 0004 loses 2 of 4 in `View3DInventorViewer.cpp`.
  The line endings are not the cause (the same files are CRLF on both sides); the code moved.
  So the work for `main` is a rewrite on the new render path, not a rebase.

## The findings

"Rule" is the pre-upload check's rule or the document the finding comes from; "Kind" says what it is for an offer to FreeCAD: **fix** (must change), **ask** (a reviewer will ask; decide and say), **ours** (the edition's own, not offered).

| # | Where | Finding | Rule | Kind |
| --- | --- | --- | --- | --- |
| 1 | all four messages | Subjects are noun phrases ("Gui: the 3D view in stereo, fitted to ..."), not the imperative ("Gui: Draw the 3D view as a stereo pair") | R8; handbook code review | fix |
| 2 | all four messages | `Assisted-by: Claude Opus 5.5 (Anthropic)`: the policy's form is `Model-Family (Version/ID)`, not a company | R7; AI_POLICY.md | fix |
| 3 | all four messages | A DEP-3 line in the message (`Forwarded: not-needed (FreeCAD's AI_POLICY.md and AGENTS.md; ...)`), and its reason is superseded: the work is now to be offered | R15 | fix in an offer; the edition's recipe updates its README and headers |
| 4 | 0002 | Its message says "On this commit its translucent, annotation and unfogged cases fail": a commit whose own tests fail | R17; CONTRIBUTING 5.7; handbook "Every commit in the PR must compile and run properly" | fix: the test lands with the code that passes it |
| 5 | 6 new files | Header in the old form with `Copyright (c) 2026 Daniel Campos Ramos <address>`; the test file has only the licence line | R2, R3; handbook snippets | fix: the three SPDX lines, holder without address |
| 6 | 3 new headers | `#ifndef GUI_VIEW3DSTEREO..._H` guards | R1; pull request 27154 | fix |
| 7 | 8 files, 31 hunks | clang-format (1.1.3's pin, v21.1.5) rewrites them: pre-commit fails | `.pre-commit-config.yaml` | fix: format the changed lines with `main`'s pin (v23.1.0) |
| 8 | `View3DStereo.cpp` | `FREECAD_STEREO3D_TRACE` read with `std::getenv`, three `std::fprintf(stderr, ...)` | R4 | ours for the trace; an offer logs through `Base::Console().log()` or `FC_LOG` |
| 9 | `View3DStereo.cpp` | `#define GL_RGBA32F 0x8814` | R6 | fix: Qt's OpenGL headers define it |
| 10 | `View3DStereo.cpp` | Function-local statics: the trace flag, the stereo probe's cache, the "told once" set, the Wayland initialisation | R22 | ask: state on the object, or a stated reason |
| 11 | `View3DStereo.cpp` | `dynamic_cast<SoGroup*>` on the render manager's scene, twice | R5 | fix: `isOfType` |
| 12 | `Quarter/QuarterWidget.*` | 56 lines in third-party code: the per-buffer loop in `paintEvent`, `replaceViewport(format)`, three virtual hooks | R10; Benjamin Nauck on 30634 | ask: the smallest hook, its own commit; `paintEvent` changed on `main` (2026-01-10) |
| 13 | `CMakeLists.txt` | `pkg_check_modules(STEREO_DECLARE REQUIRED ...)` on every Linux build, and `Qt6::GuiPrivate` | R15; CONTRIBUTING 5.5 (no new dependency) | ours |
| 14 | `View3DStereo.cpp`, `View3DStereoLimits.*` | The desktop's depth limits through libstereo-declare and Qt's private `QPlatformNativeInterface`, polled four times a second; Display Settings through `systemsettings kcm_kscreen` | R15 | ours; an offer takes the separation from FreeCAD's own preference |
| 15 | comments in every new file | "the person's depth limits", "the edition's Qt", "Sparky Stereo OS's KWin" | R15 | fix in an offer |
| 16 | `DlgSettings3DViewImp.cpp` | The eye distance widgets hidden in code | R15 | ours (one separation, one place); an offer keeps the preference |
| 17 | `View3DPy.cpp` | `setStereoType`, `getStereoType`, `listStereoTypes` changed; on `main` they no longer exist | R13; CONTRIBUTING 5.10 | ask: a new Python API needs its stub and the binding check, or none at all |
| 18 | `View3DInventor.cpp` | `SetStereoQuadBuff` and `SetStereoOff` view messages kept | R16; pull request 32116 | fix: a method, or nothing |
| 19 | `CommandView.cpp`, `Workbench.cpp` | `Std_ViewIvStereoQuadBuff` relabelled "Enable 3D" (an id that says quad buffer for a check box that is not a mode); "3D &Display Settings..." with an ellipsis; a View, Stereo menu that 30634 removed with UI/UX approval | R12 (FEP-0007, Active: no ellipsis for an action that only opens a dialog, and never three dots); PR template ("Design Working Group aware") | fix the text; ask the Design Working Group first; a command named for what it does |
| 20 | size | 1,854 changed lines; 0001 alone 1,192 insertions | R9; contributing-changes.md | fix: a series of PRs of about 500 lines |
| 21 | tests | One unit test file, for the fit function; nothing for the orthographic shear, the eye cameras, picking, or stereo off; the CI's Coin node snapshot tests not run | testing-and-validation.md ("Rendering": "existing visual snapshots"); `sub_buildUbuntu.yml` | fix: unit tests of the shear and the camera offsets, a snapshot row with stereo off unchanged |
| 22 | `View3DInventorViewer.*` | `framebufferRight` as a raw owning pointer | the file's own `framebuffer` is one (R5's table: raw `new` 178 in the viewer) | keep the file's form, or ask |
| 23 | translations | The twelve sentences come with a `.ts` patch | gui-and-translations.md: "Do not edit managed `.ts`/`.qm` output by hand" | ours; an offer carries source strings only (Crowdin) |
| 24 | process | No issue links the work; 27816 and 21496 are closed | PR template, "Issues"; CONTRIBUTING 6.2 to 6.6 | ask: an issue or the 30634 thread's answer first |

Not checked in this round: clang-tidy and the C++ tests on these commits (the build tier was run on `main` only), and the Coin node snapshot tests.

## General for FreeCAD, and the edition's own

**General** (what a FreeCAD user on any stereo-capable OpenGL desktop gets, and what answers the closed issues):
- The quad-buffer path made to work on Qt 6: the viewport is a `QOpenGLWidget`, which never draws to `GL_BACK_LEFT` and `GL_BACK_RIGHT`; drawing each eye in Quarter's paint event after `makeCurrent(QOpenGLWidget::LeftBuffer)` and `RightBuffer` (Qt 6.5) is what makes it draw (issue 27816 reports that no mode displayed anything).
- Two parallel cameras through the one viewport: Coin's own stereo camera for perspective, and for orthographic the view volume moved by the inverse world shear, which keeps an orthographic projection and gives a disparity linear in depth (issue 21496; Céleste Wouters there: "there is no parallax in orthographic by definition", which the shear answers with numbers).
- Picking, preselection and navigation from the camera between the eyes; the overlays at the screen's depth.
- The fit: the separation from the scene's own depth, read once per frame, so no pixel passes a limit; the limit itself, upstream, from FreeCAD's "Eye to eye distance" preference or a depth preference of its own.
- The Image and Framebuffer render types per eye.

**The edition's own** (kept in the edition's package, never offered): libstereo-declare and the desktop's depth limits, the poll, the Display Settings shortcut, the hidden eye-distance preference, the trace switch, the translations patch, Debian's build changes.
