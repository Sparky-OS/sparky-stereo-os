---
name: contrib-ffmpeg
description: >-
  Contribute to FFmpeg on code.ffmpeg.org (Forgejo): the series shape, commit messages (area/sub: what it does, Fixes:,
  Signed-off-by, Assisted-by), squashing fixups and force-with-lease, FATE references and samples (tests/ref/fate,
  fate-samples, inject-pr-samples, THREADS), the review bot's verdicts (minor_issues_approve, moderate_issues), the CI
  logs, replies to reviewers and rebases after approval. Load it with upstream-outreach when a FATE reference differs
  after a rebase, fate-cbs-h264-metadata-sei changes, ffprobe shows no Stereo 3D side data, the bot or a reviewer asks
  for changes, a frame packing SEI or stereo3d patch needs a test, or a pull request waits on master.
---

# Contributing to FFmpeg

Written on 2026-10-23 from the edition's FFmpeg pull requests (#24628, #24643, #25377, #25378, #25380) and their reviews.
The rules that come first were added on 2026-11-02 from `CONTRIBUTING.md`, `doc/developer.texi`, `doc/community.texi` and `.forgejo/PULL_REQUEST_TEMPLATE.md` on master at [code.ffmpeg.org](https://code.ffmpeg.org/FFmpeg/FFmpeg), read that day.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first: it has the never-cold rule and the manners; this skill is FFmpeg's own practice.
Check freshness: re-read `CONTRIBUTING.md`, `doc/developer.texi` and `doc/community.texi` in the current tree before each round.

## The rules that come first
- **FFmpeg's Code of Conduct** (`doc/community.texi`, chapter "Code of Conduct") opens: "Be friendly and respectful towards others and third parties. Treat others the way you yourself want to be treated."
  It asks to be considerate of other viewpoints, not to assume malice ("Do not assume malice for things that can be attributed to incompetence"), to stay friendly when someone does not, to take a break before answering in anger, to help and cooperate, and to give someone who struggles "a helping hand instead".
  It ends: "Be excellent to each other."
- **The Community Committee** enforces it (`doc/community.texi`): five members elected by the General Assembly for a year, who arbitrate interpersonal conflicts and can remove commit access or ban someone from the community for a time.
- **The route:** pull requests on code.ffmpeg.org or patches on the ffmpeg-devel list (below).
  `CONTRIBUTING.md`: "Github pull requests should be avoided because they are not part of our review process and **will be ignored**."
- **AI:** FFmpeg's documents state no rule on AI-assisted contributions (`CONTRIBUTING.md`, `doc/developer.texi` and `doc/community.texi`, checked 2026-11-02).
  Their one mention is the review bot, in `doc/developer.texi`, "Reviews": "If you want an LLM-based review, add Forgejo Fairy as a reviewer to your pull request."
  The edition discloses its assistance once, in the pull request description, and in the `Assisted-by:` trailer (below).

## Where
- Pull requests on https://code.ffmpeg.org (Forgejo); the ffmpeg-devel list also takes patches.
- One logical change per pull request. A bug found while reviewing, which predates the series, is its own patch and its own pull request, never folded in.
- Rebase on current master before asking for another review, and push with `--force-with-lease` against the head the reviewers saw.

## The series
- **Squash fixups before pushing.** No commit may introduce a defect that a later commit repairs; the review bot flags it. Keep a fixup branch locally if it helps you, but the pull request carries the squashed commits (`git rebase -i --autosquash`).
- Each commit builds and passes its own tests on its own.
- After squashing, rewrite the message to describe what the commit does now, not what it did before the review.

## Commit messages
- Subject `area/sub: what it does`, imperative (`avcodec/vvc: keep the current picture after an output error`).
- Body: the problem, the change, the proof, wrapped at 72 characters per line except code, URLs and trailers. FFmpeg's `doc/git-howto.texi`, "Writing a commit message": "These details should not exceed 60-72 characters per line, except when containing code." Our one-sentence-per-line style is for our own documents, never for an FFmpeg commit (a reviewer asked for the wrap on #25398, 2026-10-24).
- Trailers in one block at the end, no blank line between them: `Fixes: #NNNNN` first when an issue tracks the bug (master uses this form, for example 5fd305b8f42), then `Signed-off-by:`, then `Assisted-by:` for AI assistance. A trailer separated by a blank line is not parsed as a trailer.

## Tests (FATE)
- Expected results live in `tests/ref/fate/...`; the test prints what it observes and FATE compares. Never hard-code expectations in C constants.
- A new test fails on unpatched master and passes with the change; run the full applicable FATE with GCC and clang and report both totals.
- The test goes in its own commit, after the fix, so every commit passes FATE and the fix can be backported alone. A maintainer asked for this on #25398 (2026-10-24: "Please do not mix tests and fixes in the same commit"). It is not written in `doc/developer.texi`; the nearest text is "Bug fixes intended for backporting should stay focused".
- New samples go to the fate-suite through someone with samples access.
  Attach them to the pull request (small, generated, no outside media, with how they were made), each named as the sample, list their paths relative to the fate-suite root in the template's `fate-samples` block, and ask in a comment.
  Since 2026-05-27 the pull request's CI copies the listed attachments into its own fate-suite (`.forgejo/inject-pr-samples.py`, run by `test.yml`), so the new tests run there before the samples are uploaded.

## The review bot
- A review bot (Forgejo_Fairy) reviews pull requests and classifies them (for example `minor_issues_approve`, `moderate_issues`). Mentioning it in a comment asks it to review again.
- Answer it point by point, like any reviewer: fixed (the commit), shown correct (the evidence: code path, clause, probe), or outside this pull request (a separate patch).

## CI
- Infrastructure failures happen (the win64 job's rsync of the fate-suite was refused once); show the log line and ask a maintainer to re-run, since only maintainers can.
- Actions logs: `/actions/runs/N/jobs/J/attempt/1/logs` on the pull request's repository.

## Replies
- Disclose AI assistance once, in the pull request description; the replies in the thread do not repeat it.
- Short, one point per line, every claim with its commit, test or clause; thank reviewers by name for what they actually did.

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (9 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
