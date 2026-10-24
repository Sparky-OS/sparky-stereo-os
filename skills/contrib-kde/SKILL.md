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

## Where
- Bugs are https://bugs.kde.org; code is https://invent.kde.org.
- Invent merge requests and Bugzilla are the public review surfaces.
- One behavior belongs to one merge request.
- Link the merge request to a clear public bug report.

## The change
- Rebase on the current target branch before another review.
- Respect module boundaries and each repository's maintainer expectations.
- Keep framework cleanup apart from behavior.
- State the bug, the affected component, the cause and the proof.

## Tests
- Use the tested component pattern from the module rather than inventing a parallel system.
- Add a regression when the module has the fixture and framework for it.
- Record the test or user-path command, the failure and the passing result.
- Do not claim a platform or theme works without exercising that combination.

## Public record
- Invent merge request review is the accepted channel for component changes.
- Bugzilla is the accepted place for reproducibility and affected versions.

## Never
- Do not change `po/` files in a code change.
- Translations go through their own project process and owners.

## Replies
- Disclose AI assistance once in the merge-request description.
- Follow each maintainer's preferred review style in that module.
- Answer reviewers with the test, component path or log that proves it.
