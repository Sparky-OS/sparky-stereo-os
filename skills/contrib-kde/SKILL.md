---
name: contrib-kde
description: >-
  Contribute KDE fixes on Invent and bugs.kde.org with linked bug reports, module
  ownership and KDE tests. Load with upstream-outreach before a change.
metadata:
  requires-packages: kde-cli-tools | plasma-desktop
---

# Contributing to KDE

Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this is KDE's own practice.
Re-read the relevant Invent repository's contribution rules and Bugzilla workflow before work.
This skill uses KDE's own records read on 2026-10-24, not generic commit hygiene.

## Where
- Bugs are https://bugs.kde.org; code is https://invent.kde.org.
- Invent merge requests and Bugzilla are the public review surfaces.
- One behavior belongs to one merge request.
- Link the merge request to a clear public bug report.
- Always push from a full clone; Invent refuses a shallow push with "shallow update not allowed".

## The change
- Rebase on the current target branch before another review.
- KWin documents the subject style `component/subcomponent: Do a thing` as a convention, not a hard rule.
- Do not invent a branch named `main`; Invent's pre-receive hook rejects it and KDE uses `master`.
- A reference dependency branch fails dependency resolution before compiling ("Package ... was not found in branch ..."), so push reference branches such as `stereo3d-6.7` with `git push -o ci.skip`.
- Work for an ordinary merge request belongs on a master-based branch, which KDE CI can resolve.
- Keep framework cleanup apart from behavior.
- State the bug, the affected component, the cause and the proof.
- The pre-receive audit rejects any commit touching `po/`.
- Translated `Name[xx]=` and `Comment[xx]=` lines in `.desktop` and `.notifyrc` files count as translations too.
- Translations go through KDE's translation teams, not through a code merge request.

## Tests
- Use the tested component pattern from the module rather than inventing a parallel system.
- Add a regression when the module has the fixture and framework for it.
- Record the test or user-path command, the failure and the passing result.
- Do not claim a platform or theme works without exercising that combination.
- KWin expects tests for substantial new code and appreciates but does not require a regression on every bug fix.

## Public record
- Work item [324](https://invent.kde.org/plasma/kwin/-/work_items/324) says KWin requires all communication to be 100% human written and closes clearly LLM-generated merge requests on sight.
- [`kdeplasma-addons` merge request](https://invent.kde.org/plasma/kdeplasma-addons/-/merge_requests/17) has a maintainer comment from 2026-10-13 that "copy-pasting text from LLMs is strongly discouraged in KDE".
- Krita's README, checked on 2026-10-24, contains an AI moratorium.
- This Week in Plasma takes merged changes only and enters through a commit to an open merge request in `websites/blogs-kde-org` carrying the label `This Week in Plasma`, credited as "(Name, repo MR #n)".

## AI policy
- KDE has no adopted project-wide AI policy as of these records; module policies differ, including KWin's and Krita's bans.
- Check the target repository before any merge request; where it bans AI text, write the contributor's own words.

## Replies
- Follow each maintainer's preferred review style in that module.
- Answer reviewers with the test, component path or log that proves it.
