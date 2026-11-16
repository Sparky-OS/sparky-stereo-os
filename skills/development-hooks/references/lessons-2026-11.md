# development-hooks: lessons from the reviews of November 2026

**For** whoever maintains the hooks' kit and installer or looks into a decision a hook made: the traps the review rounds of the hooks section met, each with its symptom, its cause, its fix and how the cause was found.

Written by the review rounds of ORDER 531; each entry names the round it came from.
The traps about writing a hook are in [the skill itself](../SKILL.md#traps).

## Traps: the symptom, the cause, the fix, how it was found

- **A workspace name breaks setup.**
  **Symptom:** `install.py init` reports a JSON error for a path containing a double quote or backslash.
  **Cause:** inserting the path directly into JSON changes its syntax.
  **Fix:** quote the path for the shell when calling `init`; the installer escapes it separately for JSON, including disk-floor keys.
  **How found:** a test initializes a workspace and scratch folder with both characters, reads every configuration and runs the generated hook command.
  (ORDER 531, stage 2)
- **Rewiring loses the original settings backup.**
  **Symptom:** after two writes, only the later settings remain in the backup.
  **Cause:** a timestamp with one-second resolution gives both copies the same name.
  **Fix:** the installer reserves a unique backup name for each write, even within the same second.
  **How found:** two writes with a fixed clock must retain both preceding versions.
  (ORDER 531, stage 2)
- **A media check says clean after its reader failed.**
  **Symptom:** the metadata reader exits with an error, but the publish check finds no location tags and reports clean.
  **Cause:** the checker only looked at the reader's output, ignoring its exit status.
  **Fix:** a nonzero exit now reports `location data NOT checked`; make the file readable and run the check again.
  **How found:** a substitute metadata reader exits 2 with empty output; the test requires a hard finding and also checks the existing `location_data` switch.
  The real reader (exiftool 13.55) was then run as the check runs it: 130 pictures of this repository all exit 0, an empty file and a file it cannot open exit 1, and a text file under a picture's name exits 0 with no tags, so it passes as a file without location data.
  (ORDER 531, stages 2 and 3)
- **Listed and enabled, with no run proved.**
  **Symptom:** Codex lists a hook as enabled, but no event or answer has been recorded.
  **Cause:** registration, trust and event delivery are separate checks; an enabled hook may still be untrusted.
  **Fix:** review it in `/hooks`, then verify its effect in an authorized session using a disposable workspace and profile.
  Record the event and answer there; when only registration was checked, say so and leave event delivery unproved.
  **How found:** Codex 0.167.1 loaded all seven hooks as 15 enabled but untrusted handlers in an isolated profile, with no hook load errors or warnings; the probe started no conversation and captured no events ([the wiring proof](../../../hooks/TOOLS.md#codex)).
  (ORDER 531, stage 2)
- **A saved log cannot replay the whole command.**
  **Symptom:** replaying a refused or passed log entry no longer produces its original decision.
  **Cause:** the outreach logs keep only the first 200 characters and flatten line breaks; they also omit the working folder and session's reading state.
  A prefix can lose the sending command or end inside a quote or here-document.
  **Fix:** keep a private full event and answer when reproducing a problem, with the relevant configuration and state; inspect them for secrets before sharing any example.
  Keep synthetic complete commands separate from saved fragments, and never execute a logged send to test its classification.
  **How found:** a replay of saved entries on 2026-11-12 reproduced one false refusal of quoted text, but most entries ended at the 200-character limit and could not be judged; complete synthetic commands, kept apart and labelled, exercised each gate instead.
  A cut line is still worth reading: one of them, which the guard could not read as shell and let through, led to [the reader's trap](../SKILL.md#traps).
  (ORDER 531, stages 2 and 3)
- **A hook's command-line mode waits for ever.**
  **Symptom:** `python3 hooks/branch-keeper/hook.py --config FILE audit` prints nothing and never ends; the same with `audit` first works.
  **Cause:** the script looked for its subcommand only as the first word, so with `--config` first it took the hook's path and waited for an event on standard input, which a terminal never closes.
  **Fix:** a hook that is also a command finds its subcommand anywhere among its words, and its test runs the command with the options first and standard input closed (`test_the_audit_finds_its_configuration_after_its_options_too`).
  **How found:** a smoke run of the new hook on 2026-11-16 that had to be stopped by its process number.
  (ORDER 612)
- **One folder for a whole line.**
  **Symptom:** on a long line (`cd /A/repo ... git push ...; ... git branch -D BR; cd /A && PROGRAM; cd /B`) a guard refused `git push` and `git branch -D` with "the repository at /A could not be read", although both ran after `cd /A/repo`; the same `cd` with `&&` in a short line passed.
  **Cause:** `event.working_folder()` searched the line's text once for the first `cd DIR` followed directly by `&&`, `;` or a line end, and gave that one folder to every command. A first `cd` written any other way (`cd X || exit 1`, `cd X 2>/dev/null &&`, `cd -- X`, `cd -P X`, `if cd X; then`, `{ cd X; }`, `pushd X`) was skipped, so the next match won: a later `cd /A &&`, or a line inside a quoted multi-line text (a pull request's `--body`) that starts with `cd X &&`. And a second `cd` was never followed: `cd /A/repo && git status; cd /B/other && git branch -D only-copy` judged the deletion in the first repository, where the branch does not exist, and let it through without a word.
  **Fix:** `hookkit.commands_in_folders(line, cwd)` (and `event.commands_in_folders()`) reads each simple command with the folder the shell would be in: the reader carries the folder through `cd`, `pushd` and `popd` as bash scopes them (a subshell's ends at its `)`, a pipeline's and a background job's change nothing, `bash -c`, a substitution and a here-document a shell reads begin where they stand, `eval` keeps it, `timeout 5 cd X` changes nothing), and `hookkit.git_place` adds git's own `-C` options in order (a `-C` after the subcommand, as in `git switch -C NAME`, is the subcommand's). A folder written with a shell variable is None with the reason, so a guard can say it instead of reading a folder named `$R`. branch-keeper uses it; outreach-guard, publish-check and stereo-contract-guard still call `working_folder()`.
  **How found:** the line's shape from the queue entry was run through `working_folder()` and gave the right folder, so the cause had to be in the first `cd`; twelve ways of writing it showed nine skipped, and the first red run of the hook's long-line test named "/", the `cd / && make` of the quoted body. The test was written before the fix and failed on main for all six other forms, with the refusal of the real day.
  (ORDER 612c)
- **A gate that fails open lets everything through; a gate that treats a missing file as empty refuses everything and hides why.**
  **Symptom:** with the queue's state file gone, every lane was refused as having no row, and an error inside the hook let every dispatch through.
  **Cause:** `hookkit.main` fails open on any exception, which is right for advice and wrong for a gate, and the first version read a missing file as an empty queue.
  **Fix:** the hook raises its own `StateError` for a missing, unreadable or foreign state file and `handle` answers it as a deliberate refusal that names the file and the command that rebuilds it; `on_missing_state: tell` lets the dispatch go ahead and says so. Only the unexpected still fails open.
  **How found:** reading how the first version loaded the file, then a test with the file removed (`test_a_missing_file_refuses_the_dispatch_and_says_how_to_rebuild_it`).
  (ORDER 633)
- **A row marked when the gate passes is marked even when the tool does not run.**
  **Symptom:** a dispatch refused by another hook left its row in flight.
  **Cause:** the row changed in the same PreToolUse event that gated it, and two hooks run on one dispatch.
  **Fix:** the gate decides before, and the row changes in the PostToolUse event of the same tool, which runs only when the tool succeeded.
  **How found:** the order of the two hooks on a dispatch; `test_a_refused_dispatch_changes_nothing`.
  (ORDER 633)
- **The body of a here-document is not part of the command, so it is not part of the journal write either.**
  **Symptom:** `cat >> ORDER.md <<'EOF' ... accepted ... EOF` was not seen as an acceptance.
  **Cause:** `event.acting_command()` drops the body of a here-document no shell reads, so that a file being written is not taken for a command being run; the body is exactly the text written.
  **Fix:** to find what a command writes to a file, read `event.command` for the target (`>>`, `tee`) and take the text from it; use `acting_command()` only to decide what runs.
  **How found:** the test with a here-document append (`test_a_shell_append_to_the_journal_counts_even_through_a_here_document`).
  (ORDER 633)
- **An `echo` of a launch line is not a launch.**
  **Symptom:** `echo "run launch-lane.sh queue/x later"` was gated as a launch of lane x.
  **Cause:** the launch pattern was searched in the whole acting text, quotes included.
  **Fix:** search each simple command's own words up to the first word that holds white space, which is a quoted text; a line that cannot be read as shell is searched as text, because a gate too many is better than one missed.
  **How found:** the test `test_a_command_that_only_mentions_a_launch_is_not_a_launch`.
  (ORDER 633)
- **An option written after a subcommand is rejected by argparse.**
  **Symptom:** `hook.py next --config FILE` exits 2 with "invalid int value" naming the config path, while `--config FILE next` works.
  **Cause:** the option belongs to the main parser; after `next` its value is taken as the optional count.
  **Fix:** take `--config FILE` out of the argument list before parsing, so it may stand anywhere, as the subcommand does.
  **How found:** the test that runs the command with the option last.
  (ORDER 633)
- **A test workspace that has the other hooks' folders has lanes of its own.**
  **Symptom:** an audit test found a lane folder with no row that the test never made.
  **Cause:** `testkit.HookCase.setUp` writes a `demo-lane` folder with a brief into the queue folder for the brief hook's tests.
  **Fix:** a queue test removes it first, and every audit test lists the folders it means to find.
  **How found:** the first red run of the audit tests.
  (ORDER 633)
- **The time of a row is minute-grained, so a change in the same minute is invisible.**
  **Symptom:** an acceptance set right after the journal write stayed owed, or a settle never cleared.
  **Cause:** `updated` is `YYYY-MM-DDTHH:MMZ`; comparing it alone cannot tell two changes of one minute apart.
  **Fix:** an owed acceptance clears when the row's status, time or evidence differs from what was recorded, and settling a false hit sets the same status again with the reason in the evidence.
  **How found:** by reasoning about the comparison before writing it, then `test_the_same_status_again_with_a_reason_settles_a_journal_line_that_was_not_an_acceptance`.
  (ORDER 633)

