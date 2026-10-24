---
name: contrib-vlc
description: >-
  Contribute to VLC on code.videolan.org with focused module changes and
  reproducible playback evidence. Load with upstream-outreach before a VLC merge
  request.
metadata:
  requires-packages: vlc
---

# Contributing to VLC

Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this is VLC's own practice.
Re-read the GitLab project's guidance and any current module review before proposing it.

## Where
- Merge requests are https://code.videolan.org/videolan/vlc/-/merge_requests.
- GitLab review is the public conversation surface.
- One behavior belongs to one merge request.
- Do not split review into another private channel.

## The change
- Rebase on the current default branch before a second review.
- Respect VLC's existing modules, interfaces and naming.
- Keep cleanup work and behavior separate.
- Explain the affected module, input path and expected declaration.

## Tests
- Build the target or module the project documents.
- Run the smallest playback path that reproduces the behavior.
- Record the input, module, expected output and the changed metadata.
- Do not extend a codec or platform claim beyond the path exercised.

## Public record
- Merge request [!10366](https://code.videolan.org/videolan/vlc/-/merge_requests/10366) is the edition's reviewed VLC record.
- The public review surface is the place to add evidence and follow-up.

## Replies
- Disclose AI assistance once in the merge-request description.
- Answer each point with code, command, input or log evidence.
- Thank reviewers for specific review work.
