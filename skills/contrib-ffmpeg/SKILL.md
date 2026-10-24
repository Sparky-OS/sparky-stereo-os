---
name: contrib-ffmpeg
description: >-
  Contribute to FFmpeg on code.ffmpeg.org: series shape, commit messages and trailers, FATE references and samples,
  the review bot, CI and replies. Load with upstream-outreach when sending or answering an FFmpeg pull request.
metadata:
  requires-packages: libavcodec-dev | libavformat-dev | libavfilter-dev | libavutil-dev
---

# Contributing to FFmpeg

Written on 2026-10-23 from the edition's FFmpeg pull requests (#24628, #24643, #25377, #25378, #25380) and their reviews.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first: it has the never-cold rule and the manners; this skill is FFmpeg's own practice.
Check freshness: re-read `CONTRIBUTING.md` and `doc/developer.texi` in the current tree before each round.

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
- New samples go to the fate-suite through someone with samples access. Attach them to the pull request (small, generated, no outside media, with how they were made) and ask in a comment; until then the new test entries cannot run upstream.

## The review bot
- A review bot (Forgejo_Fairy) reviews pull requests and classifies them (for example `minor_issues_approve`, `moderate_issues`). Mentioning it in a comment asks it to review again.
- Answer it point by point, like any reviewer: fixed (the commit), shown correct (the evidence: code path, clause, probe), or outside this pull request (a separate patch).

## CI
- Infrastructure failures happen (the win64 job's rsync of the fate-suite was refused once); show the log line and ask a maintainer to re-run, since only maintainers can.
- Actions logs: `/actions/runs/N/jobs/J/attempt/1/logs` on the pull request's repository.

## Replies
- Disclose AI assistance once, in the pull request description; the replies in the thread do not repeat it.
- Short, one point per line, every claim with its commit, test or clause; thank reviewers by name for what they actually did.
