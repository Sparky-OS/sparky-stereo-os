---
name: contrib-mplayer
description: >-
  Prepare an MPlayer patch on SVN and hold every public post until Daniel says
  to send it. Load with upstream-outreach for the eventual public process.
metadata:
  requires-packages: mplayer
---

# Contributing to MPlayer

Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this is MPlayer's eventual public practice.
Re-read the current SVN history and public `[PATCH]` threads before preparing anything.

## Hold
- Do not send, post, publish, mail or expose a change anywhere public now.
- Do not ask a maintainer informally.
- Every public step waits for Daniel's explicit release instruction.

## Where
- MPlayer uses its public SVN history as the current source state.
- `mplayer-dev-eng` is the public review list for `[PATCH]` threads.
- Public Trac is the issue surface.
- No private channel is a substitute for the eventual public path.

## The change
- Keep one behavior in one patch.
- Prepare the change against a current SVN checkout.
- Record the public symptom, the cause and the exact media path.
- Keep build cleanup, interface changes and behavior separate.

## Tests
- Run the project's documented build command and the affected playback path.
- Report the exact input, command, old behavior and new behavior.
- Do not claim format support without exercising the format.

## Replies
- Disclose AI assistance in the eventual `[PATCH]` or issue text.
- Answer every future reviewer point with evidence from the patch.
