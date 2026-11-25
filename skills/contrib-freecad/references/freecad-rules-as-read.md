# FreeCAD's rules, as read at the source (ORDER 903, 2026-11-25)

**For** anyone preparing a change, an issue or a message for FreeCAD: every rule the project writes down, with the file, the line and the revision it was read at, and the practice its maintainers follow that no file states, each with the pull request that shows it.

Read on 2026-11-25 at FreeCAD/FreeCAD `main` 8861f26a7c (2026-11-25 15:06 +0100) and at FreeCAD/DevelopersHandbook `main` 575217f (2026-10-14).
The project's own files win over this page; read them again before each round (`git log -1 --format='%h %as' -- FILE` tells whether one changed).

## The documents

| Document | Where | Last change when read |
| --- | --- | --- |
| Contribution process | `CONTRIBUTING.md` | a7bc38c056, 2026-11-07, Max Wilfinger |
| AI policy | `AI_POLICY.md` (CC BY 4.0) | cc8a5eb0dc, 2026-10-17, Louis Gombert |
| Instructions for agents | `AGENTS.md` | a7bc38c056, 2026-11-07 (pull request 33660) |
| Pull request template | `.github/pull_request_template.md` | a7bc38c056, 2026-11-07 |
| Contributor guidelines | `contrib/guidelines/*.md`, nine guides, 1,304 lines | a7bc38c056, 2026-11-07 |
| Code of conduct | `CODE_OF_CONDUCT.md` (Contributor Covenant 1.4 and libvirt's) | 25e8aacbe3, 2024-07-13 |
| Security policy | `SECURITY.md` | 0eb92e4370, 2026-11-03, Chris Hennes |
| Developers Handbook | `https://freecad.github.io/DevelopersHandbook/` (repository FreeCAD/DevelopersHandbook) | per page below |

`AGENTS.md` and `contrib/guidelines` are FreeCAD's own guide for assisted work and for engineering; this skill does not repeat them.
Read `AGENTS.md` whole and the guides its table names for the task ("Write C++ or Python": writing-code.md and code-reuse.md; "commands, dialogs, task panels, text, or rendering": gui-and-translations.md; "Add tests ... or diagnose CI": testing-and-validation.md; "Prepare commits or address review feedback": contributing-changes.md).

## The rules that come first

- **The code of conduct:** "be excellent to each other"; be respectful, considerate ("many of whom have English as a second language"), forgiving. Reports go to the forum's admins and moderators (`https://forum.freecad.org/memberlist.php?mode=team`).
- **The route:** a pull request on GitHub (CONTRIBUTING 5.1, 6.7), from a branch of a personal fork (7.2: "Personal forks MAY use topic branches"; the project itself "SHALL NOT use topic branches"). An issue describes the problem first and "SHOULD seek consensus" (6.3 to 6.6). Help and discussion go to the forum (2.4).
- **A vulnerability** goes through GitHub's private advisory form (`SECURITY.md`); "a crash in FreeCAD without a demonstrated exploit" goes to a normal issue, where more developers see it.
- **AI** (AI_POLICY.md, lines 10 to 14): "We expect from our contributors: submissions that they fully understand, that they have thoroughly reviewed and tested, disclosure of AI assistance, and comments and descriptions made by contributors."
  - Line 40: "we will not accept pull requests with clearly AI-generated code, commit messages, PR descriptions, and responses to reviewer feedback."
  - Lines 46 to 56: disclosure "in the PR description (in natural language) and with git trailers in the commit messages": `Assisted-by: [Model-Family] ([Version/ID])`, for example `Assisted-by: gemini-2.5-pro (rev-1)`.
  - Line 60: the template's required box; "Don't be afraid that your English is not perfect"; with machine translation, "add original text too".
  - Line 66: "PRs from contributors outside of the "FreeCAD Developers" GitHub group will be scrutinized to find potential violations of the AI policy."
- **What `AGENTS.md` tells an assistant** (lines 29 to 44): it assists and does not act as the contributor; it does not "open, comment on, submit reviews to, label, or react to issues and PRs"; "The contributor writes commit messages, PR titles/descriptions, issue reports, comments, and review replies. Do not supply paste-ready text or polish their wording for those places. When asked, provide short factual notes: cause, changed behavior, affected files, validation, limitations, and open questions"; commits "using the contributor's own commit messages"; "Do not add AI co-author trailers, tool branding, or signatures"; "Never tick human-responsibility attestations or claim review, approval, or testing that did not happen."
  A contributor who works with assistants keeps every one of these: the assistant hands facts and code, the contributor writes and sends every text, in their own words.

## The contribution, as CONTRIBUTING.md sets it

| Clause | What it asks |
| --- | --- |
| 4.1, 4.2 | LGPL 2.1 or later; contributions under a compatible licence |
| 4.5 | Credit in the About dialog: a PR with a single commit to `src/Doc/CONTRIBUTORS` |
| 5.4 | "a minimal and accurate answer to exactly one identified and agreed-on problem" |
| 5.5 | no new dependency "unless no other option is available" |
| 5.6 | the code style guidelines where defined |
| 5.7 | "each commit MUST compile cleanly when merged with all previous commits"; checkpoint commits squashed |
| 5.9 | "MUST compile cleanly and pass project self-tests on all target platforms" |
| 5.10 | a Python API break avoided; if unavoidable, "minimized", described with the replacement, affected addons listed |
| 5.11 | each commit message "MUST succinctly explain what the commit achieves", per `git commit --help`, DISCUSSION |
| 5.12 | a UI change's body "MUST include a presentation of these UI changes, preferably with screenshots of the previous and revised state" |
| 5.13 | another author's work: attribution as the first line, original authorship kept, changes as follow-up commits or `Co-Authored-By` |
| 5.14 | the AI policy: "All communication should be done by contributors (people)" |
| 6.15, 6.16 | a PR needing more work goes to draft; a finished one that must wait gets "On hold" |

## The pull request template, box by box

| Part | What it needs as evidence |
| --- | --- |
| The summary (first comment) | a brief summary in the contributor's words |
| The required box | ticked by the person only, and only when true: "This PR is not unverified AI output, I take responsibility for it, and all communication from my side in this PR, including PR description, comments and commit messages is done by me personally." |
| AI disclosure (comment) | the technology named in the description in natural language, and the `Assisted-by:` trailer in each commit |
| Issues | "fixes #NNNN" or "closes #NNNN" for each issue the PR resolves; contributing-changes.md: closing words "only when the supported scope actually resolves that issue" |
| Before and After Images | screenshots for any GUI change |
| Notes on review (comment) | what reviewers weigh: a linked issue and consensus; the Design Working Group told of GUI changes; the CAD Working Group for workflow changes; documentation, translation and user documents; tests; rebased on main with commits squashed; backport and release notes |

## How the project works, from its records

- **Who merges.** The handbook's Maintainers Guide (176d555, 2026-07-06) lists eight maintainers (Adrián Insaurralde Avalos, Benjamin Nauck, Billy Huddleston, Kacper Donat, Louis Gombert, Pieter Hijma, Roy-043, WandererFan) and four admins (Brad Collette, Chris Hennes, Werner Mayer, Yorik van Havre).
  Of thirty viewer pull requests merged from 2026-08-02 to 2026-11-16, Chris Hennes merged 9, Max Wilfinger 8, Kacper Donat 7 and Louis Gombert 4 ([the viewer page](viewer-code-as-its-maintainers-write-it.md)).
- **Merge meetings.** "Every Monday, FreeCAD maintainers meet on a Jitsi call for an hour to go through the list of open pull requests"; "This event is open for everybody. Developers whose patches are undergoing review are encouraged to join the call" (Maintainers Guide). A large API change waits for one: "I prefer to discuss it on tomorrow's merge meeting before to merge" (Pieter Hijma, pull request 30136).
- **Assignment.** "maintainers should self-assign PRs. If a PR does not have an assigned maintainer in a reasonable time, the author may comment and ask for a maintainer" (Maintainers Guide).
- **Merge strategies.** Merge commit, rebase and merge, or squash and merge, the maintainer's choice; squash where the history is not reviewable (Maintainers Guide). Of the thirty viewer pull requests, seventeen were single commits.
- **First contributors' CI.** "The Github CI/CD pipeline will execute for any PR that is created unless the PR comes from a first-time" contributor: a maintainer starts it by hand (Maintainers Guide).
- **Labels that carry the review** (not in any written process; seen on every merged viewer PR): `Approved: Code Quality`, `Approved: UI/UX`, `Approved: Tested`, `Approved: CI`, `Requires: Code Review`; module and language labels (`Mod: Core`, `Language: C++`) set by the labeler workflow.
- **Testing by people.** GUI fixes get a tester's review: "@maxwxyz Tested, fixes the issue" (FEA-eng, pull requests 31631, 33823), and `Approved: Tested`.
- **The Design Working Group.** A PR marked for UI/UX review gets a bot comment linking a Discord thread whose discussion "is recorded and will be available at https://wg.freecad.org/logs/thread/..." (freecad-ci-runner, pull requests 32030, 32489, 31839), and the group's conclusion is posted back on the PR by a member (pull requests 32489, 31839). The handbook's Teams page gives each group's Discord.
- **Backports.** A merged fix with the label `backport releases/FreeCAD-26-3` gets its backport PR from `freecad-backport-bot` ("Successfully created backport PR for `releases/FreeCAD-26-3`", pull requests 33519, 33824, 34318); the Minor Releases page: worth backporting when the bug loses data, exposes data or is "a significant inconvenience"; a backport request is an issue titled "[BACKPORT REQUEST]" (issue template 3).
- **Releases now.** `main` is 27.1dev (`version.json`), `releases/FreeCAD-26-3` holds 26.3 (tags 26.3rc1 and 26.3rc2), and `SECURITY.md` supports 26.3dev and 1.1; FreeCAD moved from 1.x to year-based numbers after 1.1. New work goes to `main` only (CONTRIBUTING 7.1, 7.3).
- **Attribution of others' work.** A maintainer asked "if this is cherry picked from werner shouldn't you keep him as author in the commit?" (adrianinsaval, pull request 33823), and another contributor named the trailers: "Suggested-by or even Co-authored-by" (3x380V, same PR); `Suggested-by:` is used (pull request 33890).

## The handbook's code pages

- **Formatting** (Code Formatting Guidelines, 550b1fd, 2026-04-14): "only new or significantly-refactored code should have the formatting automatically applied". The page says pre-commit covers `src/Mod/AddonManager`, `src/Tools` and `tests/src`; the repository's `.pre-commit-config.yaml` covers far more, `src/Gui` included, and excludes `src/Gui/Quarter` ([the CI page](ci-on-a-fork.md)): trust the configuration.
- **Python:** Black with line length 100 (Python practices; `.pre-commit-config.yaml` line 75); "each module currently has its own style".
- **Headers** (Copyright: Headers, SPDX and Snippets, 469e557, 2026-03-26): every file with SPDX annotations; new C++ and Python files with the LGPL box; the C++ snippet is `// SPDX-License-Identifier: LGPL-2.1-or-later`, `// SPDX-FileCopyrightText: ‹Year› ‹Entity›`, `// SPDX-FileNotice: Part of the FreeCAD project.`, then the box without a copyright line. The newest files of `src/Gui` follow it with no address in the holder line (`FuzzyMatcher.h`: "2025 tetektoza"; `GeneralParameter.h`: "2026 The FreeCAD project association AISBL"; `RubberbandOverlay.cpp`: "2026 FreeCAD contributors").
- **Code review guide** (87ca7b0, 2025-10-03): commit subjects with a module prefix and in the imperative ("`Part: Add fillet feature`"; "If applied, this commit will ..."); one commit per module for a change across modules; "Every commit in the PR must compile and run properly"; "PRs must not contain any remains of development code"; "New code must not introduce any new linter warnings"; naming (classes `PascalCase`, members and functions `camelCase`; Coin nodes `So`, reimplemented Coin nodes `SoFC`; commands `Cmd` plus workbench; preference pages `DlgSettings`); "Defining new macros must be avoided"; "Boolean arguments must be avoided"; "Code should not be put in anonymous namespace" (C++ practices: use a named namespace).
- **Translation** (575217f, 2026-10-14): exceptions shown to the user in `QT_TRANSLATE_NOOP("Exception", ...)`; a Python command's context is its command name.
- **Preferences** (2024-01-05): `Base/Parameter.cpp`; preference widgets with `prefEntry` and `prefPath`.
- **Automated testing** (87ca7b0, 2025-10-03): Python `unittest` registered through `FreeCAD.__unit_test__`; C++ Google Test, "Arrange-Act-Assert"; "A single not-perfect test is better than no test at all".
