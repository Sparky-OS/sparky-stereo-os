---
name: contrib-mpv
description: >-
  Contribute to mpv on GitHub with small playback changes, commit prefixes and
  reproducible replay evidence. Load with upstream-outreach before a pull
  request.
metadata:
  requires-packages: mpv
---

# Contributing to mpv

Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this is mpv's own practice.
Re-read the public contribution guidance and the active review thread before each round.

## Where
- Pull requests are https://github.com/mpv-player/mpv.
- Keep diagnosis, review and follow-up on GitHub.
- One behavior belongs to one pull request.
- Do not replace a public diff with a private message or a short-lived paste.

## The change
- Rebase on the current default branch before another review.
- Keep the first description focused on symptom, cause and proof.
- Move necessary context into the commit body rather than into a long comment.
- Make each commit build and behave by itself.

## Tests
- Run the exact command path that a user would run.
- Prefer the smallest clip or option sequence that reproduces the condition.
- Record the expected result, the pre-patch failure and the post-patch result.
- Say plainly what remains untested or cannot be exercised locally.

## Public record
- Merged pull request [#18490](https://github.com/mpv-player/mpv/pull/18490) shows focused GitHub review and a careful reviewer follow-up.
- The accepted practice is to answer code behavior with a specific path and output.

## Replies
- Disclose AI assistance once in the pull-request description.
- Answer each point with the command, code location or log that proves it.
- Thank reviewers by name for what they actually caught or improved.
