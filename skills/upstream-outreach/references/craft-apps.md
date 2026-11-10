# Craft Apps: contributions and review follow-through

Checked 2026-11-10 against [craft-contrib](https://github.com/storytold/craft-contrib), revision cb0d67e, and the app repositories' current rules.
Read the receiving repository again before preparing a submission: the suite changes quickly.

## Working recipe

1. Read the app's `AGENTS.md`, its `CLAUDE.md` if present, the contribution files, `.coderabbit.yaml` and the called shared CI workflow.
   The core and Rust blocks come from `craft-contrib/standards/house-rules-{core,rust}.md`; local rules can be stricter.
   `craft-skills` at 2a55dce contains only its README, so it does not supply missing instructions.
2. Read the issue and every review, then search recent main, open and merged PRs for the issue and symptom.
   Keep a small table of actionable requests, the correcting commit or measured explanation, and any decision reserved to a maintainer.
   Verify a bot finding against the actual code; its suggestion is review data.
3. Restore/rebase on an explicitly recorded main revision, keep the project's module layout and tests, and run its own gate before claiming success.
   Native apps use Rust and retain their web build.
   CI belongs to `craft-common-actions`; a feature PR does not rewrite workflows.
4. Preserve the dual MIT OR Apache-2.0 licence and third-party notices.
   Check the current SPDX allowlist before adding a dependency or asset; record original/licensed assets in `ATTRIBUTION.md` with their sidecars.
   Fonts belong in `craft-fonts`.
   Edit only the contributor's own chosen credit entry; never infer another person's name or edit generated contributor statistics.
5. Prepare a short description: the concrete change, exact validation and remaining platform gaps.
   Run bots' actionable findings as regressions where they are correct.
   A static bot review is not a build or a passing gate.
6. Keep the review moving: the current core rule asks for an answer within seven days, a reminder at fourteen, and maintainer-decided closure eligibility at thirty days after actionable feedback waits on the author.
   A fix, explanation or agreed plan resets the clock; unrelated activity does not.
   Waiting on the maintainer pauses it; unconfirmed bot suggestions do not start it.
   Reuse searches and stop at a rate limit.

## The closure that exposed the gap

PhotoCraft [#7818](https://github.com/storytold/photocraft/pull/7818) was closed on 2026-11-05 after the author left FredApps' 2026-10-19 requested changes unanswered for over two weeks.
The maintainer invited a current-main rebase and a reopened or fresh PR.
That historical closure is not today's thirty-day rule.
FredApps corrected his own point 2: PNG normalization remains a maintainer decision; he withdrew the claim that the cited issue promised unchanged stored pixels.
Preserve the correction when answering the review.

The two CodeRabbit findings were truncated MPO entries silently losing damage reporting and Duotone stereo exports bypassing ink rendering.
Confirm each against the submitted head, then cite the fixing commit and a regression, or explain with measured evidence why it no longer applies.

## Disclosure conflict to resolve before sending

Current craft-contrib core rule 15 says a pull request does not say an agent wrote it.
The edition's policy asks for disclosure once, and a task may explicitly require it in a fresh PR.
Record the conflict and the responsible person's explicit instruction in the private handoff; do not quietly rewrite either project's rules or misrepresent what they require.
A local draft is not authorization to send.
