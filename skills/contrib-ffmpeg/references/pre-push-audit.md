# The audit before a push to an FFmpeg pull request

Written on 2026-11-12 by ORDER 530, after the review bot found on #25395 a test helper that compared its result with constants and called `exit(1)`, which [the skill](../SKILL.md#tests-fate) had forbidden since October.
The rule was known and nobody had looked for it in the diff: FATE passes on such a helper, so running the tests does not find it.
Walk this list against the series before the tests are rerun, by the lane that hands the series back and again by the reviewer who pushes it.
Every rule has the search that finds a breach; write the result of each in the hand-back, with "checked: how".

`BASE` is the commit the series starts from, `T` the test program, `C` each commit of `git rev-list --reverse BASE..HEAD`.

## A series

1. **One logical change per pull request; an older bug is its own patch.**
   `git diff --stat BASE..HEAD`: every file belongs to the change the title names. A finding the reviewer marks "pre-existing" is answered "outside this pull request" and listed for its own patch.
2. **Rebased on current master.**
   `git fetch up master && git log --oneline HEAD..up/master -- $(git diff --name-only BASE..HEAD)`: the commits on the touched files since the base. None: say so. Some: rebase and rerun everything.
3. **No commit repairs an earlier one.**
   `git log --format='%h %s' BASE..HEAD` has no `fixup!`, and no hunk of a later commit changes a line that an earlier commit of the series added for the same purpose: `git range-diff` against the head the reviewers saw shows where each change went.
4. **Each commit builds and passes its own tests alone.**
   Check out each commit in a worktree of its own and run the suite's part there (`make fate-cbs`), the totals per commit in the hand-back. A reference changed by a commit is in that commit.
5. **Each message says what the commit does now.**
   Read the body for the history of the review ("the two cases of the review", "now also"): rewrite it as a description. A credit to a reviewer's branch stays.
6. **The fix and its test are separate commits, the test after the fix.**
   `for c in $(git rev-list --reverse BASE..HEAD); do git show --stat --format=%h $c; done`: a commit with `tests/api`, `tests/ref` or a new `tests/fate` entry has no library file. The exception is a reference of an existing shared test that the fix changes: it goes with the fix, and the description says so.
7. **Upstream searched first, the reviewer's branches fetched.**
   `git fetch fairy` (or the reviewer's fork) and `git branch -r | grep prN`: a `-fix` or `-replace` branch is carried unchanged and credited, a `-tooling` branch is run on the unchanged head for the red column.
8. **A resubmission changes nothing unrelated to the review** (`doc/developer.texi`, "Patch review process").
   `git range-diff OLDBASE..OLDHEAD BASE..HEAD`: every changed hunk answers a finding or an item of this audit.

## A commit message

9. **Subject `area/sub: what it does`, imperative.**
   `git log --format=%s BASE..HEAD` beside `git log --format=%s -20 up/master -- DIR` for each directory touched: a test commit is `tests/api: ...` or `tests/fate/cbs: ...`, never `tests: ...`.
10. **The body wrapped at 72 columns** except code, URLs and trailers.
    `git log --format=%B BASE..HEAD | awk 'length > 72'` prints nothing but those.
11. **Trailers in one block at the end, after a blank line, `Signed-off-by:` before `Assisted-by:`.**
    `git show -s --format=%B $c | git interpret-trailers --parse` lists every trailer of every commit, and `git show -s --format=%B $c | grep -B1 -m1 '^Signed-off-by:' | head -1` prints an empty line. A message assembled by a script loses the blank line before the block easily; git still parses such a block when most of the paragraph's lines look like trailers, so the parse alone does not show it.
12. **No trailer added or removed by a lane.**
    Compare the parsed trailers with those of the head the reviewers saw.

## A test

13. **The program decides nothing about the code under test.**
    `grep -nE 'exit\(|abort\(|assert|return [1-9]|return -' T`: every hit is either a failure to set the test up (memory, the sample, a copy of a packet), which may end the program with a message on stderr, or it is a verdict, which is printed and compared by the reference instead. A helper that checks the test's own fixture is a verdict too: print what the fixture holds.
14. **No expectation in a C constant.**
    `grep -nE '(!=|==) *(-?[0-9]+|[A-Z_]{4,})' T` and `grep -nE 'strcmp|memcmp' T`: a comparison may choose what to build or print a result (`printf(" unchanged=%d", !memcmp(...))`), never choose the exit status or skip a case silently.
15. **A parser of the output prints what it cannot parse.**
    The same grep: `if (len > size) exit(2);` in a reader of the filter's output is a verdict on the output. Print `truncated` and go on.
16. **Fixtures and oracles do not come from the code under test.**
    `grep -n 'av_bsf_\|avcodec_send\|ff_cbs' T` in the helpers that build inputs and in the oracle of a walk: an input made by running the filter under test makes the test agree with whatever the filter does. Build it by hand and print what it holds.
17. **The timestamps of test packets keep the API's rules.**
    `grep -n -- '->dts *=\|->pts *=' T`: `pts` is never less than `dts` (`libavcodec/packet.h`), a missing one is `AV_NOPTS_VALUE` on purpose, and a zero-initialized packet has `dts` 0.
18. **Every case depends on the change, plus one control.**
    Run the new test on the commit before the change (a worktree of it with the test files checked out): the labels whose output is the same there test existing behaviour. Keep one as the control of a case beside it; a refusal that prints `error` either way is kept only with a mutation that makes it pass.
19. **Every fix fails a named label when taken out.**
    One mutation per fix, by a script that replaces one string, rebuilds, runs the entries with `make -k` and prints the labels whose output changed. A mutation that changes no label is a fix without a test, or an equivalent change: say which, and why.
    For a whole series, sweep it: negate every single-line `if (...)` that the series adds, one at a time (leave out the error and allocation checks, which fail every label alike), and keep the result of each as one JSON line. Two lists come out: the conditions that no label notices, and the labels that no mutation changes. On #25395, 115 conditions took 23 minutes on a loaded machine, five of them for one that looped until its timeout; 9 changed no label, one of them a real gap (an end of sequence NAL unit in front of the pictures, which is where FFmpeg's HEVC parser puts it), and no label was left unchanged by all of them. Give every run a `timeout`: a negated loop condition spins.
20. **A family, not a case.**
    When a finding is a neighbour of an earlier one, the invariant is written in the test's comment, every combination is generated, and the oracle prints one code per combination ([the recipe](lessons-2026-11.md#a-fourth-bot-round-the-invariant-and-the-walk-order-527-2026-11-11)). The red column is the walk on the unchanged library.
    The expected result of every row is written before the fix, from the clause and by something that does not read the code under test (a table, a small script), and the walk's output is checked against it ([state the obligation before the fix](lessons-2026-11.md#a-sixth-bot-round-state-the-obligation-before-the-fix-order-534-2026-11-12)). A row whose expected result the statement does not give is a gap in the statement.
21. **Every statement of the clause has the same key.**
    `grep -n 'pos\b\|pts\|picture' FILE` in the state the fix touches: for each field that stands for a picture, say whether it is its identity or its place in output order, and check that every statement (what is in force, what is owed, what a cancellation ends) uses the same pair, in the live state and in the folded one ([the model before the family](lessons-2026-11.md#a-seventh-bot-round-the-model-before-the-family-order-538-2026-11-13)).
    Search the diff for branches on an id's value, flags that exempt an id, and distinctions between "ours" and "theirs"; name the model statement behind each, including messages the code creates or repeats. An origin-aware query answers a picture relation; a special value does not. Cross input ids with the written id and observe both missing and unnecessary cancellations ([what the code writes is in the model too](lessons-2026-11.md#an-eighth-bot-round-what-the-code-writes-is-in-the-model-too)).
22. **A picture is never its timestamp.**
    `grep -n -- '->pts\|->dts' T` in the readers and `grep -n '== *pos\|< *pos\|<= *pos' FILE` in the code: a comparison of timestamps answers "later", never "the same picture". The walk has a column where two pictures share a timestamp, the reader gets the picture order counts apart from the packets, and each such combination prints what holds either way or a refusal.
23. **The test is smaller than the change, and its machinery exists once.**
    `git diff --numstat BASE..HEAD`: the test program's lines against the additions outside `tests/` and `doc/`. `grep -c 'split_nals\|next_message\|av_bsf_alloc\|av_bsf_init' T`: one walker over NAL units and SEI messages, one reader of the message, one setup of the filter. After a restructuring, the new program built against the unchanged library prints the old references.
24. **Sanitizers after the last test change**, full FATE with GCC and clang on the head that will be pushed, the load average beside the totals, an intermittent entry named and rerun 30 times and never counted as a pass.

## A reply

25. **Every finding answered once:** fixed (the commit and the test), shown correct (the clause, the code path, the probe), or outside this pull request (its own patch, named).
26. **Every clause with its edition and page**, read in the local copy (the page of a `pdftotext` line is the next footer below it).
27. **No AI line**: the description has it. Thanks for what the reviewer actually did.
28. **The description still true:** read every sentence of the pull request description against the new head (what the references cover, the FATE totals, the intermittent entries) and hand back the sentences to replace.
29. **Earlier promises kept:** read the earlier replies in the thread for "its own patch" and "its own pull request", and say where each stands.

## Traps met while writing this list

- Symptom: a global replacement of `exit(1);` by a `SETUP_FAILED();` macro also changed the `exit(1)` inside the function behind the macro, which then called itself.
  Cause: the replacement ran over the whole file.
  Fix: `grep -n 'exit(' T` after the replacement must show exactly the one call left.
  Found by: that grep, before the first build.
- Symptom: a commit message built by a script had its trailers glued to the last paragraph.
  Cause: `'\n'.join(paragraphs) + trailers` puts no blank line between them.
  Fix: check 11 above on the message file before `git commit -F`.
  Found by: `tail` of the message file; `git interpret-trailers --parse` had counted the trailers as usual.
- Symptom: the lesson "set the bit, escape again, and read the flag back" produced the `exit(1)` that the review then flagged.
  Cause: "read back" was written as a check in C.
  Fix: read back means print: the line `non-packed-source: vps=1 sps=1` is in the reference.
