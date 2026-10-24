---
name: contrib-qt
description: >-
  Contribute a Qt module change through Gerrit with the CLA, verified author email, dev branch push and public review history.
metadata:
  requires-packages: qt6-base-dev
---

# Contributing to Qt

Written on 2026-10-24 from Qt's contribution page (`https://contribute.qt-project.org/`, read 2026-10-24), the Qt Wiki Gerrit setup guide (`https://wiki.qt.io/Setting_up_Gerrit`, read 2026-10-24) and public changes 778399 and 778580 (read 2026-10-24).
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is Qt's own practice.
Re-read the Gerrit setup guide and the active change before every round.

## Where
- Changes are uploaded through Gerrit at `https://codereview.qt-project.org`, not through a Git hosting pull request.
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

## AI policy
- Qt's contribution page and Gerrit setup guide state no project-wide rule for AI assistance, AI-generated code or LLM use (checked 2026-10-24).
- On 2026-10-24, I checked the contribution page and `https://wiki.qt.io/Setting_up_Gerrit`; those public documents are the project's contribution instructions.
- In public change 778399, review and service accounts did not raise AI assistance or reject the change for it.
- Declare AI assistance only when the module's current review instructions or assigned reviewers require it.
