# brief-and-handback

**For** whoever coordinates lanes: a lane is not sent out without its design and its skill named, and its report does not come back without the sections that prove the reading.

## What it does

| Event | What happens |
| --- | --- |
| Before a dispatch (the tool that starts another agent) | Each brief the dispatch names, a `BRIEF.md` or `AGENTS.md` in a lane folder of the queue, is read. The dispatch is refused when the brief lacks a `## Design` section, when that section names no memory file or quotes nothing, when it has no `## The skill to leave behind` section, or when it does not ask for "Design check" and "Skill changes" in the hand-back. Every problem is named with the brief's path. |
| Before a dispatch whose brief is complete | A one-line reminder goes along as context. |
| Before a brief is written | The memory files that hold the brief's subject are shown as context, found by content from the lane folder's name and the brief's title ([`design_lookup.py`](../lib/design_lookup.py)). |
| Before a hand-back (Claude Code's `SubagentHandback`, or a final `REPORT.md` written whole into a lane folder) | The report must start with a status line and carry "Design check", "Corpus consulted" and "Skill changes". It is refused with what is missing, at most `max_refusals` times; after that it goes through, the gap is logged and the person is told. |
| Session start, in the coordinator's own session | The lanes whose `REPORT.md` starts with `STATUS: review` or `STATUS: blocked` and changed in the last days are listed. |

A dispatch that names no brief passes: a quick search needs no brief.

## Why

Daniel, 2026-11-06: "we register skills as we go to make the next work easier to tackle and by doing so, we do the hard consuming part once and keep enhancing as we go, each time better and better".
Daniel, 2026-11-12: "a very well informed, tooled and of course, that can read memories partner, no matter the class, is always better ... all of them are crutial all the partners need".

A brief that names the work without the design it follows comes back built on a habit from elsewhere.
A hand-back without its reading list cannot be checked against the rules it claims to follow, so it is sent back.
A lane that waits for a review after a compaction is forgotten unless something lists it.

## Configuration

One file, `private/hooks/brief-and-handback.json`; [`config.example.json`](config.example.json) shows every key.

| Key | Default | What it sets |
| --- | --- | --- |
| `enabled` | `true` | The whole hook. |
| `on.dispatch`, `on.dispatch_reminder`, `on.brief_lookup`, `on.handback`, `on.waiting_lanes` | all `true` | Each part, switched on its own. |
| `paths.queue`, `paths.memory`, `paths.memory_index`, `paths.state` | the default layout | Where the lanes' folders and the memory are. |
| `brief_pattern`, `report_pattern` | `BRIEF*.md` or `AGENTS.md`; `REPORT.md` | Which file names in a lane folder are a brief and a report. |
| `brief.headings` | `Design`, `The skill to leave behind` | The sections a brief must have. A heading matches with or without "The", singular or plural. |
| `brief.design_names_a_memory`, `brief.design_quotes` | `true` | Whether the Design section must name a memory file and quote something. |
| `brief.must_say` | `Design check`, `Skill changes` | Words the brief must ask the hand-back for. |
| `handback.first_line`, `handback.must_have` | `^STATUS: `; three section names | What a hand-back must carry. |
| `handback.final_status` | `review`, `blocked` or `done` | A `REPORT.md` is checked only when its first line says it is final. |
| `handback.max_refusals` | `2` | After this many refusals in one session the hand-back goes through. |
| `waiting_lanes.status`, `.max_age_days`, `.max_listed` | review or blocked; `3`; `12` | Which lanes are listed at session start. |
| `lookup_also`, `lookup_max_files` | none; `8` | More files for the design lookup to search (a decisions log), and how many results it shows. |

## How it fails

Open, and it says so: any failure inside the hook lets the tool call through, is written to `errors.log` and told to the person in one line.
A brief that cannot be read stops the dispatch, because a lane would then start from a path that does not exist.
A hand-back is never lost to this hook: the refusals are counted per session and stop at `max_refusals`.

Logs, in `state/hooks/brief-and-handback/`: `refused.log`, `passed.log` (a hand-back let through with what it still lacked), `errors.log`.

## Try it by hand

```sh
W=$(mktemp -d) && python3 hooks/install.py init "$W" >/dev/null
mkdir -p "$W/partners/queue/demo" && printf '# A bare brief\n' > "$W/partners/queue/demo/BRIEF.md"
printf '{"hook_event_name":"PreToolUse","tool_name":"Agent","tool_input":{"prompt":"Your brief is %s"},"session_id":"demo","cwd":"/"}' \
  "$W/partners/queue/demo/BRIEF.md" | python3 hooks/brief-and-handback/hook.py --config "$W/private/hooks/brief-and-handback.json"
```

The answer is a refusal that lists the four things the bare brief lacks.

## Tests

`python3 hooks/tests/run.py brief-and-handback` runs 18 tests in [`tests/`](tests/test_brief_and_handback.py).
