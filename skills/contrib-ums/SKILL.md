---
name: contrib-ums
description: >-
  Contribute to Universal Media Server under its three accepted checks, Java
  style gate and device-level proof. Load with upstream-outreach before a UMS
  pull request.
metadata:
  requires-packages: default-jre
---

# Contributing to Universal Media Server

Written on 2026-10-24 from Universal Media Server's `CONTRIBUTING.md`, `STYLEGUIDE.md`, pull-request template and public pull requests [#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330) and [#6389](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6389).
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is Universal Media Server's own practice.
Re-read those files in the current `master` tree before every round.

## Merge decisions
- `CONTRIBUTING.md` says the project will merge changes only if they do not break automated tests.
- It adds a second condition: "code review by one of our developers".
- It adds a third condition: manual testing.
- It also says to "please try to use the code conventions we use".
- Plan the description so a reviewer can perform all three checks.

## The pull request
- Use the template's three-part checklist: description, every relevant issue linked, and every relevant Knowledge Base article written or modified.
- The same checklist requires relevant tests to be written or modified.
- Keep renderer profile and Knowledge Base changes in one pull request only when the profile adds the documented article the template asks for.
- `STYLEGUIDE.md` says to follow the Google Java Style Guide with block K&R style.
- When resolving conflicts, `STYLEGUIDE.md` says "We prefer pulling" into the branch.
- It explains that merge commits make conflict history easier to inspect than strategies that rewrite history.

## Device and media proof
- Run the automated build and tests on the changed code.
- Exercise the exact affected renderer profile and media path by hand.
- Record the profile, client, exact input, command or configuration, old behaviour and new behaviour.
- Do not claim a device works without testing that device or a demonstrably equivalent public profile.

## AI policy
- Universal Media Server's `CONTRIBUTING.md`, `STYLEGUIDE.md` and pull-request template state nothing about AI assistance.
- All three files were checked on 2026-10-24.

## Public record
- Public pull request [#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330) was a focused renderer and media-fix change.
- Public pull request [#6389](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6389) was a focused media declaration change.
- The reviewer asked for 3D test files on [#6389](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6389).
- Treat that request as evidence that device and file-level proof matter for stereo changes.

## Replies
- Answer each review point with the automated result, code-review note or manual check that resolves it.
- Thank the reviewer for the specific review work.
