---
name: writing-front-pages
description: >-
  Write the first text a stranger meets: README openings, profiles, calls for testers, list and page openings, About
  lines within 350 characters, a document's bold lead, README translations, a one-page quick start for a reader coming
  from Windows, a glossary entry, a new term checked against other projects' names before it is used: person first,
  show before telling, short, no jargon up front, honest status, one next step, doors per reader, offer and never ask,
  value with evidence, every stereo display, move never drop, keep every link and anchor that points in, the
  cold-reader test. Load it when a newcomer cannot tell what the project is for, a long README must shrink without
  losing a fact, a tester lost Windows to a BitLocker recovery prompt, a term needs its number or a name may already
  be another project's, a status line confuses, a translated heading's anchor no longer resolves, a check says a
  link was split, or the front pages must name a planned program or capability the edition does not ship yet.
---

# Writing front pages

**Check freshness first.**
Written on 2026-10-12, from the review of the edition's public texts: the README, the organisation profile, the beta-tester calls, the documents and the three open lists.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.
If the [README](../../README.md) shows a newer practice, it wins.

**The problem it solves.**
The work was right and the texts were accurate, but a newcomer could not tell what the project is for.
The content stays; its order and its words change.

**Where it applies:** every text a stranger meets first.
**Where it does not:** upstream pull requests and issues.
Maintainers want the technical detail there, and [`sparky-stereo`](../sparky-stereo/SKILL.md) Part three applies.

## The rules

1. **Person first.** Sentence one says what someone can do with it, in everyday words. No codename, version or component name goes in it.
2. **Show before telling.** Put a picture on the first screen.
3. **Short.** The first screen is about 120 words, and a whole front page at most about 500. Lists hold three to five items.
4. **No jargon up front.** Explain a term in the same breath, or move it one click down. Specifications, clauses, measurements and credits live on the linked pages, where every rule still cites its specification.
5. **Honest status.** Say what works today, what is coming and what is in development. Show only what is done.
6. **One next step:** try it, tell us your gear, or follow.
7. **Doors per reader.** Give one line each for creating, science and engineering, watching and playing, and developing, each leading to its own section or page. The order is Daniel's: engineers, scientists and creators first.
8. **Test with a cold reader** before publishing (below).
9. **Daniel's voice:** one sentence per line, no mid-sentence em dashes, no hard wraps, and bold labels. Write pt-BR for Brazilian venues.
10. **Move, never drop.** Credits, licence, DOI, the version line and upstream merges go lower or to their own page. The credit wording never changes: "Sparky Stereo OS, Daniel Ramos's edition of SparkyLinux (by Paweł "pavroo" Pijanowski)".

## The first screen, in order

1. **What a person can do.** For example: "Create and explore in 3D on the screen you already have".
2. **What they need,** and what it costs: the screen they already have. Name the kinds of screen it drives (3D TVs and projectors, VR headsets, glasses-free 3D displays, any monitor with red-cyan glasses, a plain 2D monitor without any change), never only the oldest ones.
3. **Who makes it:** the credit line.
4. **The picture,** linked to the section that explains it. Never link it to a file type the reader does not know.
5. **The status,** for example "In development: nothing to download yet". Without this line, cold readers go looking for an ISO.
6. **The doors.**
7. **The next step,** with icon-only links labelled ("Sign up in your language").

## Words that fail with newcomers

- **Metaphors.** "Hand the desktop two eyes once" read as a riddle. Say what happens instead.
- **A term without its number.** "Deep colour" was ambiguous until it read "deep colour (16 bits per colour instead of 8)".
- **Resource lists on the first screen.** Readers take them for the product: three linked lists made a reader say the project's focus was "stereoscopic 3D, HDR, and VR".
- **Alt text.** Only screen readers and models read it, so it cannot carry meaning a sighted reader needs.
- **Ambiguous status.** "The package repository goes online together with the tested ISO" confused a cold reader in both versions of the call it sat in. Say it plainly: "the ISO and the package repository come out together".

## Each kind of front door

- **Documents:** start with one bold lead, "**For** <who>: <what they get>", and leave the rest of the page as it is.
- **Lists:** add a "**Use it to** ..." line and three or four "**Start with**" links to the list's own sections. Keep the awesome-list title, badges and description as the format expects.
- **Calls for testers:** say what the system does for a person, then the status, then how to sign up, all before the gear list.
- **About lines:** person first, and within GitHub's 350 characters.
  - A fork says where it comes from: "The stereo version of <Project> by Sparky Stereo OS, forked from <upstream>", or "Sparky Stereo OS's <kind> work on <Project>" where the name's rules ask for it.
  - Something planned starts with "Planned:".

## Selling the work to a newcomer

[Selling the work to a newcomer](references/selling-to-a-newcomer.md) holds the recipe, the traps and the method for shrinking a long front page.
The short form:

1. **Offer, never ask.** We offer one common base for 3D programs and 3D screens; what we ask for is people, never hardware, loans or money.
2. **Value first, with its evidence,** then the caveat. Never undersell a measured result, and claim reference standing only for stereo 3D.
3. **Every stereo display:** 3D TVs and projectors, VR headsets, glasses-free 3D displays, any monitor with red-cyan glasses, and a plain 2D monitor without any change. A measurement keeps its real device.
4. **Engineering readers** get full colour and full sharpness per eye, and the 3D screen already in their pocket; no red-cyan glasses in that pitch.
5. **The reader comes from Windows** and tries before reading: safety first, then the benefit, then one page of at most ten steps, with the long guide one link away.
6. **Summary first, details linked** to the exact section; one step after another.
7. **Never "the first" or "the only"** without a source, and never a status better than the evidence.

The trap that cost a tester their Windows installation: the guide did not say, before anything else, to save the BitLocker recovery key and to leave Secure Boot on.
Step 1 of every page that leads to a USB start says both.

## Adding a planned capability

When the front pages must name something the edition does not do yet, sentence one stays as it is and the word goes into the doors it serves, status first: "Scanning is planned: a video of an object or a place becomes a 3D model you can walk around."
The detail page gets one paragraph under its own anchor, the credits page one row marked "Planned, not shipped yet", and the nine languages change together.
The recipe, the checks and the traps: [Adding a planned capability to every front page](references/adding-a-planned-capability.md).

## Adding a front-page language

When a language joins after the others, translate from today's English page, settle the glossary before the first sentence, and put the language in the row where its group ends.
Every anchor the English headings make must still resolve, the call for testers follows the English call as it stands, and a cold reader reads the first screen in that language.
The recipe, the two scripts and the traps: [Adding a front-page language after the fact](references/adding-a-front-page-language.md).

## Keep every link that points in

For a website made from the existing front pages, use [The front pages as a site](references/front-pages-as-a-site.md): keyed strings from each language's own source, shared templates, a native language menu, preserved fragments, offline checks and a local preview before any publishing switch.

Before moving a heading, find who links to it: talk slides, forum posts, other lists, the issues.
- Keep each linked heading, or leave `<a id="old-anchor"></a>` where its content now starts.
- Check every relative link and anchor in the changed files before handing back.
- Keep a claims table (draft line, source file and line, and where each moved fact now lives), so a reviewer can check that nothing new was claimed and nothing was lost.
- To shrink a long page, follow [the eight steps](references/selling-to-a-newcomer.md#shrinking-a-long-front-page-without-losing-a-fact): blocks move whole, anchors stay, and a script proves every old sentence still exists.

## The newcomer test

- **Readers:** two cold models from different labs, given no project context and nothing but the first screen, as Markdown with the pictures' alt text.
- **Questions:** what is this? who is it for, and is it for a curious non-specialist? what would you do next? which words confused you?
- **It passes** when both readers say what it is, who it is for, and a next step that exists. "Download the ISO" fails while there is no ISO.
- **Test the current text too,** so the review shows the difference.
- **Change one thing at a time, and test again.** Record every answer word for word.
- **A person,** when one agrees, is the last reader.

## Before and after, from this review

**Sentence one** (the edition README):
- Before: "Sparky Stereo OS 9 "Mashtabba", based on Debian 14 "Forky": the stereo 3D edition of SparkyLinux, KDE Plasma only."
- After: "Create and explore in 3D on the screen you already have: paint, edit photos and video, study molecules and globes, then watch films and play games."
- A cold reader went from "download the ISO and test it in a virtual machine" to "Since there is nothing to download, I would click the sign-up link for my language".

**Jargon one click down** (a developer link):
- Before: "a kernel whose VKMS speaks [HDMI®](https://www.hdmi.org/resource/brand) 3D, a 3D EDID, and the bench, IGT and KWin".
- After: "a virtual display that speaks HDMI® 3D, step by step, for driver, compositor and program developers".
- VKMS, EDID and IGT stay on the guide's page, where developers meet them in order.

**Name the number** (the Create door):
- Before: "paint in deep colour and in 3D".
- After: "paint in 3D and in deep colour (16 bits per colour instead of 8)".
- The reader who had asked "high bit-depth color, wide gamut, or something else?" then called it "clear in principle".

## Human and local-model review (2026-10-19)

The two-model exercise above records the original review method; it is not a requirement to buy access to two providers for every edit.
Use an independent human or available model when it adds useful evidence, with the same cold-reader questions; name the actual coverage.
A self-review is not an independent reader test. Do not fabricate reader responses when no reviewer is available.
Offer native-language drafting when helpful, following [ai-partners](../ai-partners/SKILL.md#language-and-accessibility), then retain meaning and uncertainty in the venue's language.
A relevant outreach contact can illustrate a use case before replying; it cannot appear as an adopter, collaborator or endorsement without evidence.
Keep precise implementation/proposal labels for the Theme Editor, toolkit depth, HDR and new device integrations.

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (including the demo page whose control panel hid its point).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

HDMI®, HDMI® High-Definition Multimedia Interface and the HDMI® Logo are trademarks or registered trademarks of HDMI Licensing Administrator, Inc.

## Explainers for a standards group, with respec-mcp (2026-11-06)

Written from ORDER 431, thirty-three explainers for the W3C PM-KR Community Group, one idea each.
An explainer is a front page for one idea: the rules above apply, and the group's own form adds three things.

**The recipe.**
1. Read respec-mcp's guidance first: `python3 respec-call.py resources`, then `read respec-mcp://skills`, `read respec-mcp://authoring-guide` and `read respec-mcp://skill/w3c-explainer`. The explainer skill routes to W3C's [Writing Effective Explainers](https://www.w3.org/TR/explainer-explainer/) and says to use the repository's existing format; in pm-kr that is Markdown in `explainers/`, so no ReSpec scaffold is needed for an explainer. Reports stay ReSpec and go through `respec_preflight` then `respec_validate`.
2. Plan the set before writing: one file per idea, with the idea, its sources and its reader in a table; an idea already covered by an existing page is linked, not rewritten.
3. Mark every page as an individual's input, in the same three lines each time: "**Status:** an individual's input to the ... Community Group, by NAME, DATE. It is not a decision or a report of the group. Comments and objections are welcome in this repository's issues." The group's name goes on nothing it did not decide.
   Under those three lines, one sentence saying why the page belongs to the group, in the group's own charter words and concrete to the page (what this topic asks of the group's subject), never a pasted slogan and never a claim the group has not decided; cold readers of pages without it asked why a 3D page was in a knowledge-representation group, and Daniel ordered the line on every page (2026-11-06).
4. One shape per page: the question in the reader's words; the idea, with the names it already has and where they come from (cite the clause); where it exists today, with its status said plainly (built, measured, proposal, not implemented); earlier work; what to try or discuss. Short: about 300 to 600 words, the special one longer.
5. Reuse names. Before naming anything, look it up in the group's glossary and in the specification; never invent a second name for an idea that has one.
6. Pictures as SVG with a `<title>` and a `<desc>`, no external references; a stereo pair drawn as side by side and as red and cyan; no personal places, accounts or mail.
7. Keep a claims table as you write (`claims.tsv`: explainer, sentence, source, where checked), one row per load-bearing claim; it is what the reviewer reads first.
8. Check links by script before the hand-back: relative links and anchors against GitHub's heading slugs (lowercase, punctuation dropped, spaces to hyphens), external links by HTTP status.
9. Run the repository's own checks (`respec_list_profiles`, `respec_preflight`, `respec_validate` with `--repo-root` pointing at your clone, never at a shared clone, because validate writes the build folder) and the publish check.
   Check every report against the profile the repository's reports page names for it, not each profile's default source: a page can claim a profile a report never satisfied and CI never notices when it only runs defaults. In pm-kr, `node scripts/check-reports.mjs` reads the README's table and `--list` feeds the CI matrix; show the check red on the old claim and green on the fix, and give each report its own profile with its real sections rather than bending a report to another's profile.
10. Cold readers on two pages, with nothing but the text, answers recorded word for word.

**Traps.**
- A posted comment that turns out wrong is never contradicted silently: say "corrected", link the correction where it is posted, and explain the reason in the text (the CSS Spatial z-axis insets are named like `top` and `bottom`, a distance measured from that side, so `inset-back` moves a box toward the viewer; "popped" is `inset-back: 100%`).
- A size is not a count: a 101 KB glossary is not "101 entries". Count before writing a number.
- Mailing-list archives: the index page's regular expression needs the real markup; fetch the index and grep its `href="NNNN.html"` entries, then open the message to confirm the words before linking it.
- A talks page's "Discussed at TPAC 2027" kind of slip in a thread you quote is quoted as said, with the date from the record; do not repeat the slip as a fact.
- `ask_cloud` can answer 429 from the local Ollama and `ask_chatgpt` can be unavailable; record the refusal word for word and try the other dispatcher or another model rather than inventing a reader's answer.
- A cold reader run as a subagent must be told the one tool it may call to hand its answers back; told "use no tools", it answers into the void (two runs lost that way on 2026-11-06). A required-reading hook can then refuse that handback until the reader has read files it was told not to read: say it may read them only after its answers are written and must not change them, or take the answers from its transcript's text blocks with a bounded script. Give the reader the page with its links intact, or it reports missing references that the page has.

**Perks.** The individual-input label lets a page be bold and early without the group's name on it, and the glossary makes the names free: every explainer's "The names, and where they come from" section is a lookup, not research.
