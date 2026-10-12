---
name: writing-front-pages
description: How to write the first text a stranger meets (a README's top, the organisation profile, the repository server's README, beta-tester calls, the openings of lists and documents, repository About lines): person first, a picture, short, plain words, honest status, doors per reader, one next step, and a cold-reader test before it goes out. Load the general sparky-stereo skill first.
---

# Writing front pages

**Check freshness first.** Written on 2026-10-12, from the review of the edition's public texts: the README, the organisation profile, the beta-tester calls, the documents and the three open lists. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first. If the [README](../../README.md) shows a newer practice, it wins.

**The problem it solves.** The work was right and the texts were accurate, but a newcomer could not tell what the project is for.
The content stays; its order and its words change.

**Where it applies:** every text a stranger meets first.
**Where it does not:** upstream pull requests and issues. Maintainers want the technical detail there, and [`sparky-stereo`](../sparky-stereo/SKILL.md) Part three applies.

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
2. **What they need,** and what it costs ("cheap red-cyan glasses").
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

## Keep every link that points in

Before moving a heading, find who links to it: talk slides, forum posts, other lists, the issues.
- Keep each linked heading, or leave `<a id="old-anchor"></a>` where its content now starts.
- Check every relative link and anchor in the changed files before handing back.
- Keep a claims table (draft line, source file and line, and where each moved fact now lives), so a reviewer can check that nothing new was claimed and nothing was lost.

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
- Before: "a kernel whose VKMS speaks HDMI 3D, a 3D EDID, and the bench, IGT and KWin".
- After: "a virtual display that speaks HDMI 3D, step by step, for driver, compositor and program developers".
- VKMS, EDID and IGT stay on the guide's page, where developers meet them in order.

**Name the number** (the Create door):
- Before: "paint in deep colour and in 3D".
- After: "paint in 3D and in deep colour (16 bits per colour instead of 8)".
- The reader who had asked "high bit-depth color, wide gamut, or something else?" then called it "clear in principle".
