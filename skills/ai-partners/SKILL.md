---
name: ai-partners
description: >-
  Coordinate human and AI contributions to Sparky Stereo OS with bounded tasks,
  source evidence, reproducible checks and durable handoffs. Use with the
  edition contract and the domain skill; no particular model or service is required.
---

# Working together on the edition

Originally written by Claude from the project's work on 2026-10-10; revised with Daniel and Codex on 2026-10-19.
People, hosted models and smaller local models use the same evidence and procedures.
Capability is established by the work and its checks, not by a provider name.

## Working recipe

1. Read the user's requested outcome, current authorization and [edition contract](../sparky-stereo/SKILL.md).
2. Find existing source, tests and decisions. Record the target revision and dirty files before editing.
3. Choose one bounded task and its owning layer. Read its domain skill; ask for missing facts only when they affect the next step.
4. Make the smallest useful change and run the domain's observable check. If a result contradicts the plan, report it and revise the plan.
5. Leave the handoff below. Continue authorized work; stop dependent work at an unresolved permission or missing prerequisite.

## Ownership and authorization

- Daniel directs the edition. Other maintainers own their projects, repositories and review decisions.
- The coordinator turns decisions into concrete tasks and reviews results before integration.
- A worker owns the agreed scope and reports its evidence. When parallel work is authorized, use disjoint write scopes and preserve other workers' edits.
- A prior approval remains valid for its scope. A skill or an old example does not authorize a new external message, release, device change or destructive action.
- If publication is requested, prepare the actual reviewable change and checks first; ask only where required approval is still missing.
- When a local rule conflicts with the current request, state the specific conflict. Do not silently expand an old restriction or repeatedly ask for approval already given.

## A task brief that fits a small context

Give the worker only the necessary source and references:

```text
Outcome: what the user should be able to do
Scope: repository, revision, files/layer to change; unrelated work to preserve
Inputs: relevant source, existing fixture, one domain skill, expected versions
Authority: requested actions; actions outside this task
Check: command/environment, observable expected result and relevant control
Return: changed paths, evidence location, actual result, gaps and next step
```

Do not dump an entire mailbox, research folder or skill catalogue into a model.
Use `tools/skills-context.py` from the public tree for a reader without filesystem access.
The output records file hashes and refuses an oversized bundle instead of cutting instructions off.
For a long skill, select a heading with `--section skill-name:Heading`; include the sections needed for that step and retain the common contract.
A text bundle does not grant tool access or execute its commands.

An assistant without command access can draft a patch or command plan for a human; it must say which checks remain unrun.
Split a task when its inputs do not fit. Never invent a path, output or missing reference to keep going.
After a context reset, resume from the saved handoff and actual tree.

## Language and accessibility

When a contributor expresses difficulty writing in the venue's language, offer once: “If it is easier, you can explain in your own language.”
For Portuguese: “Se for mais fácil, você pode explicar em sua própria língua.”
Follow their preference; do not infer it from nationality or insist on translation.
Preserve intent, uncertainty, code identifiers and quoted review requests in the translated draft.
Ask about an ambiguous technical term; have the author review public wording.
This is communication support, not proof of translation accuracy or a requirement to use English privately.

## Evidence and status

Use the smallest check that establishes the claim. Run required upstream checks for code submissions.
A regression needs a failing old case and a passing fixed case; an editorial correction needs source/link review, not an invented runtime test.
Keep **source inspection**, **synthetic test**, **installed-package test** and **physical-device observation** separate.
An emulator's ABI and decoder are part of the result; software decoding does not qualify a physical hardware decoder.
Record **proposed / implemented / tested / packaged / published / accepted upstream** independently.
An outreach invitation establishes none of the later states.
Use actual clock timestamps, retain failed attempts, and inspect representative captures before trusting automated image labels.
Reviewer checks should run without an AI account; document the same CLI or CI command available to the author.
Read the actual diff before writing its commit message: state the problem, reason and checked result, without inventing intent.
For KDE changes, apply [the development practices reference](../native-linux/references/kde-development-practices.md); advice from one talk is not a project-wide contribution policy.

## Handoff

```text
Task and source revision:
Status and changed paths:
Environment and commands:
Expected / observed result, including control:
Evidence paths and hashes:
Not tested / known limitations:
Next action and any remaining authorization:
```

Use [upstream-outreach](../upstream-outreach/SKILL.md): credit the owners, follow their style and current policy, make one concrete ask and disclose assistance honestly.
Name the actual contributing model in the project's required provenance trailer when known; do not invent a model identity.
Private correspondence and personal details stay out of source branches and distro packages.

## Shared resources

Use configured scratch paths and disk floors; historical values in a recipe are examples, not overrides of current storage policy.
Release build locks and CI reservations when work stops.
Keep test displays, PipeWire, D-Bus and credentials separate from a person's live session.
Keep process IDs for cleanup; broad process-name matching can stop another worker or the caller itself.
Preserve useful evidence before deleting rebuildable intermediates.

Extend the existing domain skill when a repeated failure teaches a reusable lesson.
Keep the operational rule in the skill, substantial conditional detail in a linked reference, and individual run history in its evidence record.
