# Hooks for the development cycle

**For** contributors and their AI partners: the checks that run by themselves while the edition is being built, as small programs any tool can call, with the folder layout they assume.

A rule that lives only in a skill is followed when someone remembers to load the skill.
A hook does not wait to be remembered: it runs at the moment the rule matters, refuses or adds a line, and says what to do next.
Daniel, 2026-11-12: "a very well informed, tooled and of course, that can read memories partner, no matter the class, is always better ... all of them are crutial all the partners need".
These hooks are how that is kept without anyone having to ask.

## The hooks

| Hook | Runs | What it does | Shipped |
| --- | --- | --- | --- |
| [design-reading](design-reading/README.md) | At session start, after a compaction or a long gap, in every new lane; before every tool | The recorded designs are required reading; other tools are refused until each file was read in full | on |
| [brief-and-handback](brief-and-handback/README.md) | Before a lane is dispatched, before a brief is written, before a report is handed back | A brief must quote its design and name the skill to leave behind; a report must carry its Design check, its corpus list and its skill changes | on |
| [outreach-guard](outreach-guard/README.md) | Before a command that sends something to another project | Refused until this session read the outreach rules and the project's contrib skill and consulted the reference index; then it passes with the filing checklist | on |
| [publish-check](publish-check/README.md) | Before a push, a post or a mail; at every commit | Location data, another person's address, a name that is never published or a secret asks the person; style notes are context | on |
| [stereo-contract-guard](stereo-contract-guard/README.md) | Before a brief or a draft is written, before publishing, before a push | A sentence or a code line that breaks the stereo contract asks the person, with its rule and its fix | on |
| [disk-floors](disk-floors/README.md) | Before a command that fills a disk, and while a floor is crossed | Free space in GiB against each folder's floor | on, telling only |
| [container-guard](container-guard/README.md) | Before a command that stops or removes containers | Refused when it would act on every container of a shared daemon or on a protected service | on |

Every hook folder has the same five things: `hook.py` (the logic), `config.example.json` (every key, with the edition's defaults), `wiring.json` (the events it wants, per tool), `tests/` and a `README.md` that says what it runs on, what it refuses or adds, why, and how it fails.

## The default layout

The hooks assume one layout, and every path in it is a configuration value: `paths` in a hook's configuration replaces any of them, with a path relative to the workspace or an absolute one.

```text
WORKSPACE/                    one folder for all the work; not a repository itself
├── repos/                    the clones, one folder each
│   └── sparky-stereo-os/     this repository: skills/, hooks/, tools/
├── memory/                   the recorded decisions: one fact per file
│   └── MEMORY.md             their index, one line per file
├── partners/
│   ├── HOUSE-RULES.md        the rules every partner reads first
│   └── queue/                one folder per lane
│       └── LANE/
│           ├── BRIEF.md      the task, with its Design section
│           ├── REPORT.md     the hand-back; its first line is the status
│           ├── NOTES.md      why each choice was made
│           └── evidence/     logs, captures, measurements
├── private/                  never inside a repository that has a remote
│   ├── drafts/               texts before the person approves them
│   ├── ledger.md             what was sent, to whom, when
│   └── hooks/                each hook's real configuration: NAME.json
└── state/
    └── hooks/NAME/           each hook's state per session, and its logs
```

`memory/` holds what was decided and why, written so that a search by content finds it.
`private/` is where the lists live that make a check useful and must never be published: the names that are never named, the identities, the allowed addresses.
The repository ships only examples of them.

## Adopt it

```sh
python3 hooks/install.py init WORKSPACE            # makes the folders above and private/hooks/NAME.json for each hook
$EDITOR WORKSPACE/private/hooks/*.json             # your own lists, names and floors; switch off what you do not want
python3 hooks/install.py check WORKSPACE           # reads every configuration as the hooks do; names what is missing
python3 hooks/install.py wire claude WORKSPACE     # prints the wiring; --write FILE merges it into a settings file
```

`init` never overwrites a file, and nothing is written outside `WORKSPACE` unless `--write` or `unwire` names the settings file.
A settings write keeps a unique backup beside that file, including when two writes happen within one second.
A workspace that already has its folders elsewhere keeps them: put their paths under `paths` in each configuration.
To leave: `python3 hooks/install.py unwire FILE` takes these hooks out of a settings file and leaves every other entry as it was.

[Wiring the hooks into a tool](TOOLS.md) has the details for Claude Code, what Codex takes today, what the other tools offer and lack, and the two git hooks.

## What every hook promises

- **It fails open, and says so.** A hook that cannot run (no configuration, a broken one, an error inside it) lets the action through, writes the reason to `errors.log` in its state folder and tells the person in one line. A broken guard never becomes a wall.
- **A refusal says what to do next.** It names the files to read, the sections that are missing or the command to run instead, and when the same command can be sent again.
- **What it enforces is the person's choice.** Every hook has `enabled`, every part of a hook has its own switch, and the edition's defaults are on.
- **Its state follows the event's identity:** the agent id, else the transcript, else the session.
  Separate lanes need separate identities from the tool; that delivery is not yet proved under Codex.
  Updates hold a lock; if it stays busy for five seconds, the action goes through with a notice and no state is changed.
- **It reads shell text as a shell would run it.** A comment and the text a command only writes to a file are not commands; a command after a comment, on lines joined by a backslash, inside a loop, a condition or a substitution, behind `bash -c` or in a here-document handed to a shell is one. It is a guard rail, not a wall.
- **Nothing private is in it.** No path of a machine, no list, no contact: each hook reads one configuration file, and that file stays in `private/`.

## Tests

```sh
python3 hooks/tests/run.py            # every hook's tests and the shared ones; python3 and git are all they need
python3 hooks/tests/run.py outreach   # one hook
sh hooks/tests/clean-machine.sh       # the whole proof, for a machine that has nothing but this repository
```

Each test makes a toy workspace in the default layout with `install.py`'s own `init`, pipes an event into the hook and reads the answer.
[`clean-machine.sh`](tests/clean-machine.sh) adds the skills check, the wiring written to a file and run, the outreach guard's refuse, read, consult, pass by hand, and the publish check over this section with the example configuration; it prints one PASS or FAIL line per step and writes only under a temporary folder.

## Add a hook, or change one

The skill [development-hooks](../skills/development-hooks/SKILL.md) has the recipe and the traps: failing open, state per session, a refusal that says what to do, a pattern that must not catch reads or the workspace's own repositories, and testing by piping.
