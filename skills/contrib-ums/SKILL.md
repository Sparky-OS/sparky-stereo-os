---
name: contrib-ums
description: >-
  Contribute to Universal Media Server on GitHub with its contribution and style
  guides plus device-level proof. Load with upstream-outreach before a UMS pull
  request.
metadata:
  requires-packages: default-jre
---

# Contributing to Universal Media Server

Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this is Universal Media Server's own practice.
Re-read `CONTRIBUTING.md`, the style guide and the active pull request before work.

## Where
- Pull requests are on the project's public GitHub repository.
- Public review is the expected conversation surface.
- One behavior belongs to one pull request.
- Do not send private review mail.

## The change
- Rebase on the current default branch before another review.
- Separate dependency changes, profile work and behavior.
- Describe the symptom, the media path and the result in the description.
- Preserve the project's Java naming, logging and formatting habits.

## Tests
- Run the project's documented automated tests and build path.
- Exercise the affected transcoding or rendering path manually.
- Record the profile, device or client behavior as well as the automated result.
- Do not claim a device works without checking that device or the exact public profile.

## Public record
- Merged pull request [#6330](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6330) shows a direct merged behavior fix and later release.
- Merged pull request [#6389](https://github.com/UniversalMediaServer/UniversalMediaServer/pull/6389) shows another focused media declaration fix.

## Replies
- Disclose AI assistance once in the pull-request description.
- Answer every review point with the test, log or device check.
- Thank reviewers for the specific review work.
