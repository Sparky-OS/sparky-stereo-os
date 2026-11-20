---
name: working-practices
description: >-
  How a piece of work is placed, run and finished on the edition, for people and AI partners alike: where each kind of
  thing goes (clones, scratch, stage, evidence, notes), which disk takes the work and how to move it when one fills,
  the order ship, then clean, then hand back, what shipped means (a stage with sums and a .keep, verified bundles, the
  evidence), what to read before asking (the shared memory, the local reference index), background jobs that must end
  with you, the Kept section, and the check run before a hand-back. Load it right after sparky-stereo, before the first
  clone, build or download, and when a disk fills, a task stops at a floor, work exists only in a scratch clone, a
  container or image is left behind, or a lasting file sits in a temp folder.
---

# Working practices: where things go, which disk, ship then clean then hand back

**Check freshness first.**
Written on 2026-11-15 by Claude Sonnet 5.5 (ORDER 591) from the hand-backs of the lanes of 25 October to 15 November 2026 and the rules they were measured against.
The figures a workspace sets (disk floors, the folders for scratch and stage) are that workspace's own rules and win over any figure here.

Daniel, 2026-11-15, on why this is the first skill after the contract: the disks are free to be used "as long as we ship online in the end and then clean the space for the next partner, that's good practices"; it "should be a default skill always loaded", with where things go, and the practices "should be enforced at some level to the partners".
Daniel, 2026-10-15 and 2026-10-26, on the references: "one memory for all instances"; "you and other partners shall and should consult qdrant always - it has reference info".
A partner who has read the memory and the index has already been told most of what it would ask.

## Working recipe

Read this at the start of a task, then again before you hand back.

1. **Read before you ask.**
   - The shared memory index and every topic the brief names, in full; then search the memory by content, not by file name (`design-lookup.py PACKAGE FEATURE WORDS` where the workspace has it), because a design usually lives in a topic named after a principle.
   - The skills the brief names, with their references and lessons files; `sparky-stereo-skills find "<symptom>"` when none is named.
   - The local reference index, before a web search and before writing a fact from recall ([ai-partners](../ai-partners/SKILL.md#reference-knowledge-local-first)): `consult_knowledge` takes the collections as one comma-separated string, and a JSON array silently answers empty.
   - A question for the person goes out only when no recorded line answers it.
2. **Put each thing where it lasts or where it goes.** [The table](#where-each-thing-goes) below. Nothing lasting goes in a folder named temp, in the home folder or on a network share.
3. **Measure the disk, then pick the one with room.** `df -B1` on the folders you will fill, before a copy, a clone, an image pull or a build over 2 GB. The work goes to the solid-state disk that has room, and moving scratch there is yours to do, not a reason to stop ([the disks](#the-disks)).
4. **Write down what you create as you create it.** One line in `.artifacts` per image (`name:tag`) and per folder (absolute path) outside the lane folder, each named after the lane or its short prefix, so that whoever cleans afterwards finds it ([the file](#artifacts-and-keep)).
5. **Long jobs end with you.** Start them with the shell tool's background mode, never a bare `&` in a short call; keep the PID; one waiter per event, with a timeout; stop every loop, watcher and container you started by PID or literal name before you hand back.
6. **Ship, then clean, then hand back, in that order** ([the order](#ship-clean-hand-back)).
7. **Run the lane check** before the hand-back and put its output in the report: `lane-check.py LANE_FOLDER` in the workspace's partners folder reads the folder and says pass or what is wrong, line by line; exit status 0 only when every line passes. A check that cannot run is a failure with its reason, never a pass.
8. **Hand back with a Kept section** that lists what is left, each item with its path or name, its size measured now and why it stays ([the section](#the-kept-section)).

## Start a build or test container so its crashes stay inside

Set the workspace's Docker socket in `DOCKER_HOST` before the first container.
Record the time before starting it, keep the program's exit status, and use a core limit of exactly 1 on the outer Docker command:

```sh
started=$(date --iso-8601=seconds)
status=0
docker run --rm --pull=never --ulimit core=1 --cpus 4 --platform linux/amd64 \
  --network none --user "$(id -u):$(id -g)" \
  "${IMAGE:?select the test image}" /path/to/test || status=$?
printf 'container exit status: %s\n' "$status"
coredumpctl list -q --since "$started"
```

Use the network only when the case needs it, and keep test inputs and outputs in the workspace's allowed mounts.
Apply the same core flag to `docker create`, Python argument lists and shared argument helpers.
Put it on the launcher: an inner shell cannot raise a hard limit already set to zero.
The empty crash query is expected; a record belonging to this container is a failed isolation check even when no core file was stored.
Read the container's own result as well: suppressing the host's crash helper never makes an aborted program successful.
A link gate reports a nonzero application exit as a note when loading and binding succeeded; a dynamic-loader error remains a finding.

The [crash trap](../stereo-proof-rig/SKILL.md#traps-that-fooled-us) gives the symptom, cause, correction and the measured control: the kernel ignores zero for a piped core helper, whereas exactly 1 suppresses that helper.
Do not rerun the zero-limit crash control on a person's desktop.
Debug an expected crash under a debugger inside the container and keep its diagnosis with the test result.

From the distribution build checkout, run `python3 sparky-os/tests/supply-chain/check-container-core.py` or `bash sparky-os/tests/supply-chain/test-wiring.sh` before starting builds.
The check reads tracked shell and Python launchers, continuations and referenced core-limit arrays without starting a container.
Its regression cases reject a missing flag, a zero flag, a protected neighbouring launcher and a flag hidden in the container's command.
It failed on the earlier tree and passed after the launchers were corrected; a newly constructed launch form needs a corresponding check rather than an assumed pass.

## Where each thing goes

| Kind of thing | Where | Lasts? |
| --- | --- | --- |
| A clone you edit | A subfolder of the lane folder (`src/NAME`), never its top: the sandbox hides a `.git` there. A big tree may sit in scratch; its unpushed branches are bundled into the lane folder before the hand-back. | Until the coordinator has taken the branches |
| A clone to read | The workspace's home clones, read only. Never write there. | Theirs |
| Scratch: build trees, rigs, caches, copies of fixtures, downloads | `<scratch disk>/<lane>`, on a solid-state disk with room, listed in `.artifacts`. | No: removed before the hand-back, except what a review rerun needs, named in Kept |
| The stage: packages and sources the next step takes | `<build disk>/<lane>/stage`, one `SHA256SUMS` at its root or in each package folder, a `.keep` whose first line says why it waits and what reads it. Copied in, never hard-linked. | Until a publication takes it |
| Bundles of unpushed branches | In the lane folder, each checked with `git bundle unbundle` into a throwaway repository. | With the lane |
| Evidence: logs, captures, measurements, proof pairs | `evidence/` in the lane folder, small (images, text, numbers). | With the lane |
| The report | `REPORT.md` at the top of the lane folder, first line `STATUS: review` or `STATUS: blocked`. | With the lane |
| Private notes, drafts, contacts, plans | The private record, never a repository that has a remote and never a report committed into a branch. | Private |
| Skills | Your clone of the skills repository, a branch named after the lane, bundled into the lane folder; pushed by the coordinator. | Public once merged |
| Never | A hard disk, a network share, the home folder, a folder named temp or tmp (`/tmp`, `/var/tmp`, a folder called `temp` or ending in `-temp`) for anything that must last. A system cleaner or a person may empty a temp folder, and has. | |

Scratch may live under `/var/tmp/<lane>`: it is disposable by definition. The stage, the bundles, the evidence and the report are not scratch.

## The disks

- The disks are the local solid-state ones. A hard disk and a network share are out, even when they have the room: they are slow, and a share without a battery hangs every process that touches it when the power drops.
- Each disk has a floor of free space that the workspace sets (the station's figures live in its house rules). Stop only below a floor. A cap written in a brief is a starting figure: when a step needs more than its disk has, move the scratch to another solid-state disk with room, keep caches and what they link to on one file system, and say in the report where it went.
- The stage and the evidence do not move; scratch does.
- Docker keeps every container's writable layer and every image on the root disk, whatever disk your build tree is on. Count it separately.
- A long build is estimated from a finished one, not from the object files: the last half hour of a large package build can take a third of its peak. Start it with the peak above the floor, or stop it at the floor and resume from its saved state; do not let a watch end a two-hour build minutes before its packages exist.

## Ship, clean, hand back

**Shipped** means every one of these is true:
- The stage holds its files, `SHA256SUMS` verifies them (and says how many it verified), and `.keep` says why it waits.
- Every branch with commits on no remote is in a bundle in the lane folder that unbundles whole, or is a clone inside the lane folder. A clone only in scratch is not shipped.
- The evidence the report cites is in `evidence/`, small.
- Nothing is pushed, sent or published by the lane: the coordinator pushes what is accepted.

**Clean** means, after shipping, by literal name:
- Remove the scratch folders you made, the containers you started (`docker rm NAME`), the images you made (`docker rmi NAME:TAG`, no `-f`), the loops and watchers.
- Never `docker ps -q` in a loop, never `docker system prune`, `image prune` or `builder prune`, never an image or container of another lane: the daemon is shared with the services of the machine.
- Files a container made as root: make the container run as your user; otherwise remove them through a container before it exits.
- Keep a rerun image only when the review needs it, and say so in Kept.

**Hand back** last: `REPORT.md` current, first line the status, the Kept section true, the lane check's output in the report.

## `.artifacts` and `.keep`

- `.artifacts`: one line per thing, an image as `name:tag`, a folder as an absolute path, each once. Only what can be rebuilt belongs there; whoever cleans after acceptance removes exactly these. A line that is neither is ignored without a word.
- `.keep`: a file in a folder that must outlive the cleaner, for example the stage. Its first line says why and what reads the folder. A cleaner skips any path that holds a `.keep` anywhere inside.
- An image or scratch folder named after a short prefix (`ab-123-rig`) is found only through `.artifacts`; put the prefix in a `.prefix` file so the check and the cleaner can match it.

## The Kept section

For each item left: the path or the image name, its size measured at hand-back (`du -sx --block-size=1M PATH`; `docker image inspect --format '{{.Size}}' NAME`), why it stays, and the command that rebuilds or reruns it. Say plainly that no container and no loop is left. A size that was estimated, a cap quoted instead of the size, or a path that is gone is an unmeasured claim.

## Traps

Each with symptom, cause, fix and how it was found: [lessons from the lanes, November 2026](references/lessons-2026-11.md). The ones met most often:
- A scratch cap or a floor written into a brief stopped a task while another disk had room.
- Work exists only in a scratch clone with commits on no remote.
- Images and folders exist that `.artifacts` or Kept never listed, or are listed that no longer exist.
- A `.keep` with no first line, or a second folder called `stage` in scratch.
- A shell or wait loop of the task still running after the hand-back.
- A staged file hard-linked, so a publication gate saw it change.

## Credits

The cases come from lanes 551b, 572, 572b, 575, 576, 578, 579, 580 and 587, and from the disk, cleanup and container rules recorded between October and November 2026.
