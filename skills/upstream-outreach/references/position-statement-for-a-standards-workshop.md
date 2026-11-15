# A position statement for a standards workshop

Written on 2026-11-15, from a statement of one to two pages for a joint workshop of three standards bodies, whose draft call asked for one or more of three kinds: a critique of its principles and their trade-offs, a deep dive on one technical challenge, or a map of standards and gaps.
A statement of this kind is read by a programme committee that has already seen your comments and mails, so it must be the fuller argument behind them, never a repeat.
Its siblings are [a meeting abstract for a standards group](meeting-abstract-for-a-standards-group.md) and [the first thread on a standards group's list](first-thread-on-a-standards-list.md); the front-page rules in [writing-front-pages](../../writing-front-pages/SKILL.md) apply to its first paragraph.

## Recipe

1. Read the call as a specification: its kinds of statement, its length, its numbered principles and challenges, and every open comment in its margin. Number them, because the map below refers to them.
2. Collect what the committee has already read from you: comments in the call's document, mails to the organisers, the minutes of the session the workshop came from. The statement agrees with each of them and adds what they could not hold.
3. Write the threads map before the first sentence: one row per thing you want to contribute, with the industry or group it connects, its evidence (a public address or file) and one status word (built, published, merged upstream, proposal, paused, planned), which principle, challenge or comment it answers, whether the committee has already seen it, and its place: in the statement, behind which link, or left out with the reason. No row may end "later".
4. Choose the form from the call's own kinds and say why. A statement may span kinds when one sentence still states its position; a tension between principles is named only when your work has met it, with the record that shows it.
5. Give the statement one spine and put it in the first paragraph, person first: what a person can do, what exists, what is a design, and how the first leads to the second. Say plainly which is which; a paused design is "the model, not the specification".
6. One section per tension or challenge, each in the same order: what the call says, what exists (with its link), what is missing (quoted from the text that shows the gap), and what you propose. Credit what others built first, by the names their own records use.
7. Close with what you ask of the workshop, as a short numbered list of changes to its own text or agenda. Offer what is public; promise no demonstration, date or work.
8. Put every remaining thread behind one link each in a closing line, or behind an index page that lists them, so that nothing you want to contribute is more than one link away.
9. Keep a claims table as you write: each sentence, its source (a file and line, or an address fetched that day) and its status word. A sentence with no source is cut or marked as the author's view.
10. Check every state on the day: each issue and pull request you cite (open, merged, how many comments and by whom), every link by its HTTP status, and each quoted clause against the saved page with its SHA-256.
11. Write the one-page cut from the two-page one by removing evidence sentences, never the spine, the status words or the asks; then check that it holds no sentence the long cut lacks.
12. Hand over cold-reader questions (what is this, who is it for, what would you do next, which words confused you) and three places where a specialist of each industry in the room would push back, each with the answer the text already gives or the change you made.

## Traps

- Symptom: the draft says a format "already holds all three" kinds of content in one file.
  Cause: one of the three was a ratified extension and another only a draft proposal in the same repository.
  Fix: give each part its own status word in the sentence ("ratified", "a draft there").
  Found by: reading the extension folder's listing and each README's Status section on the day, after the sentence was written from a summary.
- Symptom: a documentation page is cited for what a product does, and the check returns 200.
  Cause: the page is drawn in the browser, so the fetched file holds only a title; the status says the address exists, not what it says.
  Fix: cite beside it a public page that states the fact in text (a talk page, minutes), and say in the hand-back that the product page's text was not read.
  Found by: stripping the tags from the saved file and finding only the site's title.
- Symptom: a list message is described as public, and its subject is not in the list's archive for that month.
  Cause: a message can be sent to a public list and never reach its archive.
  Fix: fetch the month's subject index and look for the subject before citing; without it, claim only what a public document shows.
  Found by: listing the archive's subjects and counting its messages.
- Symptom: a sentence says "nothing describes" how two things work together.
  Cause: an absence was written from one specification, while a sibling specification covers part of it (progressive delivery, in this case).
  Fix: write "I found no text for", name the part a sibling does cover in the claims table, and narrow the gap to what is left.
  Found by: rereading a specialist's published mapping of the sibling specification after the sentence was drafted.
- Symptom: the two-page cut is a third over its length after every thread has a sentence.
  Cause: threads were given sentences instead of places.
  Fix: a thread that asks nothing of the workshop goes behind a link; the closing line of links costs one word or two per thread.
  Found by: counting words per section with the link targets removed.
- Symptom: a quote from a recording is in the draft and the captions cannot be reached.
  Fix: keep at most one short quote, attribute it to the event and not to a person, link the recording, and list it as not rechecked in the hand-back; paraphrases of the other points stay out.
- Symptom: a style check flags "the owner" in "a scan of the owner's own room".
  Cause: the check guards a rule about naming a person, and the phrase reads the same to it.
  Fix: reword ("a scan of its own room").

## Perks of this part

- The call's own margin comments are its author's open questions; a section that answers one of them in the author's words is read first.
- The minutes of the session the workshop came from are the statement's standing: quote the line that set the next step.
- A registry of real pages that anyone can open is evidence for the map of gaps even while it has few entries; say how many, and that entries are welcome.
