---
name: upstream-outreach
description: >-
  Prepare evidence-based upstream contact, follow current project policy and track reviewed messages and commitments without duplicate outreach.
---

# Upstream outreach: never cold

## Working recipe

1. Read previous incoming and sent interactions, current project contribution rules and the exact implementation evidence.
2. Draft for the responsible maintainer: one concrete problem, a small useful offer, honest assistance disclosure and implementation limits.
3. Return the draft and claim sources. Send only within explicit authorization; verify the sent copy and record follow-up obligations without inventing acceptance.

**Check freshness first.**
Written on 2026-10-14, after the edition's first proposal to a project that had declined AI-assisted text.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; [`ai-partners`](../ai-partners/SKILL.md) has the upstream manners this builds on.

## The rule: a heads-up before the merge request

Daniel, 2026-10-14: the "not cold PR" policy for AI partnership works with or without a supporter.

- **Never send a merge request cold** to a project that may be wary of AI-assisted work. First, a short note to the maintainer who owns that part of the code: what is coming, why it matters, and the evidence.
- **Say it up front, once:** the work was made with AI partners and the person sending it checked it and signs it. Hiding it and being found out ends the conversation; saying it first lets the maintainer decide on the code.
- **Ask one small thing:** "would you be willing to look at it?" The merge request follows only after that.
- **The evidence goes first:** measured runs, control runs that fail without the change, results on real hardware, each linked.
- **A supporter makes it stronger, and is not required.** When another project gains from the change, its people can say so on the merge request with their own results.

Why: in October 2026 a merge request reached KWin without warning and was declined for its AI-written text, so the edition withdrew. The next proposal, the DisplayXR window-geometry publisher, goes through the area's maintainer first, with DisplayXR's panel results and support (DisplayXR runtime issue #1928).

## Per-project skills

Each project has its own practice: where to send, the shape of a series, its tests and its review habits.
Load the project's `contrib-<project>` skill with this one when it exists: [`contrib-ffmpeg`](../contrib-ffmpeg/SKILL.md).
A `contrib-<project>` skill declares the packages that make it relevant (`metadata: requires-packages`), and `sparky-stereo-skills link` links it only where one of them is installed.

## Before writing

- **Find the right person in the project's own records:** who wrote and keeps the code (its git history, metadata, maintainers file), not a guess. For a theme, its metadata names the author.
- **Get every fact about people exact:** names, roles and companies from their own pages. A wrong title in a first note costs more than a missing one.
- **Check the project's stance on AI** before choosing between a proposal, an issue only, or keeping the work in our fork.
- **Some projects refuse AI work outright, reports included.** XScreenSaver 6.17 ships an `AGENTS.md` saying it "does not want AI contributions of any kind", and its author's site turns robots away; send nothing there. A bug in the version a distribution carries goes to that distribution's tracker, which for Debian's XScreenSaver is also what its packaging asks.

## The message

- Short and human: one problem, the evidence linked, thanks where they are due.
- One sentence per line; the writer's own voice.
- One ask, small and concrete.
- In the person's own venue: an issue or comment on their repository for code, email to a maintainer or to a group's staff contact, the store page or forum for a theme's author, LinkedIn for a person without a code venue. Answer where the message came from.
- Never another person's contact details in a public file.

## After sending

- **One knock at most.** If nothing comes back, wait; a later note carries new value (a result, a fix, a release), never a bare reminder.
- **When a thread turns to the tool instead of the code,** stop arguing; ask the lead maintainer once, or keep the work in the fork.
- **Keep every promise** made in a note, and answer every reply.
- **After a merge, let it rest:** the next contact is another good patch.

## Turn a talk or reply into a reusable contribution (2026-10-19)

Read the complete talk or saved transcript and keep a private notepad with timestamps and source links.
Automatic captions can misname people, APIs and versions; verify those in the project's own records.
Separate what the speaker demonstrated, what current documentation supports, what we measured, and what we propose.
A connection can be useful before an answer arrives; it is not acceptance, endorsement or a delivery commitment.

Respect maintainer capacity: offer a small reproducer, regression case or integration test that runs without an AI client.
An organisation/repository invitation should explain who maintains the edition build, handles bug reports and supports testing, with no unrequested duties for the upstream author.
Keep upstream ownership and the edition's packaging/output responsibilities explicit.
Turn repeated review preferences into documented style/check commands usable by humans and AI; the author still owns correctness.
A question or invitation is not permission to open an unreviewed patch on every related project.

When connecting to W3C, label individual input, Community Group work, an incubation proposal and an adopted standard accurately.
Use cases and implementation evidence come first, then a specific specification gap or question; link the existing issue rather than inventing a mandate.
A browser's missing WebXR session support does not prove it cannot display stereo images through another route.
For editorial workflows use the relevant public [ReSpec MCP guidance](https://github.com/danielcamposramos/respec-mcp); its checks assist human review, not institutional certification.
Keep stereo validation and the limits of HDR validation explicit.

After an authorized send, preserve the exact reviewed text, recipients and message identifier privately.
Verify the sent copy before reporting success. If delivery is uncertain, search by that identifier before retrying to avoid duplicate mail.
Record any promised next action and wait for a response; do not schedule reminders merely because no answer has arrived.
