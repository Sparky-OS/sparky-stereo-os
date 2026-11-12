# outreach-guard

**For** anyone who sends work to other projects with an AI partner: nothing leaves for another project until the rules for it were read in this session.

## What it does

| Event | What happens |
| --- | --- |
| After a file is read in full | Its time is noted when it lies in the memory or the skills folder, or is one of `always_read`. |
| After a consult of the reference index (a tool of `consult_tools`) | Its time is noted. |
| Before a shell command that sends something to another project | Refused until this session has, within `window_seconds`, read in full every file of `always_read` and the contrib skill of the project the command names, and has consulted the reference index. The refusal lists exactly what is missing and ends with "Then send the same command again." |
| The same command, once all of it is done | It passes, with the filing checklist as context. |

What counts as sending: `gh pr` and `gh issue` with create, comment, review, edit, close, reopen or merge; a `gh api` write; a `curl` write to a forge; `git send-email` and the configured mail commands; `reportbug` without `-o`; and a `git push` whose remote is another project's forge or a fork of another project.
For a push that names only a remote, the hook asks git for that remote's address in the folder the command runs in.

What passes without any reading: commands on the workspace's own repositories (`own_owners` with `own_repos`, and `own_urls`), a pull request inside one of our own forks when it is named with `--repo`, every read (`gh pr view`, `git fetch`, a `curl` without a body), and local work.
Text that a command only writes to a file is not a command: the body of `cat > file <<'EOF'` is skipped, and the body of `bash <<'EOF'` is read.

## Why

Daniel, 2026-11-12: "I should not have to ask you to load and use proper skills, and memories, partner".
The same day, on this hook: "I asked for the hook several times at this point - go partner, do it".
And on the reference index: "I left one default out on purpouse - qdrant consults where we have corpus about".

Each rule the guard asks for was already written down in a skill.
What failed was the reading at the moment of sending.
The window is four hours, the value of the workstation where the guard was first built; no measurement stands behind the number, so set your own.

## Configuration

One file, `private/hooks/outreach-guard.json`; [`config.example.json`](config.example.json) shows every key.

| Key | Default | What it sets |
| --- | --- | --- |
| `enabled` | `true` | The whole hook. |
| `paths.memory`, `paths.skills`, `paths.state` | the default layout | Where the memory, the skills and this hook's state are. |
| `window_seconds` | `14400` | How long a read and a consult stay good. |
| `always_read` | the outreach skill and one example memory file | Files read before anything is sent: `skills:NAME/SKILL.md` and `memory:FILE.md` are taken from those folders of the layout, any other path from the workspace, or absolute. A file that does not exist is not demanded; `install.py check` names it and the hook logs it. |
| `projects` | thirteen patterns | What in a command or in a remote's address names a project, and the contrib skill that goes with it. |
| `require_consult`, `consult_tools` | `true`; one example tool name | Whether a consult is asked for, and which tools count as one. With no tool listed, none is asked for. |
| `own_owners`, `own_repos`, `own_urls` | placeholders | The accounts and projects that are ours. A fork of another project under our account is not in `own_repos`: a push to it can update an open pull request. |
| `forges` | eight hosts | Hosts where a write or a push reaches another project. |
| `mail_commands` | three | Programs that send mail. |
| `resolve_remotes` | `true` | Ask git for a remote's address. When off, or when git gives none, a remote named in `fork_remote_names` counts as a fork. |
| `checklist` | eight lines | What is shown when the command passes. |
| `lookup_hint` | `true` | The memory lookup shown in the refusal: `true` for this section's own, a text to replace it, `false` to hide it. |

## How it fails

Open, and it says so: a failure inside the hook lets the command through, is written to `errors.log` and told to the person in one line.
The guard reads shell text; it is a guard rail, not a wall.
A program that hides a command where no reader of shell text finds it (inside a script file, behind an alias) is not seen.

Logs, in `state/hooks/outreach-guard/`: `refused.log` and `passed.log` (the reason and the first 200 characters of each command), `errors.log`.
These are summaries, not complete replay inputs; [the log trap](../../skills/development-hooks/SKILL.md#traps) explains what to retain privately when a decision needs investigation.

## Try it by hand

```sh
W=$(mktemp -d) && python3 hooks/install.py init "$W" >/dev/null
printf 'One subject per request.\n' > "$W/memory/how-we-write-upstream.md"
C="$W/private/hooks/outreach-guard.json"; S=skills
event() { printf '{"hook_event_name":"%s","tool_name":"%s","tool_input":%s,"session_id":"demo","cwd":"/"}' "$1" "$2" "$3"; }
run() { python3 hooks/outreach-guard/hook.py --config "$C"; echo; }
SEND='{"command":"gh pr create --repo FFmpeg/FFmpeg --title x"}'
event PreToolUse Bash "$SEND" | run                                                        # refused: three files and a consult
for f in "$PWD/$S/upstream-outreach/SKILL.md" "$PWD/$S/contrib-ffmpeg/SKILL.md" "$W/memory/how-we-write-upstream.md"; do
  event PostToolUse Read "{\"file_path\":\"$f\"}" | run; done
event PreToolUse Bash "$SEND" | run                                                        # refused: only the consult is left
event PostToolUse mcp__reference__consult_knowledge '{"query":"x"}' | run
event PreToolUse Bash "$SEND" | run                                                        # passes, with the checklist
```

Run it from the top of this repository, so that `skills/` is the real skills folder.

## Tests

`python3 hooks/tests/run.py outreach-guard` runs 17 tests in [`tests/`](tests/test_outreach_guard.py): the refuse, read, consult, pass sequence, the window closing, eighteen commands that send, eight on our own repositories and sixteen that read or work locally, text written to files, and Codex reading with `cat`.
