---
name: contrib-qt
description: >-
  Contribute to Qt through Gerrit with coordinated changes, Qt Test regressions
  and public CI follow-up. Load with upstream-outreach before a Qt change.
metadata:
  requires-packages: qt6-base-dev | qt6-multimedia-dev
---

# Contributing to Qt

Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this is Qt's own practice.
Re-read the current Qt contribution guide and Gerrit project rules before uploading.

## Where
- Changes are on https://codereview.qt-project.org.
- Gerrit's review thread is the public review surface.
- A cross-module behavior is coordinated through related changes, not one sprawling change.
- Do not move discussion to private mail.

## The change
- Rebase on the target branch before uploading or pushing again.
- Keep the description about the symptom, the API promise and the proof.
- Separate an unrelated build cleanup from the behavior.
- Preserve the project's coding and commit conventions.

## Tests
- Add a Qt Test regression before the fix when possible.
- Make the regression fail on the unpatched code and pass with the fix.
- Prefer data-driven columns when several inputs share the same path.
- Commit the test with the fix; do not promise a later test.

## Public record
- Change [778399](https://codereview.qt-project.org/c/qt/qtmultimedia/+/778399) shows review by the Qt Multimedia maintainer.
- Companion change [778580](https://codereview.qt-project.org/c/qt/qtmultimedia/+/778580) shows a coordinated branch backport.

## Replies
- Disclose AI assistance once in the Gerrit change.
- Address every reviewer point and mark the resolved state in Gerrit.
- Thank reviewers by name for specific review work.
