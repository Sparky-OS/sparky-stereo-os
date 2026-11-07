# Reconciling a long work queue against evidence

Use this when a numbered queue has grown for weeks, status words inside it contradict each other, and someone must say what is really open.

## Recipe

1. Freeze the numbering. List every id the queue file uses: entries that start a line, ids named in dated notes ("ORDER 311", "item 15"), and lettered sub-items. The total is the checksum; the final list must contain each id once.
2. Read the sources in this order of trust: (a) merges in the build repository's main branch (`git log --grep`), (b) packages in the published repository index, (c) branches on the forks (`git ls-remote`, `gh api`, read only), (d) sent messages in the promises ledger, (e) the first line of each lane's report, (f) the dated notes, (g) the status words in the entry itself. A lower source never overrides a higher one.
3. Make a dossier per id with a script: its entry, the newest dated note that names it, the lane folders that end in the id, the report status line, the number of matching commits. Read the dossiers in batches and decide each id.
4. Sort into: in flight, open (in the the project lead's order), parked (with the quoted reason and what unparks it), waiting on the project lead (only the questions no recorded decision answers), done (with the evidence), merged into another id (naming it).
5. Items with no lane folder, no commit and no package are open, even when the entry says "queued" long ago. Check the upstream forks for the same: a fork that holds only upstream branches proves the work never started.
6. Count each bucket and compare the sum with the checksum from step 1.

## Traps

- Symptom: an entry says RUNNING or QUEUED but nothing runs. Cause: status words are written once and never revised. Fix: trust the lane report line and the merge log. Found by: comparing the entry with `head -1 lane/REPORT.md`.
- Symptom: a lane report says "review" or "queued" for work that is published. Cause: the report is written at hand-back and the acceptance is recorded only in the queue file. Fix: find the merge or the package, then call the status stale in your report. Found by: the package index listed the version.
- Symptom: a package from an item is missing from the repository index. Cause: the build was accepted and merged but waits for the next publication round. Fix: count a build-repository merge as done and write "publishes in round X". Found by: the cohort list of the next round.
- Symptom: two items describe one job (a package of the same runtime, asked twice). Cause: later notes restate an earlier item under a new number. Fix: merge the later into the earlier, keep both numbers in the list, never close either. Found by: grepping both entries for the same repository name.
- Symptom: a first reconciliation exists only as a brief. Cause: the lane's hand-back was a message that was never saved. Fix: renumber it into the new reconciliation, do not close it.
- Symptom: a grep over the queue file fails with a complexity error. Cause: very long lines and a wide context pattern. Fix: read the file with a script and slice around the match.
- Symptom: an item looks unstarted but its work lives elsewhere. Cause: the evidence is in a repository you did not search (a skills repository, a documentation fork). Fix: list the ids you could not decide, with what is missing, instead of guessing.

## Rules

- Never drop an id; a partly done item stays open with what is left.
- Evidence is a thing you can point at; an agent's report that says "done" is a lead.
- A new idea joins the end of its part unless the project lead puts it ahead.
