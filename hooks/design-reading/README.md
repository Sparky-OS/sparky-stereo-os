# design-reading

**For** anyone whose AI partner forgets the designs between sessions: the recorded designs are read before work, and read again whenever the partner's context was read cold.

## What it does

| Event | What happens |
| --- | --- |
| Session start (new, resumed, cleared, after a compaction) | The core files become required reading, and the list goes to the partner as context. |
| Before any tool, and on every prompt | In a context that has not been seen before, or after a gap longer than `gap_seconds`, the core files become required reading again. A lane also gets every memory file its prompt or its brief names, and those its subject calls for (`subject_rules`). |
| Before any tool, while a file is unread | The tool is refused with the list of what is left. The reading tools and the tools under `free_tool_prefixes` are never refused. |
| After a file is read | A required file read in full is crossed off. A read with an offset or a limit does not count, and neither does a file of the same name in another folder. |
| A prompt, while a file is unread | The list is shown as context; the prompt is not blocked. |

The refusal says what to do next: it names each file by its full path and says that each is read in full with the file-reading tool.

## Why

Daniel, 2026-11-02: "set up a hook so you are forced to read these things, specially on compactation, but, also when cache expires".
Daniel, 2026-11-12: "a very well informed, tooled and of course, that can read memories partner, no matter the class, is always better ... all of them are crutial all the partners need".

A compaction replaces the conversation with a summary, so the designs read before it are no longer in the context.
The gap stands for the tool's prompt cache having expired, after which the whole context is read again as if new; 3300 seconds is just under the hour that cache lasted on the workstation where the hook was first built, so set it to your tool's.
A lane starts with no memory at all, so its first call is the moment it reads.

## Configuration

One file, `private/hooks/design-reading.json` in the default layout; [`config.example.json`](config.example.json) shows every key.

| Key | Default | What it sets |
| --- | --- | --- |
| `enabled` | `true` | The whole hook. |
| `paths.memory`, `paths.memory_index`, `paths.queue`, `paths.state` | the default layout | Where the memory files, their index, the lanes' folders and this hook's state are. |
| `core` | two example names | The memory files every context reads. A name that does not exist in the memory folder is not demanded. |
| `also_on_subject` | one example | Lines shown as a reminder: which file to read before work on which subject. |
| `subject_rules` | one example | A pattern and the files a lane reads when its prompt or its brief matches it. |
| `gap_seconds` | `3300` | How long without a call before the reading starts again. |
| `on.session_start`, `on.first_call`, `on.gap`, `on.lane_named` | all `true` | Each trigger, switched on its own. |
| `read_tools`, `free_tool_prefixes` | Claude Code's reading tools; `mcp__` | The tools that are never refused. |
| `shell_reads` | the tool's own | Whether a plain `cat FILE` counts as reading a file in full. On by default only where the tool has no reading tool (Codex). |
| `lane_named_max` | `16` | The most files a lane's own list adds. |
| `lookup_hint` | `true` | Shown in the reading text: how to search the memory by content. `true` names the lookup of this section with the workspace's memory folder; a text replaces it; `false` hides it. |
| `state_keep_days` | `30` | How long the state of a session that is not seen again is kept. |

## How it fails

Open, and it says so.
A missing or broken configuration, an event that is not JSON, or an error inside the hook lets the tool call through, writes the traceback to `errors.log` in the hook's state folder (under `~/.local/state/sparky-stereo-hooks/design-reading/` when no state folder is known yet) and tells the person in one line.
A lane whose prompt cannot be found in the tool's own records still gets the core files; the reason goes to `errors.log`.

Logs, in `state/hooks/design-reading/`: `refused.log` (each refused call and how many files were unread), `reads.log` (each time a context finished its reading), `errors.log`.

## Try it by hand

```sh
W=$(mktemp -d) && python3 hooks/install.py init "$W" >/dev/null
printf 'A fact.\n' > "$W/memory/check-every-default.md"; printf 'A fact.\n' > "$W/memory/one-format-inside.md"
event() { printf '{"hook_event_name":"%s","tool_name":"%s","tool_input":%s,"session_id":"demo","cwd":"/"}' "$1" "$2" "$3"; }
run() { python3 hooks/design-reading/hook.py --config "$W/private/hooks/design-reading.json"; echo; }
event PreToolUse Bash '{"command":"ls"}' | run                                              # refused, with the two files
event PostToolUse Read "{\"file_path\":\"$W/memory/check-every-default.md\"}" | run
event PostToolUse Read "{\"file_path\":\"$W/memory/one-format-inside.md\"}" | run
event PreToolUse Bash '{"command":"ls"}' | run                                              # nothing: the call goes through
```

## Tests

`python3 hooks/tests/run.py design-reading` runs 21 tests in [`tests/`](tests/test_design_reading.py): the triggers, partial reads, sessions and agents kept apart, parallel reads, the switches, Codex's `cat`, and every way of failing open.
