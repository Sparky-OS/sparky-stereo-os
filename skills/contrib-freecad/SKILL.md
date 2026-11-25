---
name: contrib-freecad
description: >-
  Contribute to FreeCAD on GitHub the way its maintainers work: CONTRIBUTING.md, AI_POLICY.md (Assisted-by in each
  commit, the template's required box, scrutiny outside FreeCAD Developers), AGENTS.md (the contributor writes every
  text), commit and pull request form, labels, the Design Working Group, backports, the 3D viewer's idioms
  (View3DInventorViewer, Quarter, Coin), CI primary on a fork, and a pre-upload check. Load it with upstream-outreach
  for a FreeCAD pull request, issue or review answer, a change to src/Gui or the 3D view, git am failing on CRLF files,
  a fork's Lint job skipped, or a reviewer asking for #pragma once, Base::Console or a smaller PR.
---

# Contributing to FreeCAD

**Check freshness first.**
Written on 2026-11-25 (ORDER 903) from FreeCAD/FreeCAD `main` 8861f26a7c, the Developers Handbook 575217f, thirty merged viewer pull requests and FreeCAD's CI run in containers.
The project's own files win over this page: read `CONTRIBUTING.md`, `AI_POLICY.md`, `AGENTS.md` and the pull request template again before each round (`git log -1 --format='%h %as' -- FILE`).
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is FreeCAD's own practice.

FreeCAD writes down more than most projects: `AGENTS.md` for assisted work and nine engineering guides in `contrib/guidelines`.
This skill does not repeat them; it links them and adds what they leave out: the practice seen in the reviews, the checks as commands, the CI on a fork, and the traps.

## The rules that come first

- **The code of conduct** (`CODE_OF_CONDUCT.md`, Contributor Covenant 1.4 and libvirt's): "be excellent to each other"; respectful, considerate of members with "English as a second language", forgiving. Reports to the forum's admins and moderators.
- **The route:** an issue that states the problem and seeks consensus, then a pull request from a branch of a personal fork to `main` (CONTRIBUTING 5.1, 6.2 to 6.7, 7.2). Help and discussion on the forum. A vulnerability through GitHub's private advisory form; a crash without an exploit is a normal issue (`SECURITY.md`).
- **AI** (`AI_POLICY.md`): the contributor submits what they "fully understand" and have "thoroughly reviewed and tested", discloses the assistance in the PR description in natural language and with `Assisted-by: [Model-Family] ([Version/ID])` in each commit, and writes the comments and descriptions; "we will not accept pull requests with clearly AI-generated code, commit messages, PR descriptions, and responses to reviewer feedback"; contributors outside the "FreeCAD Developers" group are scrutinized.
- **`AGENTS.md` binds the assistant:** it does not communicate on GitHub or any project channel; the contributor writes commit messages, PR titles and descriptions, issues, comments and review replies ("Do not supply paste-ready text or polish their wording for those places. When asked, provide short factual notes"); commits use "the contributor's own commit messages"; no AI co-author trailers or branding; it never ticks the attestation or claims testing that did not happen.

So with an assistant the split is: the assistant reads, measures, writes code and tests, runs the checks, and hands the person facts (cause, changed behaviour, files, validation, limits); the person reviews and understands every line, tests the workflow, writes and sends every text in their own words, ticks the box only when true, and answers reviewers.
The edition's own disclosure line ("AI was leveraged.") does not replace FreeCAD's form: the PR description names the technology in natural language, as the policy asks.
Every rule with its clause, line and revision: [FreeCAD's rules, as read](references/freecad-rules-as-read.md).

## Working recipe

1. **Read the rules again** (the four files above, and `contrib/guidelines/README.md` for the guides the task needs).
2. **Find the issue, or open one first.** A pull request "SHOULD be a minimal and accurate answer to exactly one identified and agreed-on problem" (CONTRIBUTING 5.4); search closed attempts and removals (for the 3D view: pull request 30634).
3. **Read who writes the folder and how,** with the counts: [the viewer's code as its maintainers write it](references/viewer-code-as-its-maintainers-write-it.md) (`git log -20 --author=NAME -- DIR`; `scripts/count-idioms.py`).
4. **Work on a fork's branch off `main`,** in commits that each build and pass their tests, of about 400 to 500 changed lines per pull request (contributing-changes.md).
   Apply a patch made against FreeCAD's CRLF files with `git am --keep-cr`.
5. **Run the pre-upload check** on the parent of the change and its tip:
   ```sh
   python3 scripts/review-diff.py --repo FREECAD BASE TIP                        # this skill's rules; exit 1 on a "must"
   bash scripts/freecad-checks.sh --image LINT_IMAGE FREECAD BASE TIP             # FreeCAD's pre-commit and Lint scripts
   bash scripts/freecad-ci-build.sh --image UBUNTU_26_04 --build DIR --tidy-base BASE FREECAD   # build, C++ tests, clang-tidy
   ```
   Expect `review-diff: 0 findings`, `freecad-checks: exit 0`, `freecad-ci-build: exit 0`; walk every finding against the [rule table](references/viewer-code-as-its-maintainers-write-it.md#the-pre-upload-check).
6. **Run FreeCAD's CI on the fork** through a pull request inside the fork (base: the fork's `main`, synced; head: the branch), never through FreeCAD's repository ([CI on a fork](references/ci-on-a-fork.md)).
7. **The person tests the workflow** in FreeCAD and takes the before and after pictures of any UI change (CONTRIBUTING 5.12).
8. **The person writes and opens the pull request:** the summary, the AI disclosure in natural language, "fixes #N" for the issues it resolves, the pictures; tells the Design Working Group of a UI change; ticks the box only when true.

## The change

| Part | FreeCAD's form | Source |
| --- | --- | --- |
| Subject | `Module: Imperative verb ...` (`Gui: Draw the 3D view as a stereo pair`), completing "If applied, this commit will ..." | handbook code review, PRs and Commits 1 and 2 |
| Body | what and why, in the contributor's words; "AI disclosure does not replace an explanation of the change" | contributing-changes.md |
| Trailers | `Assisted-by: Model-Family (Version/ID)` where assisted; `Co-Authored-By` only for a human co-author; `Suggested-by:` is used | AI_POLICY.md; AGENTS.md; pull request 33890 |
| Commits | each builds and runs; one per module for a change across modules; no checkpoint commits | CONTRIBUTING 5.7; handbook |
| New file | `// SPDX-License-Identifier: LGPL-2.1-or-later`, `// SPDX-FileCopyrightText: YEAR HOLDER`, `// SPDX-FileNotice: Part of the FreeCAD project.`, the licence box, `#pragma once` in a header | handbook snippets; pull request 27154 |
| Size | about 400 to 500 changed lines per PR; a larger one says why | contributing-changes.md |
| Python API | a break avoided, or described with its replacement and the affected addons listed | CONTRIBUTING 5.10 |
| UI | before and after pictures; the Design Working Group told (a bot links its recorded Discord thread on PRs marked for UI/UX review) | CONTRIBUTING 5.12; PR template; pull requests 32030, 32489 |
| Text | FEP-0007: Title Case commands, sentence case labels, tooltips in the third person; `.ts` files are Crowdin's | gui-and-translations.md |

After the pull request: maintainers self-assign; reviews end in labels (`Approved: Code Quality`, `Approved: UI/UX`, `Approved: Tested`, `Approved: CI`); a tester's "Tested" review for GUI fixes; the Monday merge meeting on Jitsi is open to authors; a fix labelled `backport releases/FreeCAD-26-3` gets its backport PR from a bot.
A first contribution's CI waits for a maintainer to start it.
`main` is 27.1dev; 26.3 is in release candidates; 1.1 is still supported for security.

## The viewer's code, in brief

From the counts and reviews in [the viewer page](references/viewer-code-as-its-maintainers-write-it.md):
- Diagnostics through `Base::Console()` or `FC_LOG`, never `fprintf(stderr)` or an environment switch.
- Coin nodes tested with `isOfType`; Coin references with `ref()`/`unref()` as the viewer does.
- A 3D-view preference read in `View3DSettings::OnChange` beside its neighbours.
- Typed `connect`, `Q_EMIT`; no new macros; enums over booleans.
- Quarter is third-party code: the smallest hook, in its own commit ("keep changes in 3rd party code to the minimum", Benjamin Nauck on 30634).
- The file's own idiom wins over a newer form ("Matching the file's existing idiom.", Chris Hennes on 31830).
- A change that reaches every navigation style or another platform needs testing in proportion and a platform guard (Chris Hennes on 30615 and 32030).

## Traps

- **`git am` refuses FreeCAD's CRLF files** (`CommandView.cpp`, `View3DInventor.cpp`, `View3DInventorViewer.h`, `View3DPy.cpp`, `Workbench.cpp`) while `git apply` accepts the patch: `git am --keep-cr`. Check that the file stays CRLF.
- **A fork's Lint job is skipped:** only a `pull_request` event fills the changed-file lists; use a pull request inside the fork.
- **The handbook's list of pre-commit folders is stale:** `.pre-commit-config.yaml` covers `src/Gui` and most modules, and excludes `src/Gui/Quarter`.
- **A container check passes in a third of a second:** `docker run` without `-i` fed `bash -s` nothing; the script now refuses a run without its verdicts.
- **FreeCAD's lint scripts crash outside GitHub** in `emit_problem_matchers`: set `RUNNER_WORKSPACE`.
- **A patch made on a release does not apply to `main`:** since 1.1 the viewer's render path, Quarter's GL state and the view messages changed; rewrite on `main`, never force a rebase.

Each with its cause and how it was found: [CI on a fork](references/ci-on-a-fork.md#traps-symptom-cause-fix-how-found) and [the viewer page](references/viewer-code-as-its-maintainers-write-it.md#traps-symptom-cause-fix-how-found).

## Worked example

[The edition's stereo 3D view read against this skill](references/stereo-view-review-2026-11.md): four patches on 1.1.3 (1,854 lines), 24 findings with the rule each comes from, what is general for FreeCAD and what stays the edition's, and what `main` looks like after pull request 30634 removed the stereo views.
