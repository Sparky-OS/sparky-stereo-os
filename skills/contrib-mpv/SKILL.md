---
name: contrib-mpv
description: >-
  Contribute to mpv on GitHub with its 72-character commit rule, in-band stereo evidence and explicit AI disclosure policy.
metadata:
  requires-packages: mpv
---

# Contributing to mpv

Written on 2026-10-24 from `DOCS/contribute.md` (https://raw.githubusercontent.com/mpv-player/mpv/master/DOCS/contribute.md, read 2026-10-24) and public pull request #18490 (https://github.com/mpv-player/mpv/pull/18490, read 2026-10-24).
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is mpv's own practice.
Re-read `DOCS/contribute.md` in the current tree before every round.

## Where
- Use GitHub for code review and long-term discussion; IRC `#mpv` and `#mpv-devel` on Libera.Chat are the main development contacts.
- A change is a GitHub pull request or a plaintext patch from `git format-patch`.
- The contribution guide says "Plain diffs posted as pastebins are not acceptable!" and "Never send patches to any of the developers email addresses."
- Mark non-merge-ready work as `[RFC]` in the commit message or pull-request title.

## The change
- The guide says "Keep the pull request focused. Do one thing and do it fully."
- A commit subject has a subsystem prefix, for example `vo_gpu: ...`.
- The subject and every body line must stay at or under 72 characters.
- The first word after `:` is lower case and the subject does not end in a period.
- Describe the state with the patch in present tense and the state before it in past tense.
- Put an empty line between the subject and commit body.
- If an option, property or command is incompatible, add a `DOCS/interface-changes/*.txt` note whose content begins with `add`, `remove`, `deprecate`, `change` or another exact kind of change.
- The guide says "Fix the cause, not the symptom" and rejects checks, fallbacks or special cases that paper over a bug instead of removing it.
- New Apple framework code may use Swift; existing Objective-C may remain.

## Tests
- The guide says "Be sure to test your changes" and, if not tested, to say that in the commit message and pull-request text.
- For an upstream format or player-path bug, provide the smallest input and the stock commands that show the state before and after the patch.
- Pull request #18490 followed up that a frame-packing SEI arrives on FFmpeg keyframes only and loses `AV_FRAME_DATA_STEREO3D` when `fix_image_params()` runs on the next frame.
- The patch therefore persisted the in-band layout in mpv while the reviewer asked for the underlying persistence fix in FFmpeg's `ff_h2645_sei_to_frame()`.
- This exact state sequence is the model; a summary like "it plays stereo" is not.

## AI policy
- The guide permits AI or LLM use only if the result meets the same standard as any other contribution.
- It says to disclose the model and tool in the pull-request description or issue, not "an AI".
- It says "Do not put the disclosure, or any other mention of the LLM, in commit messages or code comments, and do not list it as a co-author."
- It says the contributor remains fully responsible and must be able to explain the patch and fix it when review finds a problem.
- It says "Relaying them to an LLM and pasting its answer back is not taking part in review."
- It says "Do not submit analysis or conclusions you did not reproduce and verify yourself" and that LLM output is a hypothesis until then.
- It says hidden, disguised or denied LLM involvement closes the pull request or issue immediately, without review.
- It says "Clearly vibe-coded patches will not be considered."

## Public record
- Pull request #18490 requested changes on 2026-09-21.
- Reviewer `kasper93` accepted the player-side idea but asked for the opaque-reference comment to be fixed.
- The reviewer reduced the second commit to `if (!m.stereo3d) m.stereo3d = p->codec->stereo_mode;`.
- The reviewer asked for the persistence fix in FFmpeg rather than a wider mpv backport.
- The reviewer also asked to trim the description and commit messages.
- On 2026-09-16, reviewer `llyyr` wrote that a contributor must show the ability to respond to review with human-written responses.
