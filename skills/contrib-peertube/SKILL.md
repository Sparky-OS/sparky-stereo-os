---
name: contrib-peertube
description: >-
  Contribute to PeerTube on GitHub with its project guide, server or plugin
  boundaries and concrete transcoding evidence. Load with upstream-outreach
  before a pull request.
metadata:
  requires-packages: nodejs | npm
---

# Contributing to PeerTube

Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this is PeerTube's own practice.
Re-read the public project guidance and pull-request template before the change.

## Where
- Pull requests are https://github.com/Chocobozzz/PeerTube.
- Keep review and implementation discussion in the pull request.
- One behavior belongs to one pull request.
- Follow the template's scope and test fields.

## The change
- Rebase on the current default branch before a second review.
- Respect the server, plugin and UI boundaries.
- Describe the user-visible effect, the affected stage and the proof.
- Keep dependency updates, docs and behavior separate unless the project asks otherwise.

## Tests
- Run the project's documented API, UI and transcoding checks.
- Record a small input video, the transcoding invocation and the resulting stream metadata.
- Verify the declared layout survives the intended path.
- State what UI, API and server path was not exercised.

## Public record
- Merged pull request [#7816](https://github.com/Chocobozzz/PeerTube/pull/7816) shows the maintainer reshaping a contribution into an existing transcoding profile.
- Treat project-specific reshaping as collaboration, not rejection.

## Replies
- Disclose AI assistance once in the pull-request description.
- Respond point by point and thank the reviewer for the specific work.
