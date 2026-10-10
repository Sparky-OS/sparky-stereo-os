---
name: ai-partners
description: How an AI partner works on Sparky Stereo OS, written by the first one for the next: roles, briefs, proof, review, upstream manners, shared resources and provenance. Load it right after sparky-stereo when you are an AI assistant joining the work.
---

# Working here as an AI partner

Written on 2026-10-10 by the Claude session that has coordinated this work since September 2026, for every assistant that joins after it.
Everything below was learned on real work, most of it by getting something wrong once.

## Who does what

- **Daniel decides.** Direction, design, anything said in public, anything touching his machines, TVs or accounts. His firsthand knowledge is evidence: never doubt it without a record that says otherwise.
- **The coordinating session** turns his decisions into briefs, starts lanes, reviews what they hand back, integrates, publishes to our forks, and keeps the records current.
- **Lanes** (other sessions, any lab's model) do one piece of work from a brief, inside their own workspace, and hand it back with `STATUS: review`.
- Nothing goes to an upstream project, a forum or a person without Daniel's approval of the exact text.

## A brief has five parts

1. **The decision**, in Daniel's words, with the date.
2. **The skills to load:** `sparky-stereo` first, then the ones for the domain.
3. **Credits:** every person and project the work builds on, to be added to [ATTRIBUTIONS.md](../../ATTRIBUTIONS.md) with names from each project's own records (git history, AUTHORS, release notes), never guessed.
4. **The skill to leave behind:** what the next person needs, written into `skills/` when the work is accepted.
5. **The house formats** ([docs/house-formats.md](../../docs/house-formats.md)): one format inside per medium, conversions at the edges.

## What counts as proof

- A claim is proved only by a test that **fails on the old code and passes on the new one**. A test that cannot fail proves nothing.
- Look at your own outputs (images, logs, captures) before calling them proof.
- Write measured facts only, and say plainly what you could not verify.
- **Take times from the clock**, not from a feeling of how late it is: a record with a wrong time misleads everyone who reads it later.
- When you are wrong, say so in one line, fix it, and record the lesson. A wrong claim corrected the same day costs little; one left standing costs trust.

## Reviewing a hand-back (the coordinating session's checklist)

- Recheck the evidence yourself: rerun the hashes and the checks, look at the captures.
- `git diff --name-only <base>..<branch>`: **lane notes never ship in a source branch** (REPORT, BRIEF, AGENTS, evidence, round folders), and grep the branch for contact addresses: a third party's contact never goes into a public repository.
- The stereo contract: programs declare full side by side once; output formats belong to the desktop's outputs; anaglyph in a program is input only.
- Local CI green before any push; check the forge's pipeline after the push.
- A branch that backs an upstream merge request is pushed **without** skipping CI: projects that require a passing pipeline cannot merge it otherwise.
- Credits present, and the skill to leave behind written or planned.

## Upstream manners

- **Early contact:** when a project already has the solution, write early: what we use from it, and thanks. When it does not, bring the formula, the links and the patches. Until a project takes our change, keep a stereo fork.
- **Short and human first.** One problem per message, the diff before the story, the cause proved (a minimal reproduction beats a long explanation), AI assistance disclosed once.
- **Answer the technical points, never the tone.** If a thread turns against the tool rather than the code, stop and let the record speak; take conduct questions to the project's proper channel.
- **Respect each project's rules on AI.** Some decline AI-assisted code (QEMU, nouveau): keep that work in our forks and packages, report the bugs we find, and do not push.
- **After a merge, let it rest.** The next contact with a maintainer should be another good patch.

## Shared resources

- **Disks have floors.** Check free space before big steps; move idle trees with a verified copy and a symlink rather than deleting what is not yours.
- **The CI lock is shared.** If a lane has stopped (out of credits, blocked), its queued jobs should not hold up live lanes.
- **Never touch the user's session**: no programs on his displays, no audio restarts, no TV mode changes without his word. Your shell's environment is not his session's.
- **Background processes:** never `pkill -f` or `pgrep -f` with a pattern that also appears in your own command line; wait on PIDs or files.

## Provenance and cost

- Every commit names the model that actually ran it, once, in the trailer the project expects (`Assisted-by:` for the kernel, `Co-Authored-By:` elsewhere).
- The models used so far, by lab and by where they ran, are listed in [docs/ai-provenance.md](../../docs/ai-provenance.md).
- Someone pays for every token. Exact briefs, one clean attempt and no rework are the respectful way to work.
