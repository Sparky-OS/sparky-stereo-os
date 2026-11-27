---
name: contrib-kernel
description: >-
  Send a Linux kernel patch or bug report the kernel's way: its code of conduct, a human Signed-off-by, AI disclosure
  (the Assisted-by: trailer until 7.3, the cover letter since 7.4) and the coding-assistants and generated-content
  rules, where a change goes in the cycle (merge window or -rc, fixes or next branch, tests kept for the merge window),
  the security list's rules for a bug found with AI, checkpatch.pl, get_maintainer.pl, git format-patch --base, Fixes:
  tags, lore.kernel.org searched first, the agents/skills series, a tested fix with every report, and the human's
  review before anything is sent. Load it with upstream-outreach and drivers for a DRM, HDMI 3D, EDID, amdgpu, nouveau,
  VC4, virtio-gpu or HID patch, a devcoredump or deadlock report, a late -rc pull, or a question on whether a subsystem
  accepts AI-assisted work.
---

# Contributing to the Linux kernel

Written on 2026-11-02 from the kernel's own process documents in the 7.3.1 tree the edition builds:
- `Documentation/process/code-of-conduct.rst` and `code-of-conduct-interpretation.rst`;
- `coding-assistants.rst` and `generated-content.rst`;
- `security-bugs.rst` and `submitting-patches.rst`.

It also draws on Linus Torvalds's keynote with Dirk Hohndel at Open Source Summit North America 2026 ([video](https://www.youtube.com/watch?v=fi29pfLcW4I), the week after 7.1-rc4) and his later posts.
Updated on 2026-11-25 from the 7.4-rc2 tree: where a change goes in the cycle, the removal of `Assisted-by`, and the kernel's own `agents/skills/` series.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first and [`drivers`](../drivers/SKILL.md) for the work itself; this skill is the kernel's own practice.
Check freshness: re-read those documents in the current tree before every series, because they are changing fast.

## The rules that come first

- **The code of conduct** is the Contributor Covenant 1.4, adapted, with the kernel's own interpretation document.
  It applies on the mailing lists and every kernel venue.
  Reports go to the Code of Conduct Committee (volunteers appointed by the Technical Advisory Board, with a professional mediator); its members are listed at kernel.org/code-of-conduct.html.
- **Signed-off-by is human.** `coding-assistants.rst`: "AI agents MUST NOT add Signed-off-by tags. Only humans can legally certify the Developer Certificate of Origin". The human reviews everything, adds their own Signed-off-by and takes full responsibility.
- **Say what the tool did.** The published Linux 7.3.1 `coding-assistants.rst` asks for `Assisted-by: LLM [TOOL1] [TOOL2]` (basic tools such as git, gcc or editors are not listed).
  Freshness check, 2026-11-14: media next at `3fc9303dba01676c2090768126e5327e341b7761` has removed the attribution section and the requirement in `submitting-patches.rst`; do not describe the tag as compulsory in that tree.
  Since 7.4 the tag is gone from mainline: Sasha Levin's "docs: remove Assisted-by references" (v2, applied by Jonathan Corbet on 2026-10-14) removed it from `coding-assistants.rst`, `submitting-patches.rst` and `checkpatch.pl`.
  Its message gives the Maintainers Summit's view: maintainers still want to know how a patch was created, and that "belongs in the cover letter, where it can describe how the tools were used, rather than in the changelog".
  Measured on 2026-11-25 with the 7.4-rc2 `checkpatch.pl`: a commit carrying `Assisted-by: <model> (<vendor>)` gets "WARNING: Non-standard signature: Assisted-by:" and "ERROR: Unrecognized email address"; the same commit without it passes.
  `generated-content.rst` asks for transparency about tools, prompts and testing, in its "Guidelines": which tools, their input or a summary of the prompts, which portions they affected, and how the result was tested.
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
4. Commit with the problem, the solution and a `Fixes:` tag; no Signed-off-by from the tool; the tool's part said as the rule above describes for the tree you send to.
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

## Where a change goes in the cycle

Linus Torvalds on linux-kernel, 2026-11-24 ([lore](https://lore.kernel.org/r/CAHk-=whyUfwzMDMTpih8Xs1MxmhwTCDAc_YwUSZG79vXFMLU=Q@mail.gmail.com)): "This whole notion of "anything that is a fix goes in -rc" is bogus", and "do any new development and test-cases ON A SEPARATE DAMN BRANCH, so that it can be merged during the MERGE WINDOW."
His 7.4-rc1 announcement (2026-11-01, [lore](https://lore.kernel.org/r/CAHk-=whOCnAwXz-FMRdQEDJQ+9b2YXh9M=GHgRay0o4cxSmPVg@mail.gmail.com)) says the same of AI-found fixes: "I'm *much* happier with the flood of AI triggered work going into the merge window than it showing up mainly as extra fixes during the -rc period."

Before a series or a pull request goes out:
1. Read where the cycle stands from the newest tag in Linus's tree, as `maintainer-netdev.rst` "Development cycle" says: after a release tag the merge window is most likely open, after an -rc tag the release is being stabilized.
2. Read the maintainer profile of the changed files (the `P:` entry in MAINTAINERS): its trees, its fixes and next branches, its key cycle dates.
3. Sort each change. A regression of this cycle, or an urgent or critical bug: the current release. A bug that has always existed: the current release only if it is important (`howto.rst`, "Mainline tree"). New development, new tests, cleanups and refactoring: the next merge window, on a branch of their own, out of any pull request for the current release.
4. Split a series that mixes them (`submitting-patches.rst`, "Separate your changes"), and name the target where the profile asks for it (`[PATCH net]` or `[PATCH net-next]` in netdev).

Every rule with its document and section is in [where a change goes](references/where-a-change-goes.md).

- **Symptom:** a pull request sent during the -rc weeks, with new tests and many fixes for long-standing bugs, is taken only under protest, with the warning that the next one will be ignored.
  **Cause:** every fix was treated as -rc material, and tests that are not built by default were counted as harmless; a separate branch placed at the end of the same -rc pull is still in the -rc (Linus's second reply, [lore](https://lore.kernel.org/r/CAHk-=whFaGFFcyyWXvm9NEUchjhRHSa7LbB7ki3SzWKcRx3xJQ@mail.gmail.com): "Well, I do kind of object").
  **Fix:** the four steps above; keep the tests and the fixes for old bugs for a pull in the next merge window.
  **How found:** reading the 7.4-rc5 pull thread whole on lore (2026-11-25); the rule was then matched to `howto.rst`, `maintainer-kvm-x86.rst` "Base Tree/Branch" and `handling-regressions.rst`.
- **The gap:** `2.Process.rst`, "The big picture", says that after -rc1 "only patches which fix problems should be submitted", which reads as the notion Linus rejected; no document says where new tests go or how large a change sent during the -rc weeks may be.

## The kernel's own agent skills

A series in review adds `agents/skills/` to the tree: Sasha Levin's v1 to v4 (October 2026) and Theodore Ts'o's v5 of 2026-11-11 on 7.4-rc2 ([lore](https://lore.kernel.org/r/20261111225940.1573565-1-tytso@mit.edu)), with the skills find-fixes, stable-tag, find-siblings, commit-message and writing-kunit-tests.
- **Its rules for a skill** (v5's "Agent resources" in `coding-assistants.rst`): one folder per skill with a `SKILL.md` in the Agent Skills format; it "points at the process documents that apply to its task and adds only what assistants tend to get wrong"; unless its task is to write code or tests skills "only inspect and report: they do not change files, create commits or tags, or send mail".
- **Its form:** front matter with a `# SPDX-License-Identifier: GPL-2.0-only` comment, `name` and a folded `description`; the body opens with "Read" and the documents, then "Follow the rules for skills in Documentation/process/coding-assistants.rst", then the checks agents get wrong, and ends with what to return and "return no ... and say what is missing". Each skill gets a line in `coding-assistants.rst` and a pointer from its bug-fix procedure; the MAINTAINERS entry AGENT RESOURCES (`F: agents/`, the workflows list) covers the folder.
- **What its reviewers asked:** Kees Cook, on v2: a skill "should be strictly as short as it can possibly be and then aim at the _existing_ documentation", and what agents get wrong after reading a document goes into that document. Krzysztof Kozlowski, on v5 and on a btrfs agent file: write documentation for humans that agents can use, "Not the other way around"; where the folder lives is still argued (`Documentation/`, `tools/`, `.agents/skills`).
- **State on 2026-11-25:** no v6; Sasha Levin planned on 2026-11-12 to respin it "and send it as a PR for the next merge window".

The traps of preparing a patch on top of such a series (a shallow clone, checkpatch's Python helpers, get_maintainer's history counts, lore searched with a plain client) are in [lessons from the lanes](references/lessons-2026-11.md).

## An RFC series for DRM core

To turn patches a distribution carries into an RFC for the DRM core (reconcile, search upstream, rebase onto drm-misc-next by content, KUnit parsed, every commit built alone with W=1, checkpatch, get_maintainer, an IGT companion on VKMS that goes red without the series, DRM's rule for new uAPI, the cover letter and the send checklist), follow [an RFC series for DRM core](references/rfc-series-for-drm-core.md).

## The edition's own practice

- The edition's kernel is a fork that ships everything it can, with the stereo work on top; its patches are clean, additive commits rebased onto upstream, so upstream updates slip in easily.
- What fits upstream goes there by this route; the rest stays in the fork and ships.
- Local AI is part of the toolchain. Linus recommends it so that contributors are not at the mercy of the big companies.
