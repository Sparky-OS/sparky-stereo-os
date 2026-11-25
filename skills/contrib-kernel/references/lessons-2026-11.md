# Lessons from the lanes, November 2026: contrib-kernel

**For** whoever prepares a kernel patch next: the traps met preparing a patch on top of a series still in review, each with its symptom, cause, fix and how it was found.

## Recipe: a patch on top of a series in review

1. Clone the kernel shallow at the series' `base-commit` (from its cover letter): `git clone --depth 1 --branch v7.4-rc2 https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git`, then check `git rev-parse HEAD` against the cover's `base-commit`.
2. Fetch each patch of the series in its raw form, `https://lore.kernel.org/all/<message-id>/raw`, and apply them in order with `git am`; the diffstat must match the cover letter's.
3. Commit your patch on top, then `git format-patch -1 --base=<base-commit>`: the file ends with `base-commit:` and one `prerequisite-patch-id:` per patch of the series (`submitting-patches.rst`, "Providing base tree information").
4. Run `scripts/checkpatch.pl --no-signoff` and `--strict` on the file, in a place that has `python3-ply` and `python3-git` (trap below).
5. Find the recipients with `scripts/get_maintainer.pl --nogit --nogit-fallback <patch>` in a shallow clone (trap below), and add the series' own authors.

Done this way on 2026-11-25 for a skill on top of the `agents/skills/` series v5 (ORDER 880): six patches applied, the diffstat "8 files changed, 642 insertions(+), 3 deletions(-)" as the cover said.

## Traps

- **Symptom:** `checkpatch.pl` prints a Python traceback, `ModuleNotFoundError: No module named 'ply'`, and after `python3-ply` is installed, `No module named 'git'`.
  **Cause:** checkpatch runs `scripts/spdxcheck.py` on a new file with an SPDX line on its first line, and that script imports `ply` and GitPython.
  **Fix:** run checkpatch where Debian's `python3-ply` and `python3-git` are installed (testing on 2026-11-25: 3.11-12 and 3.2.1-1), for example in a throwaway container; with both, the traceback is gone.
  **How found:** the series' own 4/6 adds `references/coccinelle.md`, whose first line is an SPDX comment; checkpatch on it showed each traceback in turn.
- **Symptom:** checkpatch warns "Unknown commit id '989fe6771266', maybe rebased or not pulled?" for a commit that exists.
  **Cause:** the clone is shallow and does not hold that commit.
  **Fix:** read the warning as a limit of the clone, or fetch the commit; do not change a correct commit ID.
  **How found:** the same warnings on the series' own patches, whose IDs are mainline commits.
- **Symptom:** every patch that adds a skill gets "WARNING: added, moved or deleted file(s), does MAINTAINERS need updating?".
  **Cause:** checkpatch warns when a patch adds a file without touching MAINTAINERS; the AGENT RESOURCES entry (`F: agents/`) already covers it.
  **Fix:** none needed; say in the cover letter that the warning is the same one the series' own skill patches carry.
  **How found:** checkpatch on the series' patches 2/6 to 6/6 gave the same single warning.
- **Symptom:** `get_maintainer.pl` prints "Bad divisor in main::vcs_assign: 0" and lists your own commit's author as `GitAuthor`.
  **Cause:** it counts authors from the history, and a shallow clone has almost none.
  **Fix:** `--nogit --nogit-fallback`; the maintainers and lists then come from MAINTAINERS alone.
  **How found:** the output, compared with the run with those options.
- **Symptom:** a commit with `Assisted-by: <model> (<vendor>)` fails checkpatch with "ERROR: Unrecognized email address" and "WARNING: Non-standard signature: Assisted-by:".
  **Cause:** the tag's handling left `checkpatch.pl` in 7.4, with the tag itself.
  **Fix:** follow the rule of the tree you send to ([the rule](../SKILL.md#the-rules-that-come-first)); in 7.4 the tools' part is said in the cover letter.
  **How found:** checkpatch on the same patch with and without the line, 2026-11-25.
- **Symptom:** a KUnit run reports success while tests fail.
  **Cause:** with `--raw_output`, `tools/testing/kunit/kunit.py` does not parse the results; `parse_tests()` says "Treat unparsed results as one passing test" (7.4-rc2). The KUnit FAQ recommends `--raw_output` for debugging and no document says the run then always passes.
  **Fix:** judge a run by the parsed summary, never by the exit status of a `--raw_output` run (also in [drivers' lessons](../../drivers/references/lessons-2026-11.md)).
  **How found:** reading `parse_tests()` after an earlier lane saw exit 0 with failing tests.

## Perks

- lore.kernel.org answered a plain client named generically on 2026-11-25. Search as an Atom feed: `https://lore.kernel.org/all/?q=<query>&x=A`, with `s:` for the subject, `b:` for the body, `f:` for the sender and `d:YYYYMMDD..` for dates; a search with no match answers HTTP 404. A message's raw form is `<address>/raw`, a whole thread `<address>/t.mbox.gz`. When a wall shows, the git mirror route in [search-upstream-first](../../search-upstream-first/SKILL.md) still works.
- `git fetch --depth 1 origin master` in the same shallow clone, then `git diff --stat <base> FETCH_HEAD -- Documentation/process`, shows in seconds whether the process documents changed since the series' base.
