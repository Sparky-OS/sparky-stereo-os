# The first thread on a standards group's list

Written on 2026-11-10, after a working group's chair answered a meeting abstract that held six topics: bring changes to the public list, one topic, no personalities, and build consensus "around use cases, modified specification prose/diagrams, implementation and evaluation of examples".
The abstract had shown finished work; the list wanted a question it could work on.
This is the recipe for the post that follows such an answer.
[A meeting abstract for a standards group](meeting-abstract-for-a-standards-group.md) is the text that came before it.

## Recipe

1. One topic. Pick the one with the plainest use case and a measurement behind it, and keep the others in a private gap map: one row per gap with its use case, its venue and whether it is measured, read or only an idea.
2. Open with the use case in one sentence a newcomer follows: who, on what, expecting what. No product name in it.
3. Say what the specification says today, clause by clause, by number, from the primary text you saved with its SHA-256. Say what you did not find ("I found no word about ...") instead of "the specification lacks".
4. Say what implementations do today, with the numbers as measured and their conditions (which implementations, which route). Start with what already works.
5. Put two or three open questions, each answerable by someone who has not read your work. A question that names its possible answers ("the author, the browser, or only the person?") gets answers; "what do you think?" does not.
6. Describe one experiment the group can run without changing the specification: the names and values, the node or element they sit on, how an implementation reads them, and how the result is evaluated the same way by everyone. Use the extension point the group itself named (for X3D: a `MetadataSet` on the node's `metadata` field).
7. Describe the experiment; do not build it ahead. The words must be enough for anyone to build it. Build it when the thread engages.
8. Name no person in the post. Projects and clauses are named; credits go in your own records and files.
9. Say AI assistance once per list, where it was first said, and not again in the thread.
10. End with one small question that moves the thread ("which of the three questions first?").
11. Keep it near 40 lines, one sentence per line, and prepare a 10-line version; the chair or the list's habits decide which fits.
12. Check before the hand-back: the count of lines, every clause quote against the saved page, every number against the report's own table, and that every link is public.

## Traps

- Symptom: the post offers two fields "with both absent a scene behaves as today", and the list reads a solution to approve or reject.
  Cause: the draft was written from the design document, where the fields were already chosen.
  Fix: move the chosen names into the experiment as working names, and turn each design decision into the question it answered.
  Found by: rereading the chair's sentence on use cases before the draft was finished.
- Symptom: the experiment asks every implementation to read metadata, and a reviewer answers that an implementation must not.
  Cause: the clause on metadata was cited by number without reading it: X3D 7.2.4.3 says "The content of the value field of a metadata node is not interpreted by the X3D browser."
  Fix: read the clause and say it in the post as the experiment's safety: scenes stay valid, and an implementation that does not take part shows them as today.
  Found by: fetching the Core component's page before writing the experiment paragraph.
- Symptom: "the scene sat behind the screen" reads as a defect of the two libraries.
  Cause: the sentence left out that both libraries follow the session exactly.
  Fix: put what works first, with its number, then what nothing describes.
- Symptom: a sentence says how an implementation "would" honour the value in a route nobody measured.
  Cause: the measured route (the browser's own setting moved) and the described one (the scene scaled to the session's metres) give the same geometry, and the draft merged them.
  Fix: keep the described route as a description, and say in the reviewer's notes which one was measured.
- Symptom: a quoted figure is one of two the report holds (25.45 and 21.9 degrees).
  Fix: quote one, and tell the reviewer in the notes that the other exists and where.

## Perks of this part

- A specification's existing field can be the question: X3D's `avatarSize` already states "the user's physical dimensions in the world", and `centerOfRotation` already names the point of interest. Asking whether an existing field answers the gap invites the editors' own knowledge.
- The gap map tells you what the next thread is before the first one is answered, and which gaps never belong on this list.
