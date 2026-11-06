---
name: contrib-mplayer
description: >-
  Prepare an MPlayer patch for SVN and the mplayer-dev-eng list (DOCS/tech/patches.txt, svn diff, a [PATCH] subject,
  mp_msg) and hold every public post until Daniel says to send it. Load it with upstream-outreach for an MPlayer or
  MEncoder change, its stereo3d filter, or a frame packing SEI read.
---

# Contributing to MPlayer

Written from MPlayer's public patch guide, `https://www.mplayerhq.hu/MPlayer/DOCS/tech/patches.txt`, which served a bot challenge on 2026-10-24.
On 2026-11-02 it was plain text again (last changed 2010-11-07); the rules that come first were added that day from it and from the [mailing lists page](https://mplayerhq.hu/design7/mailing_lists.html).
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is MPlayer's eventual public practice.
Re-read the current SVN checkout, `DOCS/tech/patches.txt`, the mailing lists page and public `[PATCH]` threads before preparing anything.

## The rules that come first
- **MPlayer publishes no code of conduct.** Its mailing lists page sets the manners instead: "Before posting please learn and follow Netiquette" (RFC 1855); "HTML mail, top-posting and thread hijacking (posting unrelated messages as replies to existing threads) are forbidden".
  The lists are English-only unless they say otherwise, posting needs a subscription "due to spam problems", and big files go up for download rather than as attachments.
- **The route** (`DOCS/tech/patches.txt`): a unified diff (`svn diff`) against Subversion HEAD, made from the root of the tree, sent to mplayer-dev-eng as an attachment with the subject "[PATCH] very short description of the patch", as a new message.
  - Independent changes as separate patches in separate mails; logical units stay together.
  - Test it ("We'll *refuse* it if it breaks something") and read it: no indentation, tab or other cosmetic changes.
  - English comments where the code needs them, string operations always explained; documentation updated for new features and options; option names with '-'; console output through `mp_msg`, never `printf`.
  - Updates and reminders are replies to the original patch, each resending the complete patch.
  - Do not ask for Subversion write access at once; it comes after accepted patches.
- **AI:** neither the patch guide nor the mailing lists page states anything about AI assistance (checked 2026-11-02; on 2026-10-24, behind the bot challenge, the available tree metadata stated nothing either).
  Re-check `DOCS/tech/patches.txt`, developer guides and Trac metadata at the top of MPlayer's current tree before release.

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

## Public record
- No Sparky Stereo merge is public in MPlayer yet.
- This hold is a Sparky Stereo brief, not an upstream policy.

## Replies
- Before release, keep the eventual post to `mplayer-dev-eng` in Daniel's owner voice.
- After release, keep every technical claim tied to the same SVN revision, patch and media path.
