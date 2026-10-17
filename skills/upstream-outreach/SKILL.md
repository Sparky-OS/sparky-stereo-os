---
name: upstream-outreach
description: >-
  How to bring AI-assisted work to projects and people without arriving cold: a short heads-up to the lead maintainer before any merge request, the evidence first, the AI help stated once and up front, one small ask, one knock at most, and the right venue for each person. Load before any upstream proposal, first contact or follow-up.
---

# Upstream outreach: never cold

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
