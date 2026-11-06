---
name: upstream-outreach
description: >-
  Evidence-based contact with another project before and after a merge request: the heads-up to the maintainer, AI
  assistance said once up front, one small ask, the project's rules and code of conduct first, which route (Debian, the
  edition's organization, any other upstream), the right person from the project's own records, prove an absence by
  running the program, the report carries the fix and the test, one finding at a time, a vulnerability through the
  private route, facts without a severity, Discourse first-post holds, one knock, the one list of merges. Load it when a
  maintainer answered with questions, a thread turned to the tool instead of the code, a pull request was closed with
  the change landed as the maintainer's own commit, a company has not answered, a report or a heads-up must be drafted,
  names from a transcript must be verified, or a sent copy must be checked.
---

# Upstream outreach: never cold

## Working recipe

1. For a fix, first search upstream for the same fix ([search-upstream-first](../search-upstream-first/SKILL.md)): when upstream has it, there is nothing to offer, only a commit to carry with credit.
2. Read previous incoming and sent interactions, current project contribution rules and the exact implementation evidence.
3. Draft for the responsible maintainer: one concrete problem, a small useful offer, honest assistance disclosure and implementation limits.
4. Return the draft and claim sources. Send only within explicit authorization; verify the sent copy and record follow-up obligations without inventing acceptance.

**Check freshness first.**
Written on 2026-10-14, after the edition's first proposal to a project that had declined AI-assisted text.
Absence claims, the one list of merges and Discourse's first-post holds added on 2026-11-02.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first; [`ai-partners`](../ai-partners/SKILL.md) has the upstream manners this builds on.

## The rule: a heads-up before the merge request

Daniel, 2026-10-14: the "not cold PR" policy for AI partnership works with or without a supporter.

- **Never send a merge request cold** to a project that may be wary of AI-assisted work. First, a short note to the maintainer who owns that part of the code: what is coming, why it matters, and the evidence.
- **Say it up front, once:** the work was made with AI partners and the person sending it checked it and signs it. Hiding it and being found out ends the conversation; saying it first lets the maintainer decide on the code.
- **Ask one small thing:** "would you be willing to look at it?" The merge request follows only after that.
- **The evidence goes first:** measured runs, control runs that fail without the change, results on real hardware, each linked.
- **A supporter makes it stronger, and is not required.** When another project gains from the change, its people can say so on the merge request with their own results.

Why: in October 2026 a merge request reached KWin without warning and was declined for its AI-written text, so the edition withdrew. The next proposal, the DisplayXR window-geometry publisher, goes through the area's maintainer first, with DisplayXR's panel results and support (DisplayXR runtime issue #1928).

## Each project's rules and code of conduct come first

Every contribution follows the receiving project's own rules and its code of conduct, in every channel it uses: code review, trackers, forums, chat and mail (Daniel, 2026-11-02).
- Read both before the first message: the repository's `CONTRIBUTING.md` or contribution page, and the code of conduct it names (KDE's, Qt's QUIP 12, Debian's, VideoLAN's).
- Each `contrib-<project>` skill opens with "The rules that come first": the code of conduct, the route the project accepts, and its stance on AI, each with its source and the date it was read.
- A project with no written code of conduct still gets the same manners: respectful, concise, in its own venue.

## Which route

- **A package that comes from Debian:** report it to Debian with the fix inline ([`contrib-debian`](../contrib-debian/SKILL.md)); when the program's own upstream has the bug too, report it there as well, in that project's way.
- **A program its creator keeps in the edition's organization:** the organization's repository is that program's upstream, so a change is a pull request there, from a branch, reviewed and merged by its creator under the creator's rules.
  Jeromy Streets moved org.kde.video, his video wallpaper, into Sparky-OS, so that repository is its only home; effcol keeps admin rights on Sparky-OS/wiz3D beside his own effcol/wiz3D.
- **Any other upstream:** the edition carries its changes in its own forks, because a stereo kernel and stereo drivers make it different from every other Linux distribution; the parts that make sense upstream go there by the project's own route, its `contrib-<project>` skill, or this skill alone when none exists yet.

## Per-project skills

Each project has its own practice: where to send, the shape of a series, its tests and its review habits.
Load the project's `contrib-<project>` skill with this one when it exists: [`contrib-ffmpeg`](../contrib-ffmpeg/SKILL.md), [`contrib-kde`](../contrib-kde/SKILL.md), [`contrib-qt`](../contrib-qt/SKILL.md), [`contrib-debian`](../contrib-debian/SKILL.md), [`contrib-kernel`](../contrib-kernel/SKILL.md) and the others listed in the [skills index](../README.md).
A `contrib-<project>` skill declares the packages that make it relevant (`metadata: requires-packages`), and `sparky-stereo-skills link` links it only where one of them is installed.

## Before writing

- **Find the right person in the project's own records:** who wrote and keeps the code (its git history, metadata, maintainers file), not a guess. For a theme, its metadata names the author.
- **Get every fact about people exact:** names, roles and companies from their own pages. A wrong title in a first note costs more than a missing one.
- **Check the project's stance on AI** before choosing between a proposal, an issue only, or keeping the work in our fork.
- **Some projects refuse AI work outright, reports included.** XScreenSaver 6.17 ships an `AGENTS.md` saying it "does not want AI contributions of any kind", and its author's site turns robots away; send nothing there. A bug in the version a distribution carries goes to that distribution's tracker, which for Debian's XScreenSaver is also what its packaging asks.
- **Read the project's reporting rules before the report.**
  The practical guide ([Securing Open Source in the Age of AI](https://openssf.org/resources/securing-open-source-in-the-age-of-ai-a-practical-guide/), OpenSSF with CNCF, May 2026), "Respect the Reporting Guidelines of the Project", asks to "learn about the community to identify the right people and formats for reporting", and adds that random "drive-bys" are not welcome, above all at the scale AI tools make possible.
  So read its `SECURITY.md`, its AI policy and its threat model first.
  A scenario the threat model marks as out of scope or not of concern is not reported ("Documented Threat Model & Real Use Case Patterns and Antipatterns").
- **Search for an earlier finding first.**
  "Be Aware, the Code is Open, Someone May Have Already Found What You Did": other people and other tools read the same code at the same time.
  The search is [`search-upstream-first`](../search-upstream-first/SKILL.md): the default branch, the merge requests and the issues, and the project's private route when it has one, since a fix may be waiting there.
- **Prove an absence by running the program, never by code search alone.** A claim that a program does not do something, made in public, is the most expensive kind to get wrong.
  On 2026-09-18 the edition's first report to Kodi ([xbmc/xbmc#29337](https://github.com/xbmc/xbmc/issues/29337)) said Kodi never reads the H.264 frame packing SEI, because GitHub's code search found no `AV_FRAME_DATA_STEREO3D`, `AV_PKT_DATA_STEREO3D` or `frame_packing` in its tree.
  Kodi does read it: `DVDVideoCodecFFmpeg.cpp` takes `stereo_mode` from the decoded frame's metadata, which FFmpeg's H.264 decoder fills from the SEI, and a container test of Kodi 21.2 logged `autodetected stereo mode for movie mode left_right` minutes after the report went out.
  The report was corrected and replaced the same day.
  So: read the source files on the code path (code search does not index every file, and a feature can arrive by a path you did not think to search), run the program on a reproducer in a throwaway container, and name the test files neutrally (a file named `sbs_*.mp4` set off Kodi's file-name detector and confused the first run).
  Measure, then write.
  A display's capabilities likewise: quote `edid-decode` of the saved EDID bytes, never a note's summary of them.

## The message

- Short and human: one problem, the evidence linked, thanks where they are due.
- One sentence per line; the writer's own voice.
- One ask, small and concrete.
- In the person's own venue: an issue or comment on their repository for code, email to a maintainer or to a group's staff contact, the store page or forum for a theme's author, LinkedIn for a person without a code venue. Answer where the message came from.
- Never another person's contact details in a public file.
- **The report carries the fix and the test.**
  The practical guide, "Wherever Possible, Provide a Proposed Patch to Address Your Discovery": "Fixes are more important than findings. Full stop."
  It also asks for "Test Cases to Avoid Future Regressions".
  The edition had the same rule from Daniel, 2026-11-02: "tell them the fix or don't send".
  A fix that was not built and proved is not sent, and the proof is the reproducer that fails before and passes after.
- **A vulnerability goes through the project's private route,** with the reproducer, the fix and the versions.
  The practical guide, "Privately Provide the Project a Proof of Concept (POC) and/or Proof of Vulnerability (POV)", warns that a proof of concept is as useful to an attacker as to a defender, so it stays out of public issues until a fix is out.
  The project's own rule wins: the kernel, for instance, treats a bug found with AI as public ([`contrib-kernel`](../contrib-kernel/SKILL.md)), and x265 asks for a private report of a memory-safety issue ([`contrib-x265`](../contrib-x265/SKILL.md)).
- **Facts, not a severity.**
  The practical guide, "The Robots Can't Rate YOUR Risk for You (and Will Over-Inflate Severity)": "Risk should ALWAYS be viewed from the eyes of the RISK HOLDER."
  Write what fails, where, in which version and how it was reproduced.
  Leave out a score, "critical" and a guess at impact unless the project's form asks for one; the maintainer knows how the code is deployed, and we do not.
- **One finding at a time, and as short as it can be.**
  The practical guide says each vulnerability report "can take a developer between 1-8 hours to review and evaluate", and describes tools that "dump tens, dozens, hundreds of reports onto a project at once".
  Send one report, wait for its answer, and send the next only when the first is settled; this is the one-knock rule applied to findings.
  "AI reports tend to be overly verbose": cut the report down to the failure, the proof and the fix.
- **Say how AI was used where the project asks.**
  The practical guide, "Be Clear and Up-Front if and How AI Tools Were Used in the Report", agrees with the rule above that it is said once and up front.
  Where a project's form asks which tool or model, give the one the session's own record shows (the kernel's `Assisted-by:`), never a guess; where it does not ask, the one line stays unitemised.
- **A first post from a new account on a Discourse forum** (KDE Discuss and others) is held for a moderator when it looks like a bot to Discourse's rules for new users: pasted in seconds, more than about two links, several @mentions.
  Daniel's first KDE Discuss post, on 2026-10-06, was held and then marked "silenced: New user typed too fast" until a staff member released it.
  Write or edit a first post in the forum's editor for a while instead of pasting it at once, keep it to two links (the rest go in a reply once it is released) and the mentions to the people who must see it, and never post it again while it is held.
  The limits lift as the account's trust level rises with ordinary reading and posting.

## After sending

- **One knock at most.** If nothing comes back, wait; a later note carries new value (a result, a fix, a release), never a bare reminder.
- **When a thread turns to the tool instead of the code,** stop arguing; ask the lead maintainer once, or keep the work in the fork.
- **Keep every promise** made in a note, and answer every reply.
- **After a merge, let it rest:** the next contact is another good patch.
- **Record a merge once,** in [Merged outside Sparky Stereo](../../docs/upstream-merges.md): the link, the date, "merged by NAME (handle)" from the project's own records, and what it does.
  That page is the one list.
  Every other page (the README, ATTRIBUTIONS, other repositories' provenance notes) links to it with "such as" or "among others" and never copies the names, because copies drift apart.

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

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (10 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
