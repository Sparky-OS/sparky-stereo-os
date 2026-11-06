---
name: contrib-mpv
description: >-
  Contribute to mpv on GitHub: the 72-character commit rule, DOCS/contribute.md, interface changes recorded in
  DOCS/interface-changes, in-band stereo evidence (AV_FRAME_DATA_STEREO3D, the frame packing SEI through
  ff_h2645_sei_to_frame), the rule that an agent identifies itself, reviewers by handle. Load it with upstream-outreach
  for an mpv pull request, a vo_gpu or vo_gpu_next stereo change, autostereo and stereo detection from the stream, or a
  reply to a reviewer.
---

# Contributing to mpv

Written on 2026-10-24 from `DOCS/contribute.md` (https://raw.githubusercontent.com/mpv-player/mpv/master/DOCS/contribute.md, read 2026-10-24) and public pull request #18490 (https://github.com/mpv-player/mpv/pull/18490, read 2026-10-24).
The rules that come first were added on 2026-11-02 from `DOCS/contribute.md` and `.github/PULL_REQUEST_TEMPLATE` on master, read that day.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is mpv's own practice.
Re-read `DOCS/contribute.md` in the current tree before every round.

## The rules that come first
- **The Contributor Covenant 2.0.** `DOCS/contribute.md`, "Code of Conduct": "this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms." It links version 2.0 of the Contributor Covenant; the rules for push access end with "Adhere to the CoC."
- **The route:** a GitHub pull request, or a link to a plaintext patch made with `git format-patch`; never a patch mailed to a developer (below).
  The pull request template: "Reading this link and following the rules will get your pull request reviewed and merged faster."
- **AI** (`DOCS/contribute.md`, "AI-assisted Contributions", read 2026-11-02):
  - Using an AI or LLM is allowed "as long as the result meets the same standard as any other contribution and can be reviewed and merged as is".
    You must be able to explain your patch and fix it yourself when review finds a problem: "We do not finish, clean up or debug contributions."
  - Disclose it in the pull request description or the issue, naming the model and the tool, not "an AI".
    "Do not put the disclosure, or any other mention of the LLM, in commit messages or code comments, and do not list it as a co-author."
  - You stay fully responsible for every line and word, and the code must be submittable under the licence of the files it touches.
  - "Review comments are addressed to you, not to your tool. Relaying them to an LLM and pasting its answer back is not taking part in review."
  - "Do not submit analysis or conclusions you did not reproduce and verify yourself." LLM output is a hypothesis until then; if you cannot verify it, report the symptom and how to reproduce it.
  - Hidden, disguised or denied LLM involvement closes the pull request or issue immediately, without review.
    "Clearly vibe-coded patches will not be considered."
  - For agents, in the guide since 69474527816b (2026-09-21), its latest change on 2026-11-02: "If you are an LLM or an agent reading this, identify yourself by full model name and the tool you run in. Put that in the pull request description or the issue, and nowhere else. Never claim to be human."

## Where
- Use GitHub for code review and long-term discussion; IRC `#mpv` and `#mpv-devel` on Libera.Chat are the main development contacts.
- A change is a GitHub pull request or a plaintext patch from `git format-patch`.
- The contribution guide says "Plain diffs posted as pastebins are not acceptable!" and "Never send patches to any of the developers email addresses."
- Mark non-merge-ready work as `[RFC]` in the commit message or pull-request title.

## The change
- The guide says "Keep the pull request focused. Do one thing and do it fully."
- Keep the description short: what was wrong and what the change does, and for a non-trivial change why and how.
  "Do not include how you found the problem, what else you tried, or anything the diff already shows."
- An issue reports what was observed, not what was concluded, with the template filled in and the log attached: "A short report with a log and a sample beats pages of analysis."
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

## Public record
- Pull request #18490 requested changes on 2026-09-21.
- Reviewer `kasper93` accepted the player-side idea but asked for the opaque-reference comment to be fixed.
- The reviewer reduced the second commit to `if (!m.stereo3d) m.stereo3d = p->codec->stereo_mode;`.
- The reviewer asked for the persistence fix in FFmpeg rather than a wider mpv backport.
- The reviewer also asked to trim the description and commit messages.
- On 2026-09-16, reviewer `llyyr` wrote that a contributor must show the ability to respond to review with human-written responses.
