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

1. **Make the workspace:** `python3 hooks/install.py init WORKSPACE` makes [the default layout](#the-default-layout) and one configuration per hook in `WORKSPACE/private/hooks/`. It prints `wrote` for each file it makes and `kept` for each that exists; it overwrites nothing.
2. **Put your own values in:** the memory files every session reads (`design-reading.json`, `core`), your accounts and projects (`outreach-guard.json`, `own_owners` and `own_repos`), your identities and the names you never publish (`publish-check.json`), your floors (`disk-floors.json`). Switch off what you do not want: every hook has `enabled`, every part its own switch.
3. **Check:** `python3 hooks/install.py check WORKSPACE` reads every configuration the way the hooks do and names each file a configuration points to that does not exist. It ends with "Every configuration reads, and every file it names exists." and exit 0, or with the count of things to fix and exit 1.
4. **Wire a tool:** `python3 hooks/install.py wire claude WORKSPACE` prints the settings block; with `--write FILE` it merges the block into that settings file and keeps a copy named `FILE.before-hooks-DATE` beside it. For Codex: `wire codex`. For commits: `python3 hooks/install.py git REPOSITORY WORKSPACE` prints two `git config` commands.
5. **Watch the first run.** A hook whose path is wrong does not stop anything: the tool shows a "hook error" notice and carries on. In Claude Code, `/hooks` lists what is wired.
6. **Run the tests after any change:** `python3 hooks/tests/run.py` ends with `N test files, N tests: all passed`; `sh hooks/tests/clean-machine.sh` runs the whole proof on a machine that has only this repository and ends with `clean-machine proof: every step passed`.
7. **To leave:** `python3 hooks/install.py unwire FILE` takes these hooks out of a settings file and leaves every other entry as it was.

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

Every one ships switched on, as the edition uses them; `disk-floors` only tells, and one part of `container-guard` (refusing a prune of everything) ships off.

## The default layout

One workspace folder holds the clones (`repos/`), the recorded decisions (`memory/`, one fact per file, with `MEMORY.md` as the index), the partners' rules and one folder per lane (`partners/HOUSE-RULES.md`, `partners/queue/LANE/` with `BRIEF.md`, `REPORT.md`, `NOTES.md` and `evidence/`), what must never be in a repository (`private/`: drafts, the ledger, each hook's real configuration) and the hooks' own state and logs (`state/hooks/`).
[The tree](../../hooks/README.md#the-default-layout) is in the section's front page.
Every path in it is a configuration value: `paths` in a hook's configuration replaces any of them, so a workspace that grew in another shape keeps its folders.
The repository ships examples only; the lists that make a check useful (identities, the names never published, allowed addresses) stay in `private/`.

## When a hook stops you

- **A refusal is a stop, not an argument.** Do what it says: read the files it lists in full, add the sections it names, fix the sentence. Then send the same call again.
- **Never work around it:** no other tool for the same act, no split command, no edit of the hook or its configuration to get past. If the hook is wrong, say so in the hand-back with the command it refused; the person changes the configuration.
- **"Ask" means the person decides.** A lane that nobody watches cannot be answered: fix what the finding names instead of waiting.
- **A notice that a hook could not run** ("Hook NAME could not run and let the action through") is not a pass of the check: the action went unchecked. Report it.

## Add a hook, or extend one

A rule becomes a hook when it was written down and broken again: the cost of the next break is higher than the cost of the hook.
Extend the hook that already stands at that moment (another pattern, another check with its switch) before making a new one.

1. **Name the moment and the answer:** which event (session start, a prompt, before a tool, after a tool), which tool, and whether the hook refuses, asks the person, or adds a line of context. Check in [the tools page](../../hooks/TOOLS.md) that the tool can do it.
2. **Make the folder** `hooks/<name>/` with the same five things as the others: `hook.py`, `config.example.json`, `wiring.json`, `tests/test_<name>.py`, `README.md`.
3. **Write the logic on the plain event.** `hook.py` defines `handle(event, kit)` and calls `hookkit.main('<name>', handle)`; it never names a tool.
   The event gives `kind` (`session-start`, `prompt`, `before-tool`, `after-tool`), `tool` (`shell`, `read`, `write`, `edit`, `dispatch`, `handback`, or the tool's own name), `command`, `path`, `text`, `agent`, and `reads()` (the files this event read in full).
   For a shell line use `event.commands()`, the simple commands the line runs, not a search of its text.
4. **Answer with** `kit.deny(reason)`, `kit.ask(reason)`, `kit.context(text)` or nothing. A refusal says what was refused, why, what to do next and when the same call will pass.
5. **Keep state in `kit.state`,** a dictionary saved per session and per lane behind a lock; log with `kit.log('refused.log', line)`.
6. **Configuration:** every path through `kit.path(...)`, every list and number from `kit.cfg`, a switch for each part read with `kit.on(...)`. The example holds placeholders and the edition's defaults, all on; nothing of one machine, no real name, no address.
7. **Tests first, by piping.** Subclass `testkit.HookCase`: it makes a toy workspace with `install.py`'s own `init`, runs the hook as a tool runs it and gives the answer back. Write what must be refused and, beside it, what must pass: the reads, the workspace's own repositories, text that is only written to a file. Run each test red once (take the rule out) before trusting its green.
8. **Wire it:** `wiring.json` lists the events and matchers per tool; `python3 hooks/install.py wire claude WORKSPACE --only <name>` shows the result.
9. **Write its page:** what it runs on, what it refuses or adds, why (with the words that asked for it), its configuration, how it fails.
10. **Check:** `python3 hooks/tests/run.py` (the whole section, with the test that no path of one machine and no address is in it) and the publish check on every file.

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
- **A refusal that only says no.**
  **Symptom:** the partner sends the same call again, gives up, or finds another way to do the same thing.
  **Cause:** the reason names the rule and not the next step.
  **Fix:** name the files by their full path, the sections that are missing, the command to use; end with "Then send the same command again"; write tool text as facts, because Claude Code's reference warns that context "framed as out-of-band system commands can trigger Claude's prompt-injection defenses".
- **A pattern that catches reads, our own repositories, or text.**
  **Symptom:** `gh pr view` is refused; a push to the workspace's own project is refused; a script written to a file with a here-document is refused because its text holds the words of a push; a commit whose message says "push" is refused.
  **Cause:** a regular expression searched over the whole command line.
  **Fix:** judge the simple commands a line runs (`event.commands()`): the program, its subcommand, its options. Text a command only writes is skipped, text handed to `bash -c` or to a shell's here-document is read. Name what is ours in the configuration, and ask git where a remote goes instead of guessing from its name.
  **How found:** on 2026-11-12 a workstation's guard refused, three times, a command that wrote or changed these hooks' own source files, because the files held the words; the lists of what must pass are now tests.
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

## Perks

- `python3 hooks/lib/design_lookup.py --memory WORKSPACE/memory WORD...` finds a recorded design by the content of the memory files, for a person as well as for the hook that uses it.
- `hooks/publish-check/publish_check.py` is a command of its own: `--files`, `--text` on stdin, a repository's unpushed commits, `--audit N`.
- Every hook can be tried by hand with one `printf` piped into it; each page has the lines.
- The logs in `state/hooks/NAME/` (`refused.log`, `passed.log`, `errors.log`) are the record of what the hooks did, for a review.

## Not proved yet

Written on 2026-11-12: the hooks' tests pipe events shaped as each tool's documentation shows them, and they passed in a container with nothing but this repository, without network, as an ordinary user, on a read-only file system.
A live session of Claude Code or of Codex running these scripts was not part of that proof; the Codex dialect in particular was written from its documentation alone.
When you run them live, add what you find here.
