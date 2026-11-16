# Keeping a work queue so the oldest request is not the last

**For** anyone who hands work to AI partners from a list of items, on any project: the state of the queue in one file, a row for every item with its true origin, a gate before every launch, and the traps of a queue that drifts, from our own case.
The program is the [queue-keeper hook](../../../hooks/queue-keeper/README.md); this page is the practice behind it.
Reconciling a queue that has already drifted is [a different page](queue-reconciliation.md); this one keeps it from drifting again.

## Working recipe

1. **Keep the state in one file and the history in another.** `QUEUE.tsv` has one row per item and one status per item. The journal (`ORDER.md` here) says what happened and when. Open items are found in the first, never in the second.
2. **Give every item a row before it gets a lane.** The row has the item's number, a short name, its origin, the date of the requester's words, a tier, a status, an `ahead` reason if any, the evidence for the status and the time of the last change.
3. **Let the gate decide who starts.** A free lane goes to the requester's oldest open request. Only a defect in what is shipped, a security hole and the blocker of a running publication round go ahead, and the report to the requester names each of them.
4. **Change the row in the same step as the event.** A launch sets `in-flight`. A hand-back is shown until the review. An acceptance sets `staged`, `published` or `done`, with the evidence. The journal entry for the event follows or precedes it, never replaces it.
5. **File what a lane leaves.** The lane lists its follow-ups in its hand-back; the coordinator adds one row for each with origin `follow-up` or `finding`. The lane never edits the state file.
6. **Read the queue before saying anything about it.** `hook.py next` before every statement about what is open, and in every status report the requester's oldest open requests and what took each free lane.

## The row and its origins

| Origin | What it is | Goes ahead? |
| --- | --- | --- |
| `owner` | A request in the requester's own words, dated by them | Oldest date first; among equal dates the requester's tiers |
| `security`, `breakage`, `round` | A hole, a defect in what ships, a publication round's blocker | Yes, and is said |
| `follow-up`, `finding` | Something a lane left or found | No: it waits behind every open owner request |
| `outreach`, `machinery` | Contact with another project; upkeep of the process itself | No |

The requester's date is the date of the words, not of the filing: a request restated a month later keeps its first date, and a follow-up never inherits the date or the authorship of its parent.
When the requester puts an item first, the row's `ahead` column holds the requester's words, quoted, and the gate says them every time it lets the item through.
A design that is only configuration ships at once, split off from the larger work it was filed with: it costs a lane for an hour, and leaving it behind a large interface is how defaults stay stock for weeks.

## The gate, and why each jump exists

The gate is the one place where an item takes a lane, so it is the one place the rule is kept ([the nine lines](../../../hooks/queue-keeper/README.md#the-gate)).
- **No row, no lane.** Work that runs outside the queue is work nobody can see.
- **A finished item is not started again.** New work on it is a new row, so the old row keeps its evidence.
- **Security, breakage, a round's blocker.** Each costs more by waiting than by being named. The three are the only jumps; a fast, high-value reply from a contact is not one.
- **The requester's request starts among the oldest few** (`slots`, the number of lanes you have), or when it is already started, or when the requester said it goes first.
- **Everything else waits while an owner request waits.** Otherwise the newest number takes every free lane.
- **Hand-backs waiting for a review are shown first.** A review costs no lane, so it comes before a new lane; the configuration may refuse a dispatch while reviews are owed.
- **A state the gate cannot read refuses the dispatch,** with the way to rebuild the file. A gate that lets work through when it cannot look is the failure the queue exists to end.

## At a launch, a hand-back and an acceptance

| Moment | The row | Shown or refused |
| --- | --- | --- |
| Launch | `in-flight`, set by the hook after the dispatch succeeded | The gate's reason, or the exception it names |
| Hand-back | Stays `in-flight` until reviewed; the lane's report starts `STATUS: review` | Listed at every prompt under hand-backs waiting |
| Review accepted | `staged`, `published`, `done` or `merged`, with the evidence; a row for each follow-up | An acceptance the journal names whose row did not change is owed: shown at every prompt, and the next dispatch is refused |
| Review sent back | `in-flight` again with the reason in the evidence | Nothing owed |
| Lane died | Stale: in flight, no running marker, nothing changed for 12 hours | Listed as stale; set it or relaunch it |

Staged, published and merged are different facts: a staged package is not published, and a merge is not a package.
Set the one the evidence shows.

## How a queue drifts: the traps

- **Symptom:** the requester's earliest requests were never started while item numbers passed six hundred. **Cause:** an item's number is its filing number; every free lane went to the newest finding, the follow-up of a running lane or the work a contact had just asked for. **Fix:** the gate, with the requester's oldest open requests shown at every prompt. **How found:** the requester asked why item 20 was not done when the numbers were at 500, and the lane folders of items 19 to 23 held a brief and nothing else.
- **Symptom:** nobody can say what is open. **Cause:** the journal had grown to 3,500 lines with status words inside entries ("queued", "running") written once and never revised. **Fix:** one state file; the journal is history only. **How found:** the line saying RUNNING for a lane whose report had said accepted for weeks.
- **Symptom:** a careful list of the requester's requests exists and is wrong. **Cause:** it was made once, as a lane's hand-back, and kept in the lane's folder: a snapshot is not a queue. **Fix:** the same data as the live state file, read by the hook. **How found:** the list's date against the acceptances after it.
- **Symptom:** most free lanes go to things the requester never asked for. **Cause:** every finished lane leaves three or four follow-ups, and they were launched as filed, carrying their parent's authority. **Fix:** an `origin` on every row; a follow-up waits behind the requester's requests. **How found:** counting origins: of 714 rows, 418 were findings and follow-ups and 197 were the requester's.
- **Symptom:** the gate lets a lane through against the wrong row, or refuses a right one. **Cause:** a lane folder called `kernel-build-17` was read as item 17 because the trailing number was tried first. **Fix:** the folder's name is matched against the rows' names first and the trailing number only after; a configuration maps the odd folder by hand. **How found:** a test with two rows, item 17 and a lane of that name.
- **Symptom:** the audit lists 103 old lane folders with no row. **Cause:** early lanes were named by topic and their rows by another word. **Fix:** `lane_rows` in the configuration maps folder to row; the audit keeps listing the rest until each has a row or is ignored on purpose. **How found:** `hook.py audit` on the real state.
- **Symptom:** the journal says accepted and the queue still says in flight. **Cause:** a reminder before the command cannot see whether the row changes afterwards. **Fix:** a hook after the journal write reads the text, finds the items it calls accepted, and keeps the acceptance owed until the row's status, time or evidence changes. **How found:** by following the order of events: the reminder runs before the command, the row change (or its absence) comes after. A test that writes the journal first and changes the row second, or never, proves both ends.
- **Symptom:** a dispatch another hook refused left its row in flight. **Cause:** the row was marked when the gate passed, before the tool ran. **Fix:** the gate decides before, the row changes after the tool succeeded. **How found:** reading the order in which the two hooks run on a dispatch.
- **Symptom:** the journal check flags items nobody accepted. **Cause:** the text has dates and times (`2026-11-16 18:24`), and numbers that match a row id. **Fix:** an item counts only next to an acceptance word, in one of three shapes (`ORDER 5 accepted`, `5 accepted`, `accepted: 5`), and only if its row can still be accepted. A false hit is settled by setting the same status again with the reason in the evidence. **How found:** a test line made only of a date and the word merged.
- **Symptom:** a lane that died is listed in flight for days. **Cause:** nothing moves the row when the lane stops. **Fix:** an in-flight item whose lane has no running marker and whose folder has been silent for twelve hours is shown as stale at every prompt. **How found:** by asking what moves a row when a lane stops, and the answer was nothing. On the real state the audit found no stale item the day it was first run, because only the three running lanes were in flight; the rule is proved on a fixture with an aged folder.
- **Symptom:** with the state file gone, every lane was refused as having no row, and an error inside the hook let every dispatch through. **Cause:** the first version read a missing file as an empty queue, and a hook that fails open passes what it could not judge. **Fix:** an unreadable or foreign state file is its own refusal that names the file and the command that rebuilds it, unless the configuration says `tell`, which lets the dispatch go ahead and says so. **How found:** reading how the first version loaded the file, then a test with the file removed.
- **Symptom:** every report with `STATUS: review` is counted as waiting for a review. **Cause:** accepted reports keep their old label ([the reconciliation page](queue-reconciliation.md#traps)). **Fix:** only rows in flight or in review whose report says review count; a finished row with an old label is no disagreement. **How found:** the audit against a queue where staged items still had `STATUS: review` reports.

## Start a queue in five minutes

```sh
python3 hooks/install.py init WORKSPACE                 # makes partners/queue/QUEUE.tsv (the header), the lane folders' place and the hook's configuration
python3 hooks/queue-keeper/hook.py --config WORKSPACE/private/hooks/queue-keeper.json add 1 first-job owner 2026-01-05 own "what was asked, in the requester's words"
python3 hooks/queue-keeper/hook.py --config WORKSPACE/private/hooks/queue-keeper.json add 2 second-job owner 2026-01-09 own
python3 hooks/queue-keeper/hook.py --config WORKSPACE/private/hooks/queue-keeper.json next
python3 hooks/install.py wire claude WORKSPACE --write ~/.claude/settings.json      # or: wire codex WORKSPACE
```

1. Edit `private/hooks/queue-keeper.json` only for what differs from the example: the requester's origin name if it should be a name, the tiers, `slots`, and `launch_patterns` for the script you start lanes with.
2. Add one row for every item the requester has asked for, dated by the requester's words. If the date is lost, say so in the evidence; do not invent one.
3. Make each lane's folder `NAME-ID` with a `BRIEF.md`. A dispatch that names the brief now passes the gate; a lane with no row is refused.
4. At each hand-back, `set ID review`; at each acceptance, `set ID staged "evidence"`, and add the follow-ups as rows.
5. Run `hook.py audit` at the end of every day until it prints `queue audit: nothing found`.

## Rules

- One state file, one status per item. The journal is history.
- The requester's oldest open request goes first; the exceptions are three, and each is named.
- The row changes in the same step as the event, and the hook says when it did not.
- A follow-up is never filed as the requester's.
- A queue is read, not remembered: before any statement about what is open, run `next`.
