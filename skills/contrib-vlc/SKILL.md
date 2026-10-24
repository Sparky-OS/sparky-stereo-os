---
name: contrib-vlc
description: >-
  Contribute a VLC change on code.videolan.org under VideoLAN's AI policy and public moderation.
metadata:
  requires-packages: vlc
---

# Contributing to VLC

Written on 2026-10-24 from VideoLAN's AI policy (`https://code.videolan.org/videolan/vlc/-/raw/master/doc/VideoLAN_AI_Policy.md`, read 2026-10-24), the VideoLAN Code of Conduct page (`https://code.videolan.org/videolan/CODE_OF_CONDUCT/-/blob/main/CODE_OF_CONDUCT.md`, read 2026-10-24) and merge request !10366 (read 2026-10-24).
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is VLC's own practice.
Re-read the active policy document and merge-request rules before every round.

## Where
- Submit a change as a merge request on `https://code.videolan.org/videolan/vlc`.
- A new code.videolan.org account may stay gated until an administrator approves it.
- If registration is blocked, ask on the project's public `vlc-devel` channel; that path unblocked our account in September 2026.
- The VideoLAN Code of Conduct applies to every project channel.

## The change
- Keep the change focused on one VLC behavior or format path.
- Include the input, the resulting path, and any format or signalling evidence in the merge-request description.
- Keep public discussion and review replies in the merge request.
- Do not send private review requests or route review outside the project's channels.

## Tests
- Run the VLC build before submitting the merge request.
- Exercise the affected demuxing, decoding, output or VLC feature through the binary.
- Record the exact input, command, old result and new result.
- Public merge request !10366 carries a video-player stereo metadata change in addition to its policy evidence.

## AI policy
- VideoLAN's policy says the contributor is responsible for all submitted code, commit messages, descriptions, comments and reports.
- It says "Read it. Test it. Understand it. Be ready to explain it."
- It says "Do not let an AI agent submit anything to VideoLAN for you, even with your approval."
- It says every merged line must be understood and vouched for by the submitting contributor, or the code is rejected.
- It says AI assistance used during coding must be disclosed in the merge request with the `AI::Assisted` label or a mention in the description.
- It says not to put this information in a commit message or credit an AI tool as a co-author.
- It says AI help with writing or translation is fine, provided descriptions, reports and comments stay precise and concise.
- It says project rules may differ from the VideoLAN policy, so re-check the policy before every merge request.

## Public record
- Public merge request !10366 has both `AI::Generated` and `AI::NotCompliant`.
- `AI::Slop` was renamed `AI::Generated` project-wide on 2026-09-23; that project's labels may evolve.
- The main session held !10366 until the review outcome and current policy are checked again.
