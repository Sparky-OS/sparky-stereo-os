# upstream-outreach: lessons from the lanes of 25 October to 6 November 2026

Harvested by ORDER 429 from the accepted lane reports; each line names the lane it came from.
A trap gives its symptom, its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Recipes that worked

- Sourcing a market claim: the producer's own release first (analyst report, results page, platform survey), fetched and marked primary; press only as "press quoting X"; a primary that refuses the fetch is "not read", never dropped; one search per studio or product fact (combined queries returned unrelated results); merges recounted through each forge's API with refusals recorded (Qt Gerrit 403, the Debian Salsa mirror API 403) (lane stereo-report-2-378)
- Shape that fit a company that had not answered a letter: at most one personal note now, to a new person who has public words to answer, with one new fact and one people ask; other notes held until the pull request that is the real lever is open; never two notes into one company on the same day, a week apart at least. Skill has "One knock at most"; this adds the hold-until-the-lever rule. (lane valve-outreach-218)
- A form or LinkedIn follow-up to an organisation already emailed names that email, says it may be in a spam folder, and gives the short version; the 200-character connection note stays clean (counted: 172, 166, 186). (lane valve-outreach-218)
- Facts in an update message are checked first: a count that cannot be reproduced (117 vs 122 commits) becomes "the same commit as X (hash)"; no number of skills, no "releases" when only packages exist; the maintainer's own repository is linked first, then the package here; the thread number belongs to the repository that holds it (a same-numbered pull request elsewhere is another thing); a person's first name is public only where they sign with it. Block lengths measured (744 to 2,350 characters; LinkedIn under its limit). (lane helpers-update-220)

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: names in a transcript do not match people ("Morasi", "David Feisy", "Carly Knight"). Cause: speech-to-text. Fix: verify each against the company's people page, press pieces and the event page before drafting; drop people whose project is already in the contact's tracker and routes that are press-only. Found by: Wikipedia, the people page and press articles. (lane valve-outreach-218)
- Symptom: a roster of event attendees changes while you prepare (18 additions and 1 removal between a morning and an afternoon check). Fix: recheck the public session lists shortly before use; verify with a script that compares the saved snapshot with the documents (exact roster coverage, proposers first, no duplicates, zoneinfo time conversions); drop region names that are not cities; include no emails, profile links or inferred views. (lane tpac-room-people-271)
- Symptom: two pull requests closed with `merged=false`. Cause: the maintainer applied the change as his own commit. Fix: retrieve and read the actual commits before calling it merged; claim a merge only when merged (see also the rebase-is-not-a-merge rule). Immutable-ref comparison (v1.9.0 before and after) proves nothing else moved. (lane stack-map-iana-273)

## Measured facts

- Pattern record: two AI-assisted MRs closed while the maintainer pushed his own commits for the same bug the same day with only a commit-list note; verify by comparing timestamps and commits before any reply (lane kde-pattern-288)
- A comment on an open public issue that answers the issue's own question (one eye, the dominant eye, in Steam Frame spectator view per SteamOS 0.4.1; the side-by-side pair as the stereo version) is a better public venue than a message. Steam Audio issues unanswered by Valve staff since at least Feb 2026. (lane valve-outreach-218)
- Keep a group's governance role apart from staff pilot intake (a charter can exclude pilot selection); recheck session pages before the event; do not invent slides or marketplace locations; a donation offer is not a promise of new bespoke maintenance. (lane tpac-extra-cards-264b)

