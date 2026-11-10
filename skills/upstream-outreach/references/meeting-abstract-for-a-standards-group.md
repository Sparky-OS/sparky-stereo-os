# A meeting abstract for a standards group

Written on 2026-11-09, from the abstract for an X3D Standards technical review that the chair asked for, to share it on the group's public list.
An abstract of this kind is read by the whole list, so it is checked like any other public post.

## Recipe

1. Read the group's list for the two weeks before the meeting, every thread that touches your topics, before writing a line. A draft written from your own earlier mails misses what moved since.
2. For each of your topics, name the list's own open proposal next to it and credit its author by the name on their message. Use the name the list already gave the idea, never a second one.
3. Say how your proposal relates to theirs in one sentence that you checked against the clause: the same thing, a part of it, or something that works beside it. Do not claim yours gives what theirs gives until the clause text shows it.
4. Read each clause you cite again in the current draft, from the address the chair gave, and save the page with its SHA-256.
5. Give the chair what they need to paste it: a title, the day with the local time and UTC, your name and affiliation, then the body. Keep the greeting to the chair outside that block.
6. Commit only to what you already promised in the thread, in the same words. A measurement promised stays a measurement and does not become a live demonstration.
7. Scope every measured claim to the route and the range that was measured.
8. Keep it near 300 words of body. When a topic must go, cut the one the list has not discussed.

## Traps

- Symptom: the saved text of a draft clause shows doubled wording ("26.3.7 26.3.6 HAnimSite", "can shall be used") and nothing tells a settled sentence from a pending one.
  Cause: Web3D's draft pages carry the change status as markup, `class="proposed"`, `class="proposedDeletion"` and `class="editorsNote"`, and stripping the tags drops it.
  Fix: list the marked passages from the HTML before quoting, and say the status with the quote.
  Found by: counting the `class=` values in the page after a field read as settled turned out to sit in an editors' note.
- Symptom: a sentence such as "today's followers cannot overshoot" reads as proved.
  Cause: the clause proves it in words for one node family only (X3D 39.3.2: a damper "consists of a set of linear first-order filters"), and the other family's core function is an equation image.
  Fix: name the family the text covers, or read the equation image before widening the claim.
  Found by: searching the saved text for the function and finding only "Equation (2)".
- Symptom: "every scene sits behind the screen" in a draft, while the measurement behind it covered one route.
  Cause: a result was carried from a report's summary line without its conditions.
  Fix: open the report's own table and copy the route and the range into the sentence.
- Symptom: two implementers support one proposed field, and their descriptions differ in one case.
  Cause: each wrote from their own implementation (here: a fraction computed as one minus the specified value, against a fraction that continues from its last value when the direction changes while active).
  Fix: put the differing case to the meeting as a question; never pick a side in the abstract.
  Found by: reading both messages and the extension's own page against the clause formula.

## Perks of this part

- A draft's editors' notes are the editors' open questions. A proposal that answers one of them is an answer, and the abstract can say so in their words.
- The sibling specification often already has the idea under another shape (glTF's interactivity extension plays an animation in reverse when `startTime` is greater than `endTime`). Reading it tells you what the list's proposal has to stay compatible with.
