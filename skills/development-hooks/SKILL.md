---
name: development-hooks
description: >-
  Hooks of the edition's development cycle: small programs an AI tool or git runs by itself, in the repository's
  hooks folder (design-reading after a compaction or a long gap, brief-and-handback before a lane is dispatched or
  reports, outreach-guard before a pull request, comment, mail or push to a fork, publish-check, stereo-contract-guard,
  disk-floors, container-guard), the default workspace layout (memory, partners queue, private, state), install.py
  init, check, wire and unwire for Claude Code and Codex, and how to add a hook: fail open and say so, state per
  session, a refusal that says what to do next, patterns that pass reads and our own repositories, tests that pipe an
  event in. Load it when a hook refuses a tool call (PreToolUse hook error, Required reading, Outreach guard, Lane brief
  not ready, Hand-back not ready), a hook error notice appears, a guard stops a harmless command, a hook stopped
  firing, or a rule written in a skill keeps being broken.
---

# Hooks for the development cycle

**Check freshness first.**
Written on 2026-11-12 by Claude Fable 5.2 with Daniel, when the hooks that had grown on one workstation were made generic and public.
The tools' own documentation was read that day ([what each tool offers](../../hooks/TOOLS.md)); hooks are young in every tool, so read it again before relying on a detail.

Daniel asked for this section on 2026-11-12: "we should also document, all hooks that are related to the OS development cycle as a "hooks" section, partner, with generic but well organizer folder structures baked in".
The first hook came on 2026-10-09: "time to start putting some hooks partner, this is wasting my precious money".
What they are for, in his words of 2026-11-12: "a very well informed, tooled and of course, that can read memories partner, no matter the class, is always better ... all of them are crutial all the partners need".

A skill states a rule; a hook makes it happen at the moment it matters, for a person's AI partner on any tool and for every lane it starts.
The programs, their example configurations and their tests are in [`hooks/`](../../hooks/README.md) of this repository.

## Working recipe: adopt the hooks

Run every command from the top folder of this repository's checkout; they need `python3` and `git`, and were run with Python 3.12 and 3.14.
`WORKSPACE` is a folder of yours for the work, new or existing; the checkout may stay where it is, because `init` writes its place into the configurations.

1. **Make the workspace:** `python3 hooks/install.py init WORKSPACE` makes [the default layout](#the-default-layout) and one configuration per hook in `WORKSPACE/private/hooks/`. It prints `wrote` for each file it makes and `kept` for each that exists; it overwrites nothing.
   It also makes four starter files for you to fill in: `memory/MEMORY.md`, `partners/HOUSE-RULES.md`, `private/README.md` and `private/ledger.md`, the list of what was sent, to whom and when.
2. **Put your own values in:** the memory files every session reads (`design-reading.json`, `core`), your accounts and projects (`outreach-guard.json`, `own_owners` and `own_repos`), your identities and the names you never publish (`publish-check.json`), your floors (`disk-floors.json`). Switch off what you do not want: every hook has `enabled`, every part its own switch.
   Each hook's page has the table of its keys with their defaults; the values to replace are the placeholders: `your-github-user`, `you@example.org`, the two memory names under `core`.
3. **Check:** `python3 hooks/install.py check WORKSPACE` reads every configuration the way the hooks do and names each file a configuration points to that does not exist. It ends with "Every configuration reads, and every file it names exists." and exit 0, or with the count of things to fix and exit 1.
   Run it again after moving or removing a rule file: a file that is named and missing is not asked for, and the reading text or the refusal says which one and where to correct it.
   A file that does not exist cannot be read, so a hook does not ask for it; that is why `check` must pass before you rely on the hooks, and why it also names a `core` list left empty.
4. **Wire a tool:** `python3 hooks/install.py wire claude WORKSPACE` prints the settings block; with `--write FILE` it merges the block into that settings file and keeps a copy named `FILE.before-hooks-DATE-UNIQUE` beside it. For Codex: `wire codex`. For commits: `python3 hooks/install.py git REPOSITORY WORKSPACE` prints two `git config` commands.
   `FILE` is the tool's settings file: for Claude Code `~/.claude/settings.json` for all your projects or `.claude/settings.local.json` in one; for Codex `~/.codex/hooks.json`, written the same way with the same copy ([the tools page](../../hooks/TOOLS.md) has the rest).
   Claude Code normally picks a changed settings file up by itself; if the hooks have not appeared after a few seconds, start a new session.
   The two `git config` lines set `core.hooksPath` to `hooks/publish-check/git` and name the configuration; while that is set, git runs only that folder's `pre-commit` and `commit-msg`, so a repository with hooks of its own calls these two from them instead ([git](../../hooks/TOOLS.md#git)).
   When the check cannot run, a commit goes ahead and says so; with `--on-failure block` the command prints a third line, and such a commit is refused instead.
5. **Watch the first run.** A hook whose path is wrong does not stop anything: the tool shows a "hook error" notice and carries on. In Claude Code, `/hooks` lists what is wired.
   In Codex, open `/hooks`, review the commands and configuration paths, and trust the entries you intend to run.
   Check the expected refusal or context on an event the hook covers; an enabled entry alone proves only that the settings were loaded.
   Six of the seven hooks' pages have a "Try it by hand" line that pipes one event in and prints the answer, without sending, deleting or publishing anything.
6. **Run the tests after any change:** `python3 hooks/tests/run.py` ends with `N test files, N tests: all passed`; `sh hooks/tests/clean-machine.sh` runs the whole proof on a machine that has only this repository and ends with `clean-machine proof: every step passed`.
   Both need `python3`, `python3-yaml` and `git` only; the proof works in a temporary folder and removes it.
7. **To leave:** `python3 hooks/install.py unwire FILE` takes these hooks out of a settings file and leaves every other entry as it was.
   It does not touch the configurations, the state or the logs under `WORKSPACE`, and it does not undo the git wiring: `git -C REPOSITORY config --unset core.hooksPath` and the same for `sparky.publishCheckConfig` do.

## What each hook is for

| Hook | The moment | What it does | Its page |
| --- | --- | --- | --- |
| design-reading | Session start, after a compaction, after a long gap, the first call of a lane | The recorded designs are required reading; other tools are refused until each file was read in full | [design-reading](../../hooks/design-reading/README.md) |
| brief-and-handback | Before a lane is dispatched; before a brief is written; before a report comes back | A brief quotes its design and names the skill to leave behind; a report carries its Design check, corpus list and skill changes | [brief-and-handback](../../hooks/brief-and-handback/README.md) |
| outreach-guard | Before a command that sends something to another project | Refused until the outreach rules and the project's contrib skill were read in this session and the reference index was consulted; then the filing checklist | [outreach-guard](../../hooks/outreach-guard/README.md) |
| publish-check | Before a push, a post, a mail; at every commit | Location data, another person's address, a name never published or a secret asks the person | [publish-check](../../hooks/publish-check/README.md) |
| stereo-contract-guard | Before a brief or a draft is written, before publishing, before a push | A sentence or a code line that breaks [the stereo contract](../sparky-stereo/SKILL.md#part-one-the-contract) asks the person, with its rule and its fix | [stereo-contract-guard](../../hooks/stereo-contract-guard/README.md) |
| disk-floors | Before a command that fills a disk; while a floor is crossed | Free space in GiB against each folder's floor | [disk-floors](../../hooks/disk-floors/README.md) |
| container-guard | Before a command that stops or removes containers | Refused when it would act on every container of a shared daemon, or on a protected service | [container-guard](../../hooks/container-guard/README.md) |

Every one ships switched on, as the edition uses them; `disk-floors` only tells, also under a floor, unless `below_floor` says `ask` or `deny`, and one part of `container-guard` (refusing a prune of everything) ships off.
Each hook's page lists the default of every part.
A long gap is 3300 seconds without a call (`gap_seconds`); a compaction arrives as a session start whose source is `compact`; a lane is one piece of work handed to another agent, and its first call is the first event that carries a new agent id.

## The default layout

One workspace folder holds the clones (`repos/`), the recorded decisions (`memory/`, one fact per file, with `MEMORY.md` as the index), the partners' rules and one folder per lane (`partners/HOUSE-RULES.md`, `partners/queue/LANE/` with `BRIEF.md`, `REPORT.md`, `NOTES.md` and `evidence/`), what must never be in a repository (`private/`: drafts, the ledger, each hook's real configuration) and the hooks' own state and logs (`state/hooks/`).
[The tree](../../hooks/README.md#the-default-layout) is in the section's front page.
Every path in it is a configuration value: `paths` in a hook's configuration replaces any of them, so a workspace that grew in another shape keeps its folders.
The repository ships examples only; the lists that make a check useful (identities, the names never published, allowed addresses) stay in `private/`.

## When a hook stops you

- **A refusal is a stop, not an argument.** Do what it says: read the files it lists in full, add the sections it names, fix the sentence. Then send the same call again.
- **Never work around it:** no other tool for the same act, no split command, no edit of the hook or its configuration to get past. If the hook is wrong, say so in the hand-back with the command it refused; the person changes the configuration.
- **"Ask" means the person decides.** A lane that nobody watches cannot be answered: fix what the finding names instead of waiting.
  Where a tool cannot ask from a hook, an ask arrives as a refusal that gives the reason (`ask_becomes`, `deny` as shipped).
- **A notice that a hook could not run** ("Hook NAME could not run and let the action through") is not a pass of the check: the action went unchecked. Report it.
  The notice is for the person and nothing needs to be sent again, but what the check would have looked at was not looked at: run it by hand where it matters, for example `python3 hooks/publish-check/publish_check.py --config WORKSPACE/private/hooks/publish-check.json --files FILE`, which prints `publish-check: clean` when nothing is found.
- **A refused hand-back** names the sections that are missing. After two refusals the next one goes through with a notice that lists what is still missing, so a report is never lost.

## Add a hook, or extend one

A rule becomes a hook when it was written down and broken again: the cost of the next break is higher than the cost of the hook.
Extend the hook that already stands at that moment (another pattern, another check with its switch) before making a new one.

1. **Name the moment and the answer:** which event (session start, a prompt, before a tool, after a tool), which tool, and whether the hook refuses, asks the person, or adds a line of context. Check in [the tools page](../../hooks/TOOLS.md) that the tool can do it.
2. **Make the folder** `hooks/<name>/` with the same five things as the others: `hook.py`, `config.example.json`, `wiring.json`, `tests/test_<name>.py`, `README.md`.
   Copy the smallest hook, `hooks/container-guard/`, as the template: it has the imports, a `handle`, the three files and a test of each kind.
3. **Write the logic on the plain event.** `hook.py` defines `handle(event, kit)` and calls `hookkit.main('<name>', handle)`; it never names a tool's own word such as `Bash`, it asks for the plain one (`event.tool == 'shell'`).
   The event gives `kind` (`session-start`, `prompt`, `before-tool`, `after-tool`), `tool` (`shell`, `read`, `write`, `edit`, `dispatch`, `handback`, or the tool's own name), `command`, `path`, `text`, `agent`, and `reads()` (the files this event read in full).
   For a shell line use `event.commands()`, the simple commands the line runs, not a search of its text.
   The reader knows `sh`, `bash`, `dash`, `zsh` and `ksh` with three levels of `-c`, and wrappers such as `env`, `sudo`, `timeout`, `nice` and `xargs`.
   The kit's words: the plain event is a tool's event under the kit's own names, a dialect is the table that turns one tool's names into them, and the reference index is whatever local search of reference documents your tools offer, named under `consult_tools`.
4. **Answer with** `kit.deny(reason)`, `kit.ask(reason)`, `kit.context(text)` or nothing. A refusal says what was refused, why, what to do next and when the same call will pass.
5. **Keep state in `kit.state`,** a dictionary saved per session and per lane behind a lock; log with `kit.log('refused.log', line)`.
   The lock is taken when the logic first touches `kit.state` and held until the run ends, so touch it only on the path that needs it: a hook that keeps no state never waits.
6. **Configuration:** every path through `kit.path(...)`, every list and number from `kit.cfg`, a switch for each part read with `kit.on(...)`. The example holds placeholders and the edition's defaults, all on; nothing of one machine, no real name, no address.
7. **Test by piping.** Subclass `testkit.HookCase`: it makes a toy workspace with `install.py`'s own `init`, runs the hook as a tool runs it and gives the answer back. Write what must be refused and, beside it, what must pass: the reads, the workspace's own repositories, text that is only written to a file. Run each test red once (take the rule out) before trusting its green.
8. **Wire it:** `wiring.json` lists the events and matchers per tool; `python3 hooks/install.py wire claude WORKSPACE --only <name>` shows the result.
9. **Write its page:** what it runs on, what it refuses or adds, why (with the words that asked for it), its configuration, how it fails.
10. **Check:** `python3 hooks/tests/run.py` (the whole section, with the test that no path of one machine and no address is in it), `python3 tools/check-skills.py` (every local link of the new page) and the publish check on every file.

## Traps

- **Failing closed locks a session, or loses a report.**
  **Symptom:** every tool call of a session is refused and nothing the partner does helps; or a lane ends and its report never arrives.
  **Cause:** a hook that exits with an error of its own, or refuses the very tool that would repair things. For a hand-back, Claude Code's reference says what a refusal does: "Claude Code then tells the subagent, up to three times, that its report wasn't delivered and to call the tool again. If your hook keeps denying, the subagent ends without delivering a report through this tool".
  **Fix:** `hookkit.main` catches every failure, lets the action through, writes `errors.log` and tells the person in one line; reading tools are never refused; the hand-back check counts its refusals and stops at two.
  **How found:** the tools' documentation, and a cold reader started with "use no tools" whose hand-back a required-reading hook refused ([writing-front-pages](../writing-front-pages/SKILL.md#explainers-for-a-standards-group-with-respec-mcp-2026-11-06), the last trap).
- **Failing open in silence is a hook that is off.**
  **Symptom:** a rule is broken while everyone believes its hook is on.
  **Cause:** a wrong path in the settings, a folder that moved while the hook's pattern still named the old one, a configuration that no longer parses; a tool carries on after a hook that cannot start. Claude Code: "A policy hook with a wrong path or a crashing script then lets everything through." Codex skips a hook that was not reviewed and trusted.
  **Fix:** every path is a configuration value and `install.py check` names the ones that do not exist; a hook that cannot run tells the person, it does not only log; watch the first run; for a workspace that prefers a refused call to an unchecked one, `wire claude ... --on-failure block`.
  **How found:** reading each tool's failure rules before choosing how these hooks fail.
- **State that is shared, or lost between two calls.**
  **Symptom:** one lane's reading opens the tools of another; or a file read a moment ago is still on the list.
  **Cause:** state kept per machine, or per session where lanes share the session; and a tool that runs several reads at once starts the hook once for each, so each run reads the old state and writes its own.
  **Fix:** the key is the agent's id, else the transcript, else the session; the state is read, changed and written behind a lock.
  **How found:** twelve reads piped in at once: without the lock a read was lost in 5 of 10 runs, with it in none (`test_parallel_reads_all_count`). Codex's page says "Subagent hooks use the parent session id", so a lane's own state is not proved there.
  A later test held the lock past its five-second timeout and found that the hook still wrote state without it.
  A timeout now lets the action through with an explicit notice, leaves the saved state intact and asks for a retry after the other hook finishes.
  That made a second gap visible: the kit took the lock for every hook, so a guard that keeps no state waited five seconds behind a long run of itself and then let its command through unchecked.
  The lock is now taken when a hook first touches `kit.state`; the publish check, the contract guard and the container guard never take it (`test_a_long_check_of_another_command_does_not_let_this_one_through`).
- **A refusal that only says no.**
  **Symptom:** the partner sends the same call again, gives up, or finds another way to do the same thing.
  **Cause:** the reason names the rule and not the next step.
  **Fix:** name the files by their full path, the sections that are missing, the command to use; end with "Then send the same command again"; write tool text as facts, because Claude Code's reference warns that context "framed as out-of-band system commands can trigger Claude's prompt-injection defenses".
- **A pattern that catches reads, our own repositories, or text.**
  **Symptom:** `gh pr view` is refused; a push to the workspace's own project is refused; a script written to a file with a here-document is refused because its text holds the words of a push; a commit whose message says "push" is refused.
  **Cause:** a regular expression searched over the whole command line.
  **Fix:** judge the simple commands a line runs (`event.commands()`): the program, its subcommand, its options. Text a command only writes is skipped, text handed to `bash -c` or to a shell's here-document is read. Name what is ours in the configuration, and ask git where a remote goes instead of guessing from its name.
  **How found:** on 2026-11-12 a workstation's guard refused, three times, a command that wrote or changed these hooks' own source files, because the files held the words; the lists of what must pass are now tests.
- **A reader that misses what the shell runs.**
  **Symptom:** a send passes unseen when it comes after a comment line, on lines joined by a backslash, inside a loop or a condition, between braces, in backticks, in a substitution inside double quotes or behind `bash -lc`; every test is green.
  **Cause:** the first reader turned each line end into a separator and handed the text to a word splitter, whose comment rule then ran to the end of the whole command and which knows no continuation lines and no keywords such as `do` or `then`; the tests held only the forms their author had thought of.
  **Fix:** `hookkit.shell_commands` reads quotes, comments, continuation lines, here-documents and substitutions itself and takes the shell's keywords off the front of a command; a line it cannot read (a quote left open) is judged by its text, for every kind of send.
  Write the test list from the shell's grammar, not from memory: each way a command can be reached, with the same send in each, and beside it the text that must stay quiet.
  **How found:** on 2026-11-12 the review of a replayed log line that the guard could not read led to a list of thirty valid forms holding one send: the reader saw seven of them, and all thirty after the change, with eight lines that only carry such text still passing.
- **A guard cannot be tested by a file that breaks its rule.**
  **Symptom:** the test file of a check is itself stopped by that check: a planted token fails the publish check, a planted sentence is stopped by the contract guard.
  **Fix:** put the planted thing together while the test runs (`'gh' + 'p_' + ...`), and say so at the top of the file.
  **How found:** the contract check, run over its own first test file, stopped three of its sentences.
- **A test that depends on the machine.**
  **Symptom:** the disk test passes on one machine and fails on a full one.
  **Fix:** make the condition, do not find it: a floor of 0 GiB is never crossed, a floor of a million always is.
- **A tool that cannot ask.**
  **Symptom:** under Codex an "ask" answer is reported as a failed hook and the command runs.
  **Cause:** Codex's hooks page: "`permissionDecision: "ask"` ... are parsed but not supported yet."
  **Fix:** the dialect turns an "ask" into a refusal that says why, or into context, as `ask_becomes` says.
- **Shell text is not all there is.**
  A hook reads the command it is shown; a script file, an alias or a program that starts another are not seen.
  Codex's page says it for every tool: "Treat tool hooks as a useful guardrail, not a complete enforcement boundary."
  Keep the rule written in the skill and the house rules as well.
- **Traps of the kit itself** are in [the lessons of the reviews](references/lessons-2026-11.md), five of them: a workspace name that broke setup, a settings backup lost to a second write, a failed media read reported clean, a hook that a tool lists and never ran, and a log that cannot replay the command it names.

## Perks

- `python3 hooks/lib/design_lookup.py --memory WORKSPACE/memory WORD...` finds a recorded design by the content of the memory files, for a person as well as for the hook that uses it.
- `hooks/publish-check/publish_check.py` is a command of its own: `--files`, `--text` on stdin, a repository's unpushed commits, `--audit N`.
- A hook can be tried by hand with one `printf` piped into it; six of the seven pages have the lines, and the contract guard's events are in its tests, because its page cannot print a sentence that the guard would stop.
- The logs in `state/hooks/NAME/` (`refused.log`, `passed.log`, `errors.log`) are the record of what the hooks did, for a review; a log over 1 MiB is moved aside as `NAME.log.1`, a session's state is dropped after `state_keep_days` (30), and a full event kept to reproduce a decision goes under `private/`.

## Not proved yet

Written on 2026-11-12: the hooks' tests pipe events shaped as each tool's documentation shows them, and they passed in a container with nothing but this repository, without network, as an ordinary user, on a read-only file system.
A live session of Claude Code or of Codex running these scripts was not part of that proof; the Codex dialect in particular was written from its documentation alone.
Codex 0.167.1 later loaded the generated wiring in an isolated profile; this checks registration only, with event delivery and response handling still unproved.
A reader of another lab, given this page alone on 2026-11-12, answered four questions on adopting the hooks and adding one from the text, and listed thirty-three things the page did not say; its list became lines of this page.
When you run them live, add what you find here.
