# Adding a planned capability to every front page

**For** anyone asked to put on the front pages something the edition does not do yet: where the word goes, which words carry the status, and how nine languages change together without a broken anchor.

Written on 2026-11-10 from ORDER 502, "scan": turning a video of an object or a place into a 3D model, with a program the edition has forked and not yet shipped.
The rules of [the skill](../SKILL.md#the-rules) come first.

## The recipe

1. **Read the program's own records before a word is written:** its README, its licence file, its licences folder, its releases, and the author's name as the profile and the README give it.
   `curl https://api.github.com/repos/OWNER/REPO` gives the description and the licence, `/contributors` the people, `/contents/LICENSES` the third-party licences, `/releases/latest` the builds; `users/OWNER` gives the name the author uses.
   Save the answers as evidence; every claim on the page must be found in them.
2. **Leave sentence one alone.**
   Sentence one lists what a person can do today, so a planned verb in it reads as done.
   The word goes into the doors it serves, as a second sentence of the door: "Scanning is planned: a video of an object or a place becomes a 3D model you can walk around."
   The status word comes first, then the act in everyday words; the technique's name ("3D Gaussian splat") waits one click down.
3. **One door per reader it serves,** each with that reader's nouns: an object or a place for creators, a part, a site or a specimen for engineers and scientists.
4. **One paragraph on the detail page,** after the list of what works and before the section's closing link, under an explicit `<a id="word"></a>` and a bold lead "**Planned: ...**":
   what the person does, then the program's name with its link, its author and its licence as its records give them, then a second "**Planned:**" line that says the two things missing (not shipped, no view per eye) and where the work will happen.
   Other sections link to that anchor with one bullet; they do not repeat the paragraph.
5. **Credits where the repository keeps them.**
   Check that the credits page already lists work in progress or planned (search it for "in progress" and "Planned") before adding a planned program; the row says "Planned, not shipped yet" in the column of what we changed, and names the third-party licences from the program's own licences folder with the holder each licence file names, never a holder from recall.
6. **The organisation profile:** the planned line beside its "Coming" line on the detail page, and the fork in the repository table with "(planned)".
   The profile's first screen follows the README's sentence one, so it stays as it is.
7. **Calls for testers stay as they are** until the program ships: a call asks people to test what exists.
8. **Nine languages together.**
   Write each language's line in that language, with the words its page already uses for the same idea (search the translated page for the term first: the page that says "skany 3D" for a splat tour gets "skanowanie").
   The anchor is the same English `id` in every language, so one fragment works everywhere.
   Where a language has no detail page, its front page links the English one; say so in the hand-back.
9. **Check by script:** for every changed file, the sets of links, anchors and headings before and after (nothing lost, only the intended additions), every relative link and fragment resolved, and a control that fails (a fragment spelled wrong must be reported).
10. **Cold readers on the first screen, before and after,** with one question added after the change: "can a person do this today? quote the words that tell you".
    The answer must be no, with the status word quoted.
11. **A second model reads each translation,** one call per language, with the English beside it and three questions: errors, a meaning that differs (the status above all), unnatural wording.
    Take the fixes that keep the page's own vocabulary, and record what was not taken and why.

## Traps

- **Symptom:** a draft line says the program "has no 3D view yet", and a reader who knows it objects: it has a 3D viewport.
  **Cause:** on this desktop "3D" means one view per eye, and in the program's own words it means a scene on a flat screen.
  **Fix:** say what is missing in full: "it does not show its models in 3D with one view per eye yet".
  **How it was found:** rereading the line beside the program's README.
- **Symptom:** a review request for a language returns an empty answer, or the dispatcher answers "410 Gone" for a model.
  **Fix:** ask the same question to a model from another lab, one language per call, and name the model that answered each language in the hand-back.
- **Symptom:** a reviewer proposes a "better" word for fork, scan or edition.
  **Cause:** the reviewer has not seen the rest of the page.
  **Fix:** the page's own word wins; note the proposal in the hand-back.
- **Symptom:** the visible word count of the first screen grows by two sentences per language.
  **Cause:** the doors are part of the first screen.
  **Fix:** keep each added sentence under twenty words, count before and after with the same script, and say both numbers.

**Perks.** A planned line written this way needs one edit when the program ships: the status word changes, and the anchor, the links and the credits stay.
