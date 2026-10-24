---
name: contrib-mplayer
description: >-
  Prepare an MPlayer patch on SVN and hold every public post until Daniel says
  to send it. Load with upstream-outreach for the eventual public process.
metadata:
  requires-packages: mplayer
---

# Contributing to MPlayer

Written from MPlayer's public patch guide, `https://www.mplayerhq.hu/MPlayer/DOCS/tech/patches.txt`, which now serves a bot challenge (checked 2026-10-24).
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is MPlayer's eventual public practice.
Re-read the current SVN checkout, `DOCS/tech/patches.txt` and public `[PATCH]` threads before preparing anything.

## Hold
- Do not send, post, publish, mail or expose a change anywhere public now.
- Do not ask a maintainer informally.
- Every public step waits for Daniel's explicit release instruction.

## Where
- MPlayer uses its public SVN history as the source state.
- `mplayer-dev-eng` is the public review list for `[PATCH]` threads.
- `DOCS/tech/patches.txt` is the in-tree copy of the patch guide.
- Public Trac is the issue surface.
- Check the repository's developer guide and README in the current tree before preparing the post.

## The change
- One patch carries one behavior; keep build fixes, interface changes and playback changes separate.
- Prepare the change against the current SVN checkout.
- Record the public symptom, the cause and the exact media path.
- Quote the project's own patch-guide clauses for subject shape and diff format before posting.
- Use the exact source revision in the patch; public SVN history is the state a reviewer can fetch.

## Tests
- Run the project's documented build command on the exact SVN revision.
- Run the affected playback path on that revision.
- Record the exact input, command, revision, old behavior and new behavior.
- Do not claim format support without exercising that format path.

## AI policy
- The current MPlayer patch guide serves a bot challenge, and the available current tree metadata states nothing about AI assistance.
- Re-check `DOCS/tech/patches.txt`, developer guides and Trac metadata at the top of MPlayer's current tree before release.
- This AI-policy line was checked on 2026-10-24.

## Public record
- No Sparky Stereo merge is public in MPlayer yet.
- This hold is a Sparky Stereo brief, not an upstream policy.

## Replies
- Before release, keep the eventual post to `mplayer-dev-eng` in Daniel's owner voice.
- After release, keep every technical claim tied to the same SVN revision, patch and media path.
