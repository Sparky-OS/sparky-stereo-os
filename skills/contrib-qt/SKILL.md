---
name: contrib-qt
description: >-
  Contribute a Qt module change through Gerrit: the CLA and the verified author email, the commit-msg hook and
  Change-Id, git push HEAD:refs/for/dev with reviewers, Pick-to and Task-number, the ChangeLog line (QUIP 17), licence
  headers and licenseRule.json, the Sanity Bot, a reviewer's own patch set, searching Gerrit for a file's changes and a
  QTBUG. Load it with upstream-outreach for a qtbase, qtdeclarative, qtmultimedia or qtwayland change, a plugin that
  cannot load its library (libMyStyle.so, RUNPATH, RPATH_SET could not write new RPATH), a style plugin fix, or a reply
  on codereview.qt-project.org.
---

# Contributing to Qt

**Check freshness first.**
Written on 2026-10-24.
The project's own contribution rules, read again before each round, win over this page.

Written on 2026-10-24 from Qt's contribution page (`https://contribute.qt-project.org/`, read 2026-10-24), the Qt Wiki Gerrit setup guide (`https://wiki.qt.io/Setting_up_Gerrit`, read 2026-10-24) and public changes 778399 and 778580 (read 2026-10-24).
Updated on 2026-11-02 from qtsvg's `CONTRIBUTING.md`, the Qt Community Code of Conduct ([QUIP 12](https://code.qt.io/cgit/meta/quips.git/tree/quip-0012-Code-of-Conduct.rst)), [QUIP 17](https://code.qt.io/cgit/meta/quips.git/tree/quip-0017-Change-log-creation.rst) and public change [785347](https://codereview.qt-project.org/c/qt/qtsvg/+/785347).
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is Qt's own practice.
Re-read the Gerrit setup guide and the active change before every round.

## The rules that come first
- **The Qt Community Code of Conduct (QUIP 12, active since 2018-10-24, adapted from KDE's):** consideration, respect, collaboration and pragmatism, in every Qt channel: Gerrit, the mailing lists, the forum, the wiki, meetings and private correspondence about the project.
  A Code of Conduct committee of at least three members answers reports of unacceptable behaviour.
- **Gerrit is the only route.** Every module's `CONTRIBUTING.md` says: "we cannot accept pull requests on GitHub". The repositories under github.com/qt are mirrors; qt/qtbase has never had a pull request.

## Where
- Changes are uploaded through Gerrit at `https://codereview.qt-project.org`, not through a Git hosting pull request.
- Name reviewers by their Gerrit username, not the email in their commits (one reviewer's commit address is not his account's, and the push was refused): look them up with REST `/a/accounts/?q=name:SURNAME&o=DETAILS`, then push `HEAD:refs/for/dev%r=USER1,r=USER2`.
- The `commit-msg` hook is served by Gerrit itself: `https://codereview.qt-project.org/tools/hooks/commit-msg`.
- Push a change to the project's `dev` branch with `git push ssh://USER@codereview.qt-project.org:29418/qt/REPO HEAD:refs/for/dev`.
- The Gerrit setup guide says to register the commit author email and click the confirmation email before contributing.
- The same guide says the commit email must match a registered email address.
- Accept the Qt Contribution Agreement in Gerrit before the first push.
- Install the `commit-msg` hook from `qtrepotools` so Gerrit receives the `Change-Id`; add that footer by hand if the hook is absent.
- For a release-series copy, upload the resolved cherry-pick to `refs/for/6.x`.

## The change
- Qt's contribution page says a `dev` push needs a `Pick-to:` footer when cherry-picking to another release branch.
- It also says the commit needs a `Task-number:` or `Fixes:` footer.
- The cherry-pick bot opens the backports named by `Pick-to:`.
- If a bot-opened backport conflicts, resolve it in the source tree, upload it as a new patch set to that backport with its original `Change-Id`, and post `cpbot: retry` on the change.
- Before amending, fetch every patch set; a reviewer may have uploaded the latest set, and their work must not be pushed over or lost.
- Update the same Gerrit change with a new patch set and the original `Change-Id`.
- **The ChangeLog line (QUIP 17):** `[ChangeLog][module][class/topic] text`, but the module tag only where the repository holds several modules. In qtsvg the sanity bot calls `[ChangeLog][QtSvg]` a "Redundant repository reference"; write `[ChangeLog][QSvgRenderer]`.
- **Every new file carries the SPDX line `licenseRule.json` gives its path,** data files such as `.inc` included: under `src/` `LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`, under `tests/` `LicenseRef-Qt-Commercial OR GPL-3.0-only`, build files `BSD-3-Clause`.
- Commit message lines at most 72 characters, ChangeLog line included.
- A file that names a generator outside Qt's tree is a question for reviewers: say what the data comes from (for example, the specification's own sample code) instead.
- QtSecurityBot marks changes to parser files, such as qtsvg's handlers, as "Qt-Security change" and comments "Modifying security sensitive file"; that is a notice, not a rejection.

## Tests
- In public change 778399, the Qt Sanity Bot first reported that omission of `6.12` from cherry-pick targets was probably incorrect.
- In 778399, the reviewer parameterized the backend test to increase coverage and the author answered the exact line suggestion.
- In 778399, the reviewer asked for use cases in `https://bugreports.qt.io` when test scope changed.
- The Qt CI Bot and Qt Sanity Bot participate in the change and verify it before merge.
- Run the affected module's targeted tests, upload the change, and monitor its bot and manual review results.

## Public record
- Public change 778399, FFmpeg backend display peak reporting, was merged on `dev` on 2026-10-08.
- Public change 778580, FFmpeg backend display peak reporting copied for `6.12`, was merged on 2026-10-09.
- In 778399, the reviewer uploaded a later patch set that parameterized the test for broader coverage.
- Public change 785347, Qt SVG reading every CSS colour and painting it at the target's precision, was uploaded to `dev` on 2026-11-02.

## AI policy
- Qt's contribution page and Gerrit setup guide state no project-wide rule for AI assistance, AI-generated code or LLM use (checked 2026-10-24, and the contribution page again on 2026-11-02).
- On 2026-10-24, I checked the contribution page and `https://wiki.qt.io/Setting_up_Gerrit`; those public documents are the project's contribution instructions.
- In public change 778399, review and service accounts did not raise AI assistance or reject the change for it.
- Declare AI assistance only when the module's current review instructions or assigned reviewers require it.

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (4 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
