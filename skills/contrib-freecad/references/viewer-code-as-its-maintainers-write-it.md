# FreeCAD's 3D viewer code as its maintainers write it (ORDER 903, 2026-11-25)

**For** anyone changing `src/Gui`'s viewer (`View3DInventorViewer`, `View3DInventor`, `View3DSettings`, `View3DPy`, Quarter, the navigation cube, the overlays): who writes and reviews it, what reviews ask for, the forms counted in the newest files, and the pre-upload check that searches a change for each rule, with the decision each finding needs.

Written from the thirty pull requests merged into `main` from 2026-08-02 to 2026-11-16 that touch those files (the newest first-parent commits on the paths, each mapped to its pull request through GitHub's API), and from counts at `main` 8861f26a7c.
Rerun before a change: the counts move, and the [rules page](freecad-rules-as-read.md) dates every document.

## Who writes the viewer now

`git log` since the 1.1 branch point (af2d42a4aa, 2025-11-05) shows the viewer's render path rewritten on `main`: "Gui: Remove legacy GL compositing in View3DInventorViewer" and "Gui/Quarter: Remove legacy GL state usage" (tritao, 2026-01-10), "Gui: Refactor NaviCube into SoNaviCube node" (2026-03-30), "Gui: isolate the GL render-action scene path" and "Gui: capture the live viewport through QOpenGLWidget" (João Matos, July 2026), "Gui: Add a MaxFrameRate limiter" (Chris Hennes, pull request 31830), "Gui: Implement mouse move coalescing" (Ladislav Michl, 33890), "All: Header Guards ➞ Pragma Once" (pull request 27154).
João Matos (tritao on GitHub) leads the rendering rework and reviews viewer changes; Chris Hennes, Kacper Donat, Max Wilfinger and Louis Gombert review and merge most of the rest.

| Count in the thirty | Who |
| --- | --- |
| Authors | Louis Gombert 4, Ladislav Michl (3x380V) 3, and nineteen others with one or two |
| Reviewers (non-author, non-bot) | Chris Hennes 7, Kacper Donat 6, FEA-eng 5 (testing), tritao 5, Flaviu Tamas 4, Max Wilfinger 4, Louis Gombert 3, Céleste Wouters (ElementW) 2, mnesarco 2 |
| Merged by | Chris Hennes 9, Max Wilfinger 8, Kacper Donat 7, Louis Gombert 4, Roy-043 1, Pieter Hijma 1 |
| Single-commit PRs | 17 of 30 |
| PRs adding or changing tests | 6 of 30 (32030 adds four Google Test files in `tests/src/Gui`; 32489 `tests/src/Gui/Camera.cpp`; 32455, 33823, 29470, 30136) |
| Labelled `Approved: UI/UX` | 6 (32030, 32489, 32340, 28941, 30990, 31839) |
| Labelled for backport to 26.3 | 7 |

## What reviews asked, in their words

- **Scope that reaches every navigation style needs testing proportionate to it.** "Changing `lookAtPoint` (which will affect ALL nav styles) -- this seems like a really large change considering the subject of this PR ... In order to merge this, it will need quite a lot of testing first." (Chris Hennes, 30615)
- **A platform change must not leak to other platforms.** "while this is billed as a macOS-only change, it does leak through to Linux X11"; "The native-gesture branch isn't behind a `Q_OS_MACOS` guard, and should be." (Chris Hennes, 32030)
- **Every place a changed contract is used changes with it.** "If we change this here, we also need to make sure to change it here" (Chris Hennes, 33823, with three more such comments); "There are a few places in here where inconsistencies have crept in which will break things" (his change request on 33823).
- **The file's idiom wins over a newer form.** Asked "Why not a `std::unique_ptr<QTimer>`", the author answered "Matching the file's existing idiom." and it stayed (Céleste Wouters and Chris Hennes, 31830, `Quarter/QuarterWidgetP.h`); "The coding style is interesting for sure, but it aligns perfectly with the style of the file" (Benjamin Nauck, 33890).
- **Measure intervals the way they are meant.** "Is measuring the interval from the end of one frame to the next redraw intentional here?" (tritao, 31830; changed).
- **Coin's blending is known to the reviewers.** "Coin's transparency rendering uses `GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA` for both RGB and alpha, including the `SORTED_OBJECT_SORTED_TRIANGLE_BLEND` mode used by FreeCAD" (tritao, 32489).
- **Small things: names and enums over booleans.** "This should be an enum maybe `LinearDraggerStyle { Arrow, Sphere }` so it's clear what it means"; "I'd suggest adding `using ClickCallback = std::function<void()>` ... Also please check if that is the way we handle callbacks in coin." (Kacper Donat, 31839)
- **Line endings.** "you probably did change line-endings in the files so the diffs are impossible to read as everything is marked as change" (Kacper Donat, 28941).
- **Dead code goes whole.** "that whole CMake structure can also be removed" (Chris Hennes, 29470).
- **Addons affected by a change are checked.** "Based on indexed Addons, there are not Addons affected." (mnesarco, 30631)
- **Third-party code stays as close to upstream as possible.** "In general i think it is good to keep changes in 3rd party code to the minimum, as it makes it easier to update from upstream if needed." (Benjamin Nauck, 30634, about Quarter)
- **GUI changes are tested by a person and shown.** "@maxwxyz Tested, fixes the issue" (FEA-eng, 31631); before and after pictures in the review itself (Flaviu Tamas, 33519).

## The forms, counted

Counts made with `scripts/count-idioms.py` with `git grep -P -c` at `main` 8861f26a7c (743 C++ files in `src/Gui`); "viewer" is `View3DInventorViewer.*`, `View3DInventor.*`, `View3DSettings.cpp`, `View3DPy.cpp`, `Inventor/SoNaviCube.*`, `RubberbandOverlay.*`, `ColorScaleOverlay.cpp` (11 files); "newest" is the fifteen `src/Gui` files added from July to November 2026.

| Form | src/Gui | viewer | newest | Against | src/Gui | viewer | newest |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `#pragma once` | 360 files | 4 | 7 | `#ifndef X_H` guard | 3 files | 0 | 0 |
| `SPDX-FileCopyrightText` | 105 files | 6 | 6 | old box "Copyright (c)" | 614 files | 5 | 5 |
| `Base::Console()` calls | 314 lines | 16 | 1 | `fprintf(stderr` | 4 lines (2 in Quarter) | 0 | 0 |
| `FC_LOG/FC_WARN/FC_ERR` | 180 lines | 1 | 0 | `std::getenv` | 4 | 1 | 0 |
| `isOfType(`/`isDerivedFrom(` | 229 | 27 | 0 | `dynamic_cast<` | 152 | 1 | 0 |
| `freecad_cast<` | 139 | 1 | 0 | | | | |
| `->ref()`/`->unref()` | 316 | 70 | 2 | `CoinPtr<` | 35 | 2 | 0 |
| `std::unique_ptr`/`make_unique` | 238 | 16 | 0 | raw `= new X` | 1,535 | 178 | 11 |
| `connect(..., &Class::member` | 732 | 4 | 0 | `SIGNAL(`/`SLOT(` | 33 | 0 | 0 |
| `Q_EMIT` | 150 | 1 | 0 | bare `emit` | 0 | 0 | 0 |
| named namespaces | 604 | 7 | 12 | anonymous namespaces | 58 | 3 | 5 |
| `GetParameterGroupByPath(` | 241 | 16 | 1 | `ViewParams::` | 236 | 8 | 0 |

Read the table the way the reviewers do: the viewer's own form for a viewer file, the newest form for a new file.
So a new header is `#pragma once` with the three SPDX lines; diagnostics go through `Base::Console()` or the `FC_*` macros; a Coin node is tested with `isOfType`; Coin references stay `ref()`/`unref()` as in the viewer; a 3D-view preference is read in `View3DSettings::OnChange` beside its neighbours (`applySettings()` calls `OnChange` key by key) or through `Base::ParameterObserver` (Max Wilfinger, 2026-06) in new code; anonymous namespaces are used (5 of the 15 newest files) although the handbook asks for named ones: expect the question.

## The pre-upload check

Run both commands from the FreeCAD clone, on the parent of the change and its tip:

```sh
python3 "$skill/scripts/review-diff.py" --repo . "$base" "$tip"          # this page's rules; exit 1 on a "must"
bash "$skill/scripts/freecad-checks.sh" --image IMAGE . "$base" "$tip"     # FreeCAD's own hooks and lint ([CI page](ci-on-a-fork.md))
git diff --stat "$base" "$tip"; git log --format=%B "$base..$tip"
```

`review-diff.py` prints `RULE level where what`.
Walk each finding against the table: the program finds places to read, the contributor decides.

| Rule | Level | What it finds | Source | Decision |
| --- | --- | --- | --- | --- |
| R1 | must | a new header with an `#ifndef` guard or without `#pragma once` | pull request 27154; 360 to 3 | `#pragma once` |
| R2 | must | a new source file without the three SPDX lines at the top | handbook, Copyright: SPDX and Snippets | the snippet's form |
| R3 | must | an address in a copyright line of a new file | handbook snippets (year and holder only); newest files | the holder's name only |
| R4 | must | `fprintf(stderr`, `std::cerr`, `std::cout`, `printf(`, `getenv(` added | handbook code review, Common 9; writing-code.md, "Match the module's ... logging facilities"; counts | `Base::Console()` or `FC_*` at the right level; no environment switch in shipped code |
| R5 | note | `dynamic_cast<So...>` | handbook code review 20 (dedicated casts); viewer 27 to 1 | `isOfType` |
| R6 | must | a new `#define` (include guards excepted) | handbook code review, Design 6 | a `constexpr`, or the header that defines it |
| R7 | must | an `Assisted-by:` value not in the form `Model-Family (Version/ID)`, or naming a company | AI_POLICY.md lines 46 to 56 | e.g. `Assisted-by: Claude Opus 5.5 (claude-opus-5-5)`, the model the session's own record names |
| R8 | must | a subject without a `Module:` prefix or not in the imperative | handbook code review, PRs and Commits 1 and 2 | `Gui: Add ...` |
| R9 | note | more than 500 changed lines | contributing-changes.md, "Keep PRs small and structured" | split into coherent PRs, or say why not |
| R10 | note | lines added in Quarter, `src/3rdParty`, QSint or navlib | Benjamin Nauck on 30634; `.pre-commit-config.yaml` excludes Quarter | the smallest hook, in a commit of its own |
| R11 | must | a file whose line endings changed (CRLF to LF, or mixed) | AGENTS.md "Preserve ... existing line endings"; Kacper Donat on 28941 | keep the file's own endings |
| R12 | must | an ellipsis in a menu text | FEP-0007 (Active, 1.0.2): "Use an ellipsis **only** when the action requires further user input"; "Do **not** use ellipses merely because an action opens a dialog"; "the single ellipsis character `…` (not three dots `...`)" | no ellipsis for "open settings"; `…` where input is asked |
| R13 | note | a method added to a Python binding | CONTRIBUTING 5.10; mnesarco on 30631 | describe the API change, search the addons |
| R14 | must | an AI co-author trailer or tool branding in a message | AGENTS.md lines 40 and 41 | `Assisted-by:` only |
| R15 | must | words of another product in code, comments or messages (a distribution's name, its library, its settings module, a Debian patch header) | CONTRIBUTING 5.4 and 5.5 | keep it in the distribution's own patch; the offer carries only what FreeCAD needs |
| R16 | note | a new string message to a view (`strcmp("...", pMsg)`) | pull requests 32116, 30632, 30633 migrated them to methods | a method on the view |
| R17 | must | a message saying a test fails on its commit | CONTRIBUTING 5.7; handbook "Every commit in the PR must compile and run properly"; contributing-changes.md "Do not leave a broken intermediate state" | the test with the fix, or the test first only when it passes |
| R18 | must | `qDebug()` added | handbook code review, Common 9 | remove, or a real log |
| R19 | must | bare `emit`, `signals:`, `slots:` | writing-code.md (`QT_NO_KEYWORDS`) | `Q_EMIT`, `Q_SIGNALS`, `Q_SLOTS` |
| R21 | note | an anonymous namespace | handbook C++ practices, "Avoid anonymous namespaces"; 5 of 15 newest use one | a named namespace, or be ready to say why |
| R22 | note | a function-local `static` variable | handbook code review: "Global state ... should be avoided" | state on the object that owns it |

What no search finds, walk by hand: each commit builds and its tests pass (build each commit with the [build tier](ci-on-a-fork.md)); a UI change has before and after pictures and the Design Working Group is told; the issue it closes is linked and agreed; a platform-specific path is guarded for its platform; every caller of a changed contract changes with it.

### Proof of the check

On `main` against itself: `review-diff: 0 findings`, exit 0.
On a commit made to break three rules (a header with `#ifndef GUI_KNOWNBADEXAMPLE_H`, a `std::fprintf(stderr, ...)`, the subject "the example of a report"): exactly three findings, R1, R4 and R8, exit 1.
FreeCAD's own checks pass that same commit (`freecad-checks.sh`: every pre-commit hook, version sync, file case, Qt connections and codespell, exit 0): what reviewers ask is not what the CI checks, which is why this walk exists.
On the edition's four FreeCAD stereo patches as commits on the 1.1.3 tag: 66 findings, 53 on must rules ([the worked example](stereo-view-review-2026-11.md)).

## Traps (symptom, cause, fix, how found)

- **Symptom: `git am` stops with "patch does not apply" on `CommandView.cpp`, `View3DInventor.cpp`, `View3DInventorViewer.h`, `View3DPy.cpp` and `Workbench.cpp`, while `git apply --check` of the same patch passes.**
  Cause: those files are committed with CRLF line ends, and `git am` (mailsplit) drops the carriage returns from the patch's lines.
  Fix: `git am --keep-cr`; then `git show HEAD:FILE | grep -c $'\r$'` equals the line count.
  How found: the failing files were exactly the CRLF ones (`grep -c $'\r$'` at both revisions).
- **Symptom: a counting search reports two findings for one include guard.** Cause: the guard's `#define` matched the macro rule. Fix (in the script): include-guard defines are left to R1.
