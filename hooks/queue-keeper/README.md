# queue-keeper

**For** anyone who hands work to AI partners through a queue: the queue's state lives in one file with one status per item, the person's own requests are served oldest first, and no lane starts that the queue does not allow.

## What it does

| Event | What happens |
| --- | --- |
| Session start, and every prompt | The state is shown. First the hand-backs waiting for a review and the acceptances not yet written to the state, then the requester's open requests oldest first (`context_open_listed` of them, and how to see the rest), what is in flight, and the items in flight whose lane is not running. |
| Before a dispatch (a subagent whose prompt names a lane's `BRIEF.md` or `AGENTS.md`) and before a launch command (`launch_patterns`) | The lane's row must pass [the gate](#the-gate). A lane with no row, a finished item, a request that jumps its elders and an acceptance still owed are refused, each with the reason and the command that fixes it. |
| After a dispatch or a launch that succeeded | The lane's row becomes `in-flight`, with the time. The gate writes nothing; a dispatch another hook refused changes no row. |
| After a write to the journal | The text written is read for items it calls accepted (`acceptance_patterns`). An item whose row still says `open`, `in-flight` or `review` is owed: the acceptance is not complete until the row changed. It is shown at every prompt of that session and refuses a dispatch (`owed_acceptance`) until the row's status, time or evidence changed. |

A lane's own calls are never judged (`lanes_exempt`): a lane does not dispatch and does not write the queue; the coordinator's session does.
Hand-backs and stale items are shown, not refused, unless the configuration says `handbacks_waiting: refuse`.

## The state file

One file, `QUEUE.tsv` beside the lane folders by default (`state_file`), one header line and one row per item, fields separated by tabs:

| Column | Holds |
| --- | --- |
| `id` | The item's number with its letter: `20`, `156b`. Matches `id_pattern`. |
| `name` | A short name; the lane folder is `NAME` or `NAME-ID`. |
| `origin` | Where the item came from: `owner` (a request of the person the queue serves; `owner_origin` renames it), `follow-up` and `finding` (a lane left it), `security`, `breakage`, `round` (a publication round's blocker), `outreach`, `machinery`. |
| `asked` | For an owner request the date of the requester's words, which is its place in the line; for the others the filing date or empty. `YYYY-MM-DD`. |
| `tier` | The requester's order among requests of one date: `tiers`, first to last. |
| `status` | One of `statuses`. Three the machinery depends on: `open`, `in-flight`, `review`. Four end an item for good (`closed_statuses`): `published`, `done`, `merged`, `superseded`. The rest (`staged`, `parked`, `waiting-owner`, `unknown`) are free. |
| `ahead` | Empty, or the requester's recorded words that put this item ahead of older requests. |
| `evidence` | What shows the status: a commit, a version, a stage, `brief only`. |
| `updated` | When the row last changed, `YYYY-MM-DDTHH:MMZ`. |

The journal (`ORDER.md` by default, `journal`) says what happened and when; it never says what is open.
A follow-up a lane leaves gets its own row with its true origin; it is never filed as a request of the requester.

## The gate

A dispatch or launch of lane `L` passes when every line holds; the first that does not is the refusal.

1. **The state is readable.** A missing file, an unreadable one or another header is refused with the way to rebuild it (`on_missing_state: refuse`, the default) or told while the dispatch goes ahead (`tell`). It is never passed silently.
2. **No acceptance is owed** in this session (`owed_acceptance`: `refuse` as shipped, `tell`, or `off`).
3. **`L` has a row.** The folder is a row's `name` or `NAME-ID`, else a row named in `lane_rows`, else the row whose id the folder name ends in (`match_lane_by_id`). The name is tried first, so a lane called `kernel-build-17` is not item 17. Nothing runs outside the queue.
4. **The row's origin is one the schema knows.**
5. **The item is not finished** (`closed_statuses`). New work on a finished item gets its own row.
6. **`security`, `breakage` and `round` go ahead** (`jump_origins`) and the gate says so, so the report to the requester names the exception.
7. **An owner request starts** when it is already started (its status is not `open`), or among the `slots` oldest open requests of the requester, or it has an `ahead` reason, which is then said. Otherwise it is refused with the older requests named.
8. **Anything else** (`follow-up`, `finding`, `outreach`, `machinery`, `unknown`) starts when it has an `ahead` reason or when no owner request is waiting. Otherwise it is refused with the oldest requests named.
9. **Hand-backs waiting for a review** are told (`handbacks_waiting: tell`), refused (`refuse`) or left out (`off`). The lane being relaunched after its own review is not counted.

Why each jump exists: a defect in what is shipped, a security hole and the blocker of a running round cost more by waiting than by being named; everything else would let the newest number take every free lane, which is what the queue is there to stop.
The requester decides what jumps: `ahead` records the words, and the gate then says them.

## Shown and refused, by what the folders say

- **A hand-back waiting for a review:** a row in `in-flight` or `review` whose lane's `REPORT.md` starts with `report_handed_back` (`STATUS: review` or `blocked`), or a row in `review` with no report. It stays in the list at every prompt until the row is set.
- **Stale:** a row in `in-flight` whose lane is not running and whose row has not changed for `stale_hours` (12). A lane runs when its folder holds the marker file (`running_marker`, `.active`) or something in the folder changed within `stale_hours`. An item in flight with no lane folder at all is stale once its row is old.
- **An acceptance owed:** see the table above. A journal write is a Write or Edit of the `journal` file, a Codex patch to it, or a shell line that appends to it (`>>`, `tee`, a here-document). A whole-file Write is read by its last `journal_scan_chars` (6000) only. To settle a line that was not an acceptance, set the same status again with the reason in the evidence.

## Configuration

`config.example.json` has every key with the edition's defaults; `private/hooks/queue-keeper.json` in the default layout is the real one.

| Key | Default | Meaning |
| --- | --- | --- |
| `paths.queue` | `partners/queue` | The folder of the lane folders; the state file and the journal are beside them by default |
| `state_file`, `journal` | `queue:QUEUE.tsv`, `queue:ORDER.md` | Paths, relative to the workspace, absolute, or `queue:NAME` |
| `owner_origin`, `owner_name` | `owner`, `the requester` | The origin value of the requester's requests, and the name the messages use for them |
| `origins`, `jump_origins`, `tiers`, `statuses`, `closed_statuses` | see the example | The schema's words |
| `slots` | `4` | How many of the requester's oldest open requests may start (the number of lanes the work has) |
| `on_missing_state` | `refuse` | `refuse` or `tell`, when the state file cannot be used |
| `owed_acceptance` | `refuse` | `refuse`, `tell` or `off` |
| `handbacks_waiting` | `tell` | `tell`, `refuse` or `off`, for a dispatch while reviews are owed |
| `stale_hours`, `running_marker` | `12`, `.active` | What counts as a running lane |
| `lanes_exempt` | `true` | Calls made inside a lane (the event has an agent id) are not judged |
| `launch_patterns` | one example | Regular expressions with one group, the lane folder, matched on the words of a shell command up to its first quoted text, so `echo "launch-lane.sh queue/x"` is no launch |
| `brief_pattern` | `BRIEF*.md`, `AGENTS.md` | The file names a dispatch names |
| `lane_id_pattern`, `match_lane_by_id`, `lane_rows` | see the example | How a folder finds its row; `lane_rows` maps a folder to a row id by hand |
| `acceptance_patterns` | three | Regular expressions with a group `id`: `ORDER 5 accepted`, `5 accepted`, `accepted: 5` |
| `report_handed_back`, `report_working`, `report_accepted` | `STATUS:` lines | How a lane's report first line is read |
| `audit_folders`, `audit_ignore` | `briefed`, `[]` | Which lane folders `audit` expects a row for: `briefed` (a brief, an agents file or a report, or the marker), `active` (the marker) or `all`; and folders to leave out |
| `on` | all `true` | `session_start`, `prompt`, `gate`, `mark_in_flight`, `journal` |

## The command line

```sh
python3 hooks/queue-keeper/hook.py --config FILE init                      # a new state file: the header only
python3 hooks/queue-keeper/hook.py --config FILE add ID NAME ORIGIN ASKED TIER [EVIDENCE]
python3 hooks/queue-keeper/hook.py --config FILE set ID STATUS [EVIDENCE]  # a launch, a hand-back, an acceptance, a parking
python3 hooks/queue-keeper/hook.py --config FILE ahead ID "THE OWNER'S WORDS"   # no words removes the reason
python3 hooks/queue-keeper/hook.py --config FILE next [N]                  # what a session start shows
python3 hooks/queue-keeper/hook.py --config FILE show ID
python3 hooks/queue-keeper/hook.py --config FILE gate LANE-FOLDER          # ALLOW or REFUSE with the reason
python3 hooks/queue-keeper/hook.py --config FILE audit
```

`--config FILE` may stand anywhere, and may be left out when `SPARKY_HOOKS_CONFIG_DIR` or `SPARKY_WORKSPACE` names it, as for every hook.
Changes read the file again behind a lock and write it by replacing it, so two writers lose no row.
Exit status: 0 done or allowed; 1 refused, or `audit` found something; 2 the state or the configuration cannot be used.

`audit` prints, one line each: a row the schema does not allow (origin, status, tier, an id or a date out of shape, an id twice, a line with the wrong number of fields); an open row whose report says `STATUS: working`; an item in flight whose report says accepted or done, or handed back and not reviewed; a finished row whose lane folder still has the running marker; an item in flight with no lane running; and every lane folder `audit_folders` expects a row for that has none.
An old `STATUS: review` on a row that was accepted is not a disagreement: a report keeps its label.

## How it fails

- **A missing, unreadable or foreign state file is the one failure that is not let through.** The edition's default is to refuse the dispatch and say how to rebuild the file, because a gate that passes when it cannot look is no gate. `on_missing_state: tell` lets it go ahead with the reason in the context.
- **Any other failure fails open, and says so,** as every hook here does: the action goes ahead, `errors.log` in the state folder has the reason, and the person is told in one line.
- **A row that could not be marked in flight** after a dispatch is said in the context; the dispatch itself already ran.
- **What it does not see:** a journal written by a program other than the tool call (a script that rewrites it), a lane named only by a path the patterns do not know, and a dispatch whose prompt does not name a brief. It is a guard rail, not a wall.
- A dispatch whose prompt merely mentions another lane's brief path is judged for that lane too; name briefs only for the lane being started.
- The owed acceptances belong to the session that wrote the journal, as the hooks' state does.

## Try it by hand

```sh
python3 hooks/install.py init WORKSPACE            # makes partners/queue/QUEUE.tsv with its header, and this hook's configuration
python3 hooks/queue-keeper/hook.py --config WORKSPACE/private/hooks/queue-keeper.json add 1 first-job owner 2026-01-05 own "the first request"
mkdir WORKSPACE/partners/queue/first-job-1 && echo '# first job' > WORKSPACE/partners/queue/first-job-1/BRIEF.md
python3 hooks/queue-keeper/hook.py --config WORKSPACE/private/hooks/queue-keeper.json gate first-job-1
printf '{"hook_event_name":"UserPromptSubmit","prompt":"go","session_id":"s","cwd":"."}' | python3 hooks/queue-keeper/hook.py --config WORKSPACE/private/hooks/queue-keeper.json
```

The last line prints the answer a tool would receive: the open requests and what is in flight.

## Why

A queue stored as a log fails in a known way: the log grows, status words are written once inside entries and never revised, the newest numbers take every free lane, and the oldest requests of the person the queue serves are never started while the numbers pass six hundred.
The fix is the one this hook applies: the state apart from the journal, one status per item, the origin of every item recorded truthfully, and a gate at the one moment an item takes a lane.
[Keeping a work queue](../../skills/ai-partners/references/keeping-a-queue.md) has the whole story with each trap, and how to start a queue in five minutes.

The design of the gate's nine lines, of the stale rule and of the owed acceptance is the edition's own.
The rule they serve is short: a queue serves who came first.
