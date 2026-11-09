---
name: contrib-vlc
description: >-
  Contribute a VLC change on code.videolan.org under VideoLAN's AI policy (the AI::Assisted, AI::Generated,
  AI::NotCompliant and AI::Slop labels) and code of conduct, through a merge request and vlc-devel. Load it with
  upstream-outreach for a VLC stereo, frame packing or video output change, a reply on a VideoLAN merge request, or a
  moderation question.
---

# Contributing to VLC

**Check freshness first.**
Written on 2026-10-24.
The project's own contribution rules, read again before each round, win over this page.

Written on 2026-10-24 from VideoLAN's AI policy (`https://code.videolan.org/videolan/vlc/-/raw/master/doc/VideoLAN_AI_Policy.md`, read 2026-10-24), the VideoLAN Code of Conduct page (`https://code.videolan.org/videolan/CODE_OF_CONDUCT/-/blob/main/CODE_OF_CONDUCT.md`, read 2026-10-24) and merge request !10366 (read 2026-10-24).
The rules that come first were checked again on 2026-11-02: the AI policy on master (added in 8a097e63 on 2026-10-21) and the Code of Conduct on the [VideoLAN wiki](https://wiki.videolan.org/Code_of_Conduct/) (last edited 2019-02-11), because the code.videolan.org page sat behind a bot check that day.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is VLC's own practice.
Re-read the active policy document and merge-request rules before every round.

## The rules that come first
- **The VideoLAN Code of Conduct** applies "to all means of communication, online and in real life", across VideoLAN's projects and channels.
  - No foul language, and "absolutely NO insults will be tolerated"; no ad hominem attacks, flaming or trolling; no spam; no abuse of administrative powers.
  - Criticism with care: focus on the possible improvements, do not make it personal, and "criticize in private, and praise publicly" where possible.
  - Do not undo someone else's contribution (wiki edits, code reverts) without asking first.
  - Communication in English; some lists, wiki pages and forum topics allow other languages when clearly flagged.
  - On the mailing lists: the proper list for the question, no quoting of private mail without agreement, no copy to the original poster unless asked, lines wrapped at 80 characters, no top-posting, no HTML-only mail, no attachments over 65 kB without moderation.
  - In the code repositories: no revert wars, no force-push that deletes another developer's commit, no insults in commits, and the project's commit log style.
  - A first violation brings a warning unless it is grave or deliberate; repeated ones may be escalated to the VideoLAN board and the general assembly.
- **The route:** a merge request on code.videolan.org (below), with public discussion and review kept there.
- **AI:** the VideoLAN AI Policy (`doc/VideoLAN_AI_Policy.md` in VLC's tree), which applies to every VideoLAN project that has not set a different, explicit rule; the clauses follow.

## Where
- Submit a change as a merge request on `https://code.videolan.org/videolan/vlc`.
- A new code.videolan.org account may stay gated until an administrator approves it.
- If registration is blocked, ask on the project's public `vlc-devel` channel; that path unblocked our account in September 2026.

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
- The policy's scope: "In this policy, AI means large language models (LLMs) and the tools built on them, such as chatbots, coding assistants, and agents."
- VideoLAN's policy says the contributor is responsible for all submitted code, commit messages, descriptions, comments and reports.
- It says "Read it. Test it. Understand it. Be ready to explain it."
- It says "Do not let an AI agent submit anything to VideoLAN for you, even with your approval."
- It says every merged line must be understood and vouched for by the submitting contributor, or the code is rejected.
- It says AI assistance used during coding must be disclosed in the merge request with the `AI::Assisted` label or a mention in the description.
- It says not to put this information in a commit message or credit an AI tool as a co-author.
- It says AI help with writing or translation is fine, provided descriptions, reports and comments stay precise and concise.
- It says project rules may differ from the VideoLAN policy, so re-check the policy before every merge request.
- It says "Bug reports and security reports must be investigated and verified by the person submitting them. Unverified AI-generated reports will be rejected."
- It says repeated violations "are handled by the board under our Code of Conduct and can lead to a ban".
- It explains the commit-message rule: "We do not want to advertise for any AI company."
- In the edition, Daniel submits to VideoLAN himself; no agent submits anything there, approved or not.

## Public record
- Public merge request !10366 has both `AI::Generated` and `AI::NotCompliant`.
- `AI::Slop` was renamed `AI::Generated` project-wide on 2026-09-23; that project's labels may evolve.
- The main session held !10366 until the review outcome and current policy are checked again.
