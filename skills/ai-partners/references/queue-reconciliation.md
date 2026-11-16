# Reconciling a long work queue against evidence

Use this when a numbered queue has grown for weeks, status words inside it contradict each other, and someone must say what is really open.

## Recipe

1. Freeze the sources and the numbering. Save the queue, its previous reconciliation, the source revision and package indexes with their capture time and hashes. List every task id, including lettered sub-items; do not turn a count, line number or hash into a task. Compare the body with its stated range and counts. The total is the checksum; the final list must contain each base id once, with sub-items retained beneath it.
2. Check implementation against merges in the build repository's main branch, packages in the published repository index, branches on the forks, sent messages in the promises ledger and coordinator acceptances. Use status words as leads. Check the actual scope: a merge proves its change, a package index its version, a sent message its delivery. None proves that every part of the original request is finished. The person's latest decision governs intent and can reopen accepted work.
3. Make a dossier per id with a script: its entry, the newest dated note that names it, the lane folders that end in the id, the report status line, the number of matching commits. Read the dossiers in batches and decide each id.
4. Sort into: in flight, open (in the project lead's order), parked (with the quoted reason and what unparks it), waiting on the project lead (only the questions no recorded decision answers), done (with the evidence), merged into another id (naming it).
5. Keep an item open when no delivery evidence can be found, even when its entry says "queued" long ago. Search the earlier reconciliation and differently named lanes before saying never started. Forks holding only upstream branches establish that no implementation is visible there; work may still exist as an accepted stage or in another repository.
6. Count each bucket and compare the sum with the checksum from step 1.

## Keep the list true between reconciliations

Update the canonical record whenever work is accepted, rather than waiting for the next audit.

1. Find the parent request and every affected follow-up before closing a lane. Preserve the date of the person's original request and a short exact quote with its source. A filing date or a later restatement never makes old work newer. If the original words or date are missing, record the gap rather than inventing either.
2. Record the accepted scope, the accepting reviewer, the time and the evidence: source revision, fork branch, package version and artifact location as applicable. Separate accepted, staged and published. A staged successor does not change the published version; update that field only after publication is verified.
3. Compare the acceptance with the request clause by clause. Write what remains, what it needs and which item owns it. An accepted study closes the study, while implementation stays open. A configuration-only part can ship separately from its larger settings interface. Keep the parent's remaining clauses visible when creating that child.
4. Change the lane's report status and the queue record in the same acceptance step. Regenerate the open-design view and counts, then check that every id still occurs exactly once. Preserve the previous snapshot so that a later reader can tell what changed. A renamed or merged item keeps its number and the destination that now owns its work.
5. Show the person's open design requests first, ordered by the date of their words, across technical tiers. At the next free lane, take the oldest eligible design request. Only breakage, security or a running publication's blocker jumps ahead; record which exception applies and why. Keep explicit parks and dependencies visible, and do not interrupt running work.
6. At publication, reconcile the accepted versions against the published index, update the delivery state and remove superseded stages from the next cohort. At the next dispatch, check this record again. Progress among recent numbers is not evidence that early requests were delivered.

Use one machine-readable state file with one row per id, and keep the dated journal as history.
Record the true origin separately from status: a person's request, a follow-up, a finding, security, breakage, a publication blocker, outreach or maintenance of the process.
A follow-up does not inherit the person's authorship just because its parent was requested by them.
Preserve an explicit reason and the person's recorded words for any priority exception.
The dispatcher reads this state and refuses unregistered work or a younger request while an eligible older request is waiting.
The coordinator updates it at launch, hand-back, acceptance and publication; a worker submits a proposed delta and does not silently overwrite shared state.

Before hand-back, validate the exact schema, allowed values, unique ids, complete base range and every lettered follow-up that has its own lane.
Compare the readable view with those same rows, counts and original request dates.
Run the project's own state audit as well; report disagreements with old report labels instead of changing a truthful state to silence the audit.
Freeze a cutoff and list later events separately so a long audit can finish.

When an intermediate audit is authorized, name the range actually adjudicated and retain the other numbers with their source pointers.
When the assignment requires the complete list, finish every row before handing back.
If evidence cannot be found in reasonable time, give the row an explicit unknown status with the exact missing scope, acceptance or artifact; a pending placeholder is not a completed decision.
Never present inherited status words or a script's matches as a definitive reconciliation.

## Traps

- Symptom: an entry says RUNNING or QUEUED but nothing runs. Cause: status words are written once and never revised. Fix: trust the lane report line and the merge log. Found by: comparing the entry with `head -1 lane/REPORT.md`.
- Symptom: a lane report says "review" or "queued" for work that is published. Cause: the report is written at hand-back and the acceptance is recorded only in the queue file. Fix: find the merge or the package, then call the status stale in your report. Found by: the package index listed the version.
- Symptom: a package from an item is missing from the repository index. Cause: the build was accepted and merged but waits for the next publication round. Fix: mark the merged implementation accepted and its package staged, with the planned round; close the parent only if its whole scope is accounted for. Found by: the cohort list of the next round.
- Symptom: two items describe one job (a package of the same runtime, asked twice). Cause: later notes restate an earlier item under a new number. Fix: merge the later into the earlier, keep both numbers in the list, never close either. Found by: grepping both entries for the same repository name.
- Symptom: a first reconciliation exists only as a brief. Cause: the lane's hand-back was a message that was never saved. Fix: renumber it into the new reconciliation, do not close it.
- Symptom: a grep over the queue file fails with a complexity error. Cause: very long lines and a wide context pattern. Fix: read the file with a script and slice around the match.
- Symptom: an item looks unstarted but its work lives elsewhere. Cause: the evidence is in a repository you did not search (a skills repository, a documentation fork). Fix: list the ids you could not decide, with what is missing, instead of guessing.
- Symptom: a reconciliation claims one id range but contains later entries and revised statuses. Cause: the old deliverable became a working list without updating its date, counts or change record. Fix: freeze its actual contents, compare body ids with the declared range and describe it as a mutable baseline. How found: the saved list contained nine additional base ids despite retaining its original total.
- Symptom: a first pass calls old work never started, while an accepted implementation exists in another lane. Cause: it inspected the original brief's folder and skipped the earlier reconciliation. Fix: follow the previous list's evidence to the implementation lane, source merge and published version; preserve any remaining kernel or outreach work. How found: an original brief-only folder coexisted with accepted library and compatibility-layer builds in a numbered lane.
- Symptom: an accepted cleanup job seems to close a request for a desktop cleanup page. Cause: the same short name hides different outcomes. Fix: compare the original requested interface with the delivered maintenance operation; keep the interface open until it has its own evidence. How found: the early request specified a settings page and preview, while the later report measured recovered disk space.
- Symptom: completed high-number follow-ups coexist with an early audio design that never shipped. Cause: each fresh finding took a free lane, and no acceptance refreshed an oldest-first design register. Fix: maintain that register at every acceptance and dispatch; split already-designed defaults from the larger interface. How found: the original request specified hardware-based rates, while the later installed-state check still showed stock defaults.
- Symptom: an accepted lettered sub-item appears to close an unrelated part of an older design. Cause: the same id was reused for a different task. Fix: preserve both meanings and their source pointers, leave the original remaining work visible, and have the coordinator assign unambiguous ownership before closing it. How found: the early integration plan used a letter for camera integration, while the later acceptance used it for encoder metadata.

- Symptom: a complete-queue assignment stops after its first useful tranche. Cause: a generic milestone habit overrides the requested hand-back scope. Fix: keep working through the required range; resolve unavailable evidence to unknown with a precise missing-proof note, then verify full coverage. How found: the first hand-back had retained later numbers but left their decisions pending.
- Symptom: every report saying review is counted as an unreviewed hand-back. Cause: accepted reports retain their old label, or a later review accepts only a smaller slice. Fix: compare each report's scope with the coordinator's acceptance; separate unreviewed work, reviewed work awaiting a decision and accepted work with a stale label. How found: the same census contained published packages, sent texts and a report explicitly named as unreviewed by the coordinator.
- Symptom: a numbered hole is described as never assigned even though a later entry gives it a subject. Cause: the old reconciliation omitted the original entry and the journal later reused the reference. Fix: keep the conflicting attribution and missing original scope visible as unknown until the coordinator resolves it. How found: a supposedly empty number reappeared as a reference for a shared per-file choice interface.
- Symptom: the state audit passes while numbers or lettered lanes are missing. Cause: its checks cover report disagreements and legal statuses, not the assignment's coverage contract. Fix: add an independent census against the required range and lane inventory, then compare the readable and machine-readable views. How found: the project's audit had no duplicate-id or complete-range check.

- Symptom: an early task acquires an acceptance from a much newer lane. Cause: a parser treats a milestone number, kernel build number or merge-request number as the task id. Fix: require the subject relation and reject those numerical roles before attaching acceptance; inspect every changed verdict and preserve explicit scope decisions. How found: an editor request appeared to inherit a kernel publication, and a power-management request inherited an unrelated merge request.
- Symptom: a valid-looking exported row has no name or request date. Cause: the seed contained an empty name, or a dated journal paragraph introduced several following bullets. Fix: validate nonempty identities, recover each name from its own source and inherit a paragraph date only with its source pointer; leave an unrecoverable historical date visibly unknown. How found: the full census passed before the schema check exposed the blank name, and four rebase requests lost the date on their shared introductory paragraph.

## Rules

- Never drop an id; a partly done item stays open with what is left.
- Evidence is a thing you can point at; an agent's report that says "done" is a lead.
- A new idea joins the end of its part unless the project lead puts it ahead.
