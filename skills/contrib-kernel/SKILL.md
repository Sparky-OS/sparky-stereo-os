---
name: contrib-kernel
description: >-
  Send a Linux kernel patch or bug report the kernel's way: its code of conduct, a human Signed-off-by, the Assisted-by:
  LLM trailer and the coding-assistants and generated-content rules, the security list's rules for a bug found with AI,
  checkpatch.pl, get_maintainer.pl, git format-patch, Fixes: tags, lore.kernel.org searched first, a tested fix with
  every report, and the human's review before anything is sent. Load it with upstream-outreach and drivers for a DRM,
  HDMI 3D, EDID, amdgpu, nouveau, VC4, virtio-gpu or HID patch, a devcoredump or deadlock report, or a question on
  whether a subsystem accepts AI-assisted work.
---

# Contributing to the Linux kernel

Written on 2026-11-02 from the kernel's own process documents in the 7.3.1 tree the edition builds:
- `Documentation/process/code-of-conduct.rst` and `code-of-conduct-interpretation.rst`;
- `coding-assistants.rst` and `generated-content.rst`;
- `security-bugs.rst` and `submitting-patches.rst`.

It also draws on Linus Torvalds's keynote with Dirk Hohndel at Open Source Summit North America 2026 ([video](https://www.youtube.com/watch?v=fi29pfLcW4I), the week after 7.1-rc4) and his later posts.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first and [`drivers`](../drivers/SKILL.md) for the work itself; this skill is the kernel's own practice.
Check freshness: re-read those documents in the current tree before every series, because they are changing fast.

## The rules that come first

- **The code of conduct** is the Contributor Covenant 1.4, adapted, with the kernel's own interpretation document.
  It applies on the mailing lists and every kernel venue.
  Reports go to the Code of Conduct Committee (volunteers appointed by the Technical Advisory Board, with a professional mediator); its members are listed at kernel.org/code-of-conduct.html.
- **Signed-off-by is human.** `coding-assistants.rst`: "AI agents MUST NOT add Signed-off-by tags. Only humans can legally certify the Developer Certificate of Origin". The human reviews everything, adds their own Signed-off-by and takes full responsibility.
- **Say what the tool did.** `coding-assistants.rst` asks for `Assisted-by: LLM [TOOL1] [TOOL2]` (basic tools such as git, gcc or editors are not listed).
  `generated-content.rst` asks for transparency about tools, prompts and testing.
  It also gives maintainers full discretion: a maintainer may treat the patch like any other, review it more strictly, or reject it.
  The 2026 Maintainers Summit agreed to stop requiring the tag; the edition keeps it anyway (Daniel, 2026-10-16: "we'll change nothing - it's just not compulsory anymore - but we respect devs").
- **Understand and defend every line.** `generated-content.rst`: "You are expected to understand and to be able to defend everything you submit."
  Linus on LKML, 2026-10-13, on tool rules: understanding "has very little to do with what tools they use".
- **Nothing goes out without the human's review.** `coding-assistants.rst` step 9: the assistant leaves the result to the reporter for review and "must never send anything itself": an agent never sends on its own.
  The edition's practice already is that: the assistant prepares the series and the evidence, Daniel reviews and approves, and only then is it sent, from his account, by him or at his word.
- **Subsystems add their own rules.** nouveau's community statement asks for code that is "the output of your own human brain"; the edition carries its nouveau work in its own fork and does not push AI-assisted features there.
  Read the subsystem's documents and MAINTAINERS entry first.

## A bug found with AI help

The kernel's procedure (`coding-assistants.rst`, "Procedure for finding and fixing bugs", and `security-bugs.rst`, "Responsible use of AI to find bugs"):

1. Read the whole process documentation first, not pieces found by keyword search.
2. Reproduce the bug. A report without a reproducer may be ignored, because many unverified reports turn out invalid.
3. **Write the fix and test it**, with the reproducer, no new build warnings and `checkpatch.pl` clean. A report without a fix is the exception.
   Dirk Hohndel's point at the 2026 keynote: the companies that found bugs with AI sent no patch, though the code was open source.
4. Commit with the problem, the solution and a `Fixes:` tag; no Signed-off-by from the tool; `Assisted-by`.
5. Find the recipients with `scripts/get_maintainer.pl`.
6. Say what could not be done: no reproducer, a fix that could not be built or tested.
7. Decide vulnerability or ordinary bug with `threat-model.rst`.
   **A bug found with AI is treated as public** ("bugs discovered this way systematically surface simultaneously across multiple researchers"), so it goes to the public list.
   The reproducer is not published; say one is available, for maintainers to ask for privately.
   Ordinary bugs never go to the security list: they do not move faster there and they use triage capacity others need.
8. **The report is short and plain text:** a summary first (files, versions, impact), no Markdown, verifiable facts only, no speculative impact. The kernel asks reporters to configure their tools "to produce concise, human-style reports".

## Working with people

- Linus at the 2026 keynote: his job is working with people, and he does not use AI for that.
  On the kernel lists, review answers are the sender's own words.
  The evidence they point to (logs, test runs, bisects) may come from the tools.
- Answer every question on the thread. The burnout Linus names is drive-by reports whose senders never answer follow-ups.
- One series per behaviour, `git format-patch` with a cover letter, a new version (v2, v3) for each round with what changed, per `submitting-patches.rst`.
- Reviews by AI tools (Sashiko on the lists) are reviews: answer them like any reviewer, with the fix, the evidence, or why the point does not apply.

## The edition's own practice

- The edition's kernel is a fork that ships everything it can, with the stereo work on top; its patches are clean, additive commits rebased onto upstream, so upstream updates slip in easily.
- What fits upstream goes there by this route; the rest stays in the fork and ships.
- Local AI is part of the toolchain. Linus recommends it so that contributors are not at the mercy of the big companies.
