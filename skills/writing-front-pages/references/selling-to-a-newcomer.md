# Selling the work to a newcomer

**For** anyone who writes a front page, a call, a quick start or a first note for the edition: what we offer, how the value is said, and how a reader who has only ever used Windows gets from the first line to a 3D desktop without losing anything.

Written on 2026-11-09 from ORDER 490, the review of the edition's README, its translations, the organisation profile and the first one-page quick start.
The rules of [the skill](../SKILL.md#the-rules) come first; this page adds what they do not say.

## The recipe

1. **Offer, never ask.** Say what the reader gets: one desktop where a program hands over its two eye pictures once and every kind of 3D screen shows them.
   The only thing we ask for is people: a tester, a developer, a pointer to someone who should see it.
   Never ask for hardware, a loan, a discount or money, and never promise work, a demonstration or a date.
2. **The reason behind the offer** is a common base: with one hand-over that every screen understands, N programs and M kinds of screen need N plus M pieces of work instead of N times M.
   Daniel's line, used as a reason and never as a slogan: "the internet is a success because is free", and "the same must go for 3D content".
3. **Value first, with its evidence, then the caveat.**
   Write the measured gain or the measured failure it prevents, with the device it was measured on, and only then the limit.
   Never shrink a measured result to "compliance" or "changes nothing".
   The edition is a reference only in its own subject, stereo 3D and the display path that carries it.
4. **Every stereo display, never the oldest ones.**
   Name the families whenever the scope is described: 3D TVs and projectors, VR headsets, glasses-free 3D displays, any monitor with red-cyan glasses, and a plain 2D monitor, which shows the same desktop without any change.
   A measurement keeps its real device ("measured on a 3D TV at 1920 pixels wide"): the device of a measurement is a fact, the scope of the system is the design.
5. **The engineering reader gets colour and quality.**
   For engineers, scientists and their vendors leave red-cyan glasses out: write full colour and full sharpness per eye, the screens that give it, and that every engineer, worker and client already carries a 3D screen in the pocket, the phone in a viewer.
6. **The reader comes from Windows.**
   Assume a first reader who has never started a computer from a USB stick, and who will try before reading.
   Write for that reader in this order: it is safe, here is what you get, here is the one page of steps.
7. **Safety first, then the benefit.**
   Before any step that touches the firmware or the disk, the page says what to save and what cannot be undone.
   The first rule of showing anything to a person is that it must not cost them anything: not their files, not their Windows.
8. **One page before any long guide.**
   At most ten steps, one sentence each, one real screenshot where one exists, what to check after the step, and one link to the long guide at the end.
   The long guide stays, complete and linked by section, for the reader who asks.
9. **Summary first, details linked.**
   A page or a message opens with the subject, what the reader needs, and priorities one to three.
   Each detail is a link to the exact section, never a paragraph in the way.
10. **One step after another.**
    Never ask the reader to weigh several things at once; too much to analyse before acting is a reason to stop.
11. **A demonstration stays stable.**
    Nothing changes modes or loses a setting in front of the viewer; say which settings a page relies on, and do not send a reader through a step that resets them.
12. **Never "the first" or "the only"** without a source beside it, and never a status better than the evidence: works today, coming, in development.
13. **A true simplification stays.**
    A sentence that is true at the reader's level is not an error; the precise form waits one click down for the reader who asks.

## The quick start for a Windows PC, as built

[Try it on your Windows PC](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/guides/try-on-windows.en.md) is the pattern.
- Step 1 saves the BitLocker recovery key and backs up the files, before the USB stick is even written.
- The page tells the reader to leave Secure Boot on, because the stick starts with it on.
- It says in one line that the live session changes nothing on the disks and keeps nothing after a restart.
- It ends with one link to [the long guide](../../../docs/guides/beta1-install-classic-linux.en.md).
- A screenshot is used only where a real one exists; a missing one is listed for the next capture round, never drawn or generated.

## Traps

- **Symptom:** a tester's Windows asked for a BitLocker recovery key at the next start; the tester did not have it and had to reinstall Windows.
  **Cause:** the tester turned Secure Boot off to start the USB stick, and the only warning sat in the installation section, deep in a long guide they had not read.
  The person may never have turned the encryption on or seen the key ("Device Encryption is a Windows feature that enables BitLocker encryption automatically for the Operating System drive and fixed drives", [Device Encryption in Windows](https://support.microsoft.com/en-us/windows/device-encryption-in-windows-cf7e2b6f-3e70-4882-9532-18633605b7df)); BitLocker checks Secure Boot through the TPM ("By default, BitLocker provides integrity protection for Secure Boot by utilizing the TPM PCR[7] measurement", [BitLocker countermeasures](https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/countermeasures)), and Microsoft lists "Changes to the boot manager" and "Modifying the Platform Configuration Registers (PCRs) used by the TPM validation profile" among the events that start recovery ([BitLocker recovery overview](https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/recovery-overview)).
  **Fix:** step 1 of every page that leads to a USB start is "save the BitLocker recovery key" with Microsoft's own page for finding it ([Find your BitLocker recovery key](https://support.microsoft.com/en-us/windows/find-your-bitlocker-recovery-key-6b71ad27-0b89-ea08-f143-056f5ab347d6)), and the page says not to turn Secure Boot off.
  **How the cause was found:** the order of the steps taken, set against where the guide first mentions the key.
- **Symptom:** readers do not follow the guide, and write back with problems the guide answers.
  **Cause:** the guide is complete, so it is long; people try first and read when something fails.
  **Fix:** the one page above, linked from the README's next step and as a bold "**Short version:**" lead at the top of each long guide.
- **Symptom:** a text describes the edition as "3D TVs and red-cyan glasses", and a reader files it under 2010.
  **Cause:** the writer listed the outputs that were tested first.
  **Fix:** name the five families of recipe step 4, and keep the tested device only beside its measurement.
- **Symptom:** a first screen that passed the cold-reader test loses its picture or its status line after a shortening pass.
  **Cause:** the shortening worked by paragraphs, not by the first-screen order.
  **Fix:** shorten below the first screen first; test the first screen again after every change to it.
- **Symptom:** the text on a small high-density laptop screen is too small to read at the first start.
  **Cause:** the scale of the live session is chosen for a desk monitor.
  **Fix:** in a quick start, name where the scale is changed (System Settings, Display & Monitor, Scale) in the step that follows the first start.

## Shrinking a long front page without losing a fact

The method used on the README (3,720 words down to about 500) and the organisation profile.

1. **List who links in.** Search the repository, the talks, the other READMEs, the organisation profile and the sister repositories for `README.md#` and `sparky-stereo-os#`; write the anchors down. Each one must still resolve at the end.
2. **Cut the page into blocks** at its headings, and give every block a destination: stays on the front page, moves to an existing page under `docs/`, or moves to a new page under `docs/`.
   A block that moves goes whole, with its pictures, links, credits and footnotes; rewrite nothing on the way.
   The form that loses nothing by construction, and the one used here: the whole former page becomes one detail page (`docs/edition-in-detail.md`, with its links rewritten for the new folder), and the front page keeps, for every section, one sentence of the section's own and a link to the same anchor on the detail page.
3. **Keep the claims table** as you go (`claims.tsv`: the front page's sentence, the old line it came from, where the full text now lives). A sentence on the new front page without an old line is a new claim: remove it or source it.
4. **Leave the anchors.** Where a linked heading left the front page, keep a short section of the same name that says one line and links to the new page, or leave `<a id="old-anchor"></a>` at the line that now points there.
5. **Prove nothing was lost.** Compare the sets of link targets and of pictures before and after across the front page plus the pages that received its blocks; then compare the words: every sentence of the old page must be found, whole, in the new page or in one of the receiving pages. A script does both; keep its output as evidence.
6. **Run the link and anchor check** over the whole repository, not only the changed files: a moved heading breaks links in files you did not touch.
7. **Translations follow the English** in structure and anchors. Give every translated heading that other pages link an explicit `<a id="english-slug"></a>`, because a translated heading makes a different slug.
   Build each translated front page from that translation's own sentences (the first sentence, the credit, the door lines, the first line under each heading), found by position because every translation keeps the headings in the English order; then only the few new lines need translating. A generator script with one strings file per language keeps the nine pages identical in structure.
8. **The cold-reader test,** before and after, on the first screen only.

## Traps met while shrinking

- **Symptom:** the first screen stays near 190 words when the rule says about 120.
  **Cause:** three things may not leave it: the credit sentence, the Lean Code lines with their measurement, and the line that names every kind of screen.
  **Fix:** cut everywhere else first (the status to one sentence, the next step to one link), say the measured count in the hand-back, and let the cold readers judge the result.
- **Symptom:** a scope line reads as a claim that everything works ("it drives VR headsets and glasses-free displays").
  **Cause:** the design's scope and the tested devices were written as one sentence.
  **Fix:** two lines: "It is made for ..." names the families, and the status line says what was tested and what is in progress.
- **Symptom:** a cold reader calls a door "a rhetorical question that does not clearly tell me what to do".
  **Cause:** the door reused a section's opening question.
  **Fix:** a door states what the reader gets; the question stays in its section.
- **Symptom:** a cold reader of a quick start lists Secure Boot, the hash check and the writing tool as the confusing words.
  **Cause:** the step named the thing and not what it is.
  **Fix:** one clause in the same breath: "Secure Boot is the PC's own check that only signed systems may start".
- **Symptom:** the second reader cannot be reached (`ask_chatgpt`: "ACIG bootstrap pending").
  **Fix:** `ask_cloud` with a `model` from another lab than the default; give the text as a file, and record which model answered. Never count one lab twice as two readers.
- **Symptom:** a request to check nine languages of strings in one call returns an empty answer, three models in a row.
  **Fix:** not found; say in the hand-back which languages no second model read.
- **Symptom:** a link from a skill to a page that exists only on the texts branch fails the skills check.
  **Fix:** link the page by its full address on the main branch until both branches are merged.

**Perks.** The claims table is also the reviewer's reading list, and the receiving pages become the "doors" of the front page for free.
