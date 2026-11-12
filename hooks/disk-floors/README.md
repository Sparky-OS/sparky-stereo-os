# disk-floors

**For** anyone who builds on a machine other work shares: the free space of each folder is said in GiB against its floor before a command that fills a disk, and all the time while a floor is crossed.

## What it does

| Event | What happens |
| --- | --- |
| Before a shell command that asks about space (`df`, `du`, `lsblk`, `findmnt`) or writes a lot (a recursive copy, `rsync`, `dd`, a clone, an image pull or build, an unpack, a package build, a download to a file) | The free space of every folder in `floors_gib` is shown as context, each against its floor. |
| Before any shell command, while a folder is under its floor | The same line, with the folder under its floor first and what to do about it, at most once every `remind_seconds`. |
| Before a write-shaped command, while a folder is under its floor | What `below_floor` says: told (`context`), put to the person (`ask`) or refused (`deny`). Commands that free space or only look are never refused. |

The figures are GiB free, never a percentage: a large disk at 93 % can hold more free space than a small one at 80 %.

## Why

A build that fills a disk stops every other piece of work on the machine, and the person's desktop with it.
[Unattended agent runners](../../skills/ai-partners/references/agent-runners.md) has the measured case: one workspace-wide test run wrote 26 GB at about 143 MB/s and filled the root file system on 2026-10-22.
A floor checked only before a build is passed during it, so the figures come back on every disk-shaped command.

No words of Daniel's were given to this work for this hook.
The default answer under a floor, `context`, is what the hook does on the workstation it comes from; whether a write under a floor is refused is a choice for each workspace.

## Configuration

One file, `private/hooks/disk-floors.json`; [`config.example.json`](config.example.json) shows every key.

| Key | Default | What it sets |
| --- | --- | --- |
| `enabled` | `true` | The whole hook. |
| `floors_gib` | `/` 12, the workspace 2, a scratch folder 2 | Each folder to measure and its floor in GiB. `install.py init` writes the workspace's real path, and the scratch folder when `--scratch` names one. |
| `below_floor` | `context` | What a write-shaped command gets while a folder is under its floor: `context`, `ask` or `deny`. |
| `remind_seconds` | `600` | How often the line comes back on ordinary commands while a floor is crossed. |
| `asks`, `writes` | the lists in [`hook.py`](hook.py) | Patterns tried at the start of each simple command of the shell line. |

## How it fails

Open, and it says so: a failure inside the hook lets the command through, is written to `errors.log` and told to the person in one line.
A configuration without floors is such a failure: the hook says that `floors_gib` is empty instead of measuring nothing.
A folder that does not exist is named as "Not measured" in the same line as the others.

Logs, in `state/hooks/disk-floors/`: `refused.log` or `asked.log` when `below_floor` is `deny` or `ask`, `errors.log`.

## Try it by hand

```sh
W=$(mktemp -d) && python3 hooks/install.py init "$W" >/dev/null
printf '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"df -h"},"session_id":"demo","cwd":"/"}' \
  | python3 hooks/disk-floors/hook.py --config "$W/private/hooks/disk-floors.json"
```

## Tests

`python3 hooks/tests/run.py disk-floors` runs 8 tests in [`tests/`](tests/test_disk_floors.py).
They use a floor of 0 GiB, which is never crossed, and one of a million GiB, which always is, so they need no particular disk.
