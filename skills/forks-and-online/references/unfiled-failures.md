# Keeping failures that cannot be filed upstream

Use this recipe when a project's reporting position prevents a report from being sent.
Keep the reason specific to the module whose position is recorded.
One module's position does not establish a KDE policy or another module's rules.

## Working recipe

1. Record the observed failure, the affected version and the evidence before drafting an issue.
   For the non-stereo inventory, the failure must also happen with stereo disabled.
   Exclude findings already accepted upstream, stereo-only failures and findings without evidence.
   Keep doubtful candidates separately with the missing check.
2. Search the approved records with bounded, non-symlink-following scans.
   Identify the failure separately from its issue, merge request and test references.
   A report and a patch for the same failure count once.
3. Query the project's default branch and pin its current commit and check date.
   Read the relevant implementation, its history since the affected base, the open and merged changes and the related reports.
   Record the exact queries and any inaccessible or incomplete results.
   An unchanged source mechanism is source evidence; it does not mean the reproducer was run on that revision.
4. Make the inventory first, for Daniel's review.
   The first line gives the number of distinct failures and separately the number of records.
   Each row names the program and component, says plainly what a person sees, links the evidence and our fix or says "none yet", gives the dated upstream status and links the related upstream reports.
   Leave the future issue link unset until the issue exists.
5. After the authorized publication step, use one issue per failure in Daniel's approved repository.
   For the KDE non-stereo list, Daniel chose one repository in his own Invent namespace, with issues alone.
   Preserve multiple historical records as references in the same failure's issue.
   If Daniel withdrew them, say they were withdrawn, with the date and the recorded reason, rather than calling them rejected.
   No report, comment or proposal goes to a KDE project's own tracker under the current hold.
6. Keep the record current when it is next reviewed.
   Recheck the default branch and related reports before saying a failure remains.
   When upstream fixes it, record the upstream commit, author, first containing version when known and the date checked.
   Close the downstream issue as fixed upstream only after the applicable fix is verified.
   Keep its historical evidence and distinguish a fixed historical finding from an unresolved failure in the counts.

The repository and its issues are prepared for review before the coordinator creates or posts them.

## Issue template

Title: what fails, using the component's words.

```text
Version:
[Program version, affected source commit and test environment.]

What happens:
[One concrete failure, in words a person using the program can understand.]

How to reproduce:
[Minimal steps and the expected and observed results.]

Cause:
[File and line at the pinned commit; distinguish a proven cause from a hypothesis.]

Fix and test:
[Our commit links and the failing-before/passing-after evidence, or "none yet".]

Related upstream reports:
[All related open reports with links; label historical closed reports separately.]

Upstream status:
[Check date, pinned default-branch commit, result and whether it comes from source inspection or a new runtime test.]

Status:
[Use the applicable approved status line below verbatim.]
```

Daniel approved two status lines on 2026-11-08.
Use the first only where the module's position is recorded:

> Not filed upstream: the developers of this module currently accept only fully human-written reports. That is their position, not an official KDE policy. Why: https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/not-filed-upstream.md

For a module with no stated position on AI-assisted reports, when Daniel’s hold on KDE contributions is the reason, use:

> Not filed upstream: I am not contributing to KDE projects for now. The developers of this module have not stated a position on AI-assisted reports. Why: https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/not-filed-upstream.md

Use only the applicable status line and its link for the reason.
The statement itself stays on the linked page, without copying or rewording it.
No personal reason, third-party contact address or severity rating goes into these issues.
A hold on all KDE contributions is not proof that each module has the same policy.
The recorded positions currently cover KWin and Krita; the second line applies to Marble, Plasma Workspace and Karton.
Recheck the module’s own record before changing its status line.
Credit project authors from their own records and related reporters by their public names.

## Writing public issues from private records

1. Read the private evidence, but write the public explanation from its measured facts.
   Keep the affected version, minimal reproduction, expected and observed result, fix and failing-before/passing-after counts.
   Do not paste internal reports, machine paths, task numbers, worker names or personal reasons.
2. Give the cause a public permalink to the file and line at an exact source commit.
   Link public fix and test commits where they exist.
   If a current-master fix exists only locally, say so and name its incomplete checks; do not invent a public link or imply that an older published patch applies unchanged.
3. Preserve the limits of the evidence.
   Source inspection is not a runtime reproduction.
   A test-only failure does not establish a production crash, a focused renderer test does not establish the complete application, and a simulated slow disk is not a hard-disk measurement.
4. List related open upstream reports and label closed historical records as closed.
   Keep one issue per failure even when the historical record contains both a patch and a report.
   Write the title and plain-language list entry from what fails, with one sentence per line and no hard wraps or mid-sentence dash.
5. Validate every public draft, the list and its manifest.
   The checker must reject private paths, internal task references, email addresses, missing headings, a status block that differs from its approved line, and a public link that an anonymous reader cannot resolve.
   Check the final URL as well as the HTTP status: a redirect to sign-in followed by HTTP 200 is not a resolved public issue.
   When the brief requests future issue numbers in a review draft, retain those exact proposed targets, mark the anonymous link check as blocked until the issues exist, and do not create or post them merely to pass the check.
6. Hand back the reviewed files and manifest for the authorized publisher.
   A planned issue number is not proof that an issue exists or that its final number will match.
   The publisher checks the actual numbers after creation and updates the list before it goes live.

## Traps found while making the inventory

- Symptom: three closed tracker records appear to be three failures.
  Cause: a merge request and its linked issue describe the same test failure.
  Fix: retain the requested historical records, but give them one failure identity and one future issue.
  Found by reading the merge request's linked issue and matching its cause and reproducer.
- Symptom: an older summary dates a tracker closure differently from the live record.
  Cause: a later policy discussion was confused with the earlier closure.
  Fix: keep the closure timestamp returned by the public tracker API, and describe the later discussion separately.
- Symptom: a report says "none found" after a broad tracker search.
  Cause: the first page was read without checking pagination, or a keyword match was treated as the same bug.
  Fix: follow the returned next-page field within a stated bound, inspect candidate descriptions and record any remainder.
  Save the query and response so the absence claim can be assessed.
