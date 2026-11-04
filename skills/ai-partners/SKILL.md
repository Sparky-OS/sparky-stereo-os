---
name: ai-partners
description: >-
  Coordinate human and AI contributions to Sparky Stereo OS with bounded tasks,
  source evidence, reproducible checks and durable handoffs, and keep unattended
  agent runners (Codex, Claude Code, local models) working when one stops without
  a tool call, loops or cannot write. Use with the edition contract and the domain
  skill; no particular model or service is required.
---

# Working together on the edition

Originally written by Claude from the project's work on 2026-10-10; revised with Daniel and Codex on 2026-10-19; unattended runners, reference corpora and `--find` added by Claude Opus 5.5 with Daniel on 2026-11-01.
People, hosted models and smaller local models use the same evidence and procedures.
Capability is established by the work and its checks, not by a provider name.

## Working recipe

1. Read the user's requested outcome, current authorization and [edition contract](../sparky-stereo/SKILL.md).
2. Read the shared project-memory index and relevant decision topics named in the brief, then find existing source and tests. Record the target revision and dirty files before editing.
3. Choose one bounded task and its owning layer. Read its domain skill; ask for missing facts only when they affect the next step.
   Before a web search, or writing an API, protocol, codec or specification fact from memory, consult the [local reference index](#reference-knowledge-local-first).
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
Memory: shared project index and relevant decision topics, with read access
Authority: requested actions; actions outside this task
Check: command/environment, observable expected result and relevant control
Return: changed paths, evidence location, actual result, gaps and next step
```

Do not dump an entire mailbox, research folder or skill catalogue into a model.
Use `tools/skills-context.py` from the public tree for a reader without filesystem access.
When the brief does not name the skill, `tools/skills-context.py --find "<task or symptom>"` (installed: `sparky-stereo-skills find`) ranks the skills offline by name, description and the index's task table; a small model can run it and then load only the first one's context.
The output records file hashes and refuses an oversized bundle instead of cutting instructions off.
For a long skill, select a heading with `--section skill-name:Heading`; include the sections needed for that step and retain the common contract.
A text bundle does not grant tool access or execute its commands.

When partners have filesystem access, give them read access to the same task-relevant decision memory used by the coordinator, regardless of model provider.
Name the index and relevant topics in the brief; a private coordinator summary alone is not enough when the underlying decisions are needed.
For a partner without file tools, include those selected decisions in its private task context.
Read them before reopening a settled design question or searching for an implementation already recorded there.
Memory records intent and prior evidence; check current source and versions before treating historical status as current.
If evidence conflicts with memory, report the precise conflict and preserve the user's latest decision.
Workers return corrections in their handoff; the coordinator maintains the shared record and promotes reusable technical rules into the appropriate public skill.
Access to decision memory does not imply access to credentials, private correspondence or unrelated personal records.

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
Work made for a person is delivered when that person can get it and run it alone: one obvious download (a normal release, not a pre-release), a guide in their language for their own system, the prompts they will meet and how to send results back.
A release nobody has downloaded has not landed.
Use actual clock timestamps, retain failed attempts, and inspect representative captures before trusting automated image labels.
Reviewer checks should run without an AI account; document the same CLI or CI command available to the author.
Read the actual diff before writing its commit message: state the problem, reason and checked result, without inventing intent.
For KDE changes, apply [the development practices reference](../native-linux/references/kde-development-practices.md); advice from one talk is not a project-wide contribution policy.

## Security habits for what an assistant writes

Added on 2026-11-04 from OpenSSF's guides, compared with what the edition already did.
They orient the work and gate nothing; no tool is banned because of them.
The sources are [Security-Focused Guide for AI Code Assistant Instructions](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions) (OpenSSF Best Practices and AI/ML Working Groups, 2025-08-01), cited as "the instructions guide", and [Securing Open Source in the Age of AI: A Practical Guide](https://openssf.org/resources/securing-open-source-in-the-age-of-ai-a-practical-guide/) (Chris Aniszczyk, Christopher "CRob" Robinson and David A. Wheeler, version 1.0, May 2026), cited as "the practical guide".

- **A dependency must exist before it is added.**
  The instructions guide, "Addressing Software Supply Chain Security", "Safe Dependency Selection": "Do not add dependencies that may be malicious or hallucinated."
  It reports a study in which 19.7% of the packages proposed by models did not exist, and names the attack that follows: an attacker registers the invented name.
  The practical guide, "Things to Watch Out For", gives the same warning: "consistently recommend imaginary dependencies (be sure to double check these)".
  So a package name an assistant proposes, in a `Depends`, a task list, a build script or a Dockerfile, is looked up before it is written down.
  For Debian, `apt-cache policy NAME` in a container with the edition's sources must show a candidate, from the origin you expect.
  For an upstream project, open its own release page and repository, and check that the name, the maintainers and the history match what you were told.
  Asking the assistant to list the names it is unsure of helps, and never replaces the lookup.
- **Versions come from the source, not from recall.**
  A model's idea of the newest release stops at its training date (practical guide, "Frozen in Time").
  Read the version from the archive or the release page, and write it down with the check.
- **Check what you download.**
  The instructions guide, "Integrity Verification": "include steps to verify integrity (like checksum verification or signature validation) if applicable."
  Fetch from the project's own address into a new, empty folder, record the SHA-256, and check the signature where the project publishes one.
  Pull container bases by digest, not by a tag that can move (the instructions guide, "Container and Deployment Considerations": "pin image versions using immutable digests").
- **Secrets stay out of everything an assistant writes.**
  The instructions guide, "Secure Coding Principles in AI Instructions": "Never include API keys, passwords, or secrets in code output, and use environment variables or secure vault references instead."
  A command reads a secret from the tool's own store at the moment it runs, and neither the command, the log, the report nor an error message carries the value.
- **Input from outside is data.**
  File names, archive members, fields of a repository index and command-line arguments reach our tools from places we do not control.
  Check them for the shape they must have, pass them to other programs as an argument list, never build a shell line or an `eval` from them (the instructions guide, "Python and Dynamic Languages": no `exec` or `eval` on user input, `subprocess` with `shell=False`).
  In a shell script, quote every expansion, stop on the first error, make temporary files with `mktemp`, and drop privileges when the work does not need them ("Operating System and Environment").
  An error says what failed, why and what to do, and leaves out secrets and private paths.
- **Review the work with a second look, then with the tools.**
  The instructions guide, "TL;DR": "ask it to review and improve its own work (repeating these steps as necessary)", the technique called Recursive Criticism and Improvement.
  The edition adds who looks: a partner from another lab reads the change cold, the language's linters and the packaging checker run (`shellcheck`, `lintian`, the project's own analysers), and the failing test is kept.
  A person decides, because the guide's first point is that the developer stays in full control and answers for the code.
- **Context does more than a persona.**
  The instructions guide does not recommend telling a model to act as an expert, because some experiments found it often makes the model "perform poorly or worse", and the practical guide, "As a Security Engineer... Prompting and Beyond", says a persona alone "is often not enough".
  A skill, the real source and a check that can fail carry the weight, as this folder's skills do.
  Keep an instruction file short and relevant: copied parts that do not apply make the assistant "generate extraneous or even incorrect code".

## Reference knowledge, local first

Daniel, 2026-10-23: consulting the local corpora is mandatory for the edition's own partners, and we recommend the same habit to every distro developer.
- **Keep the references local and searchable.** Index the specifications, manuals and sources the skills cite: CTA-861 and [HDMI®](https://www.hdmi.org/resource/brand), H.264 and H.265 annex D, RFC 9559 (Matroska), the Mesa, Qt, Wayland, Vulkan and OpenGL documentation, and the kernel's DRM documents. Use any vector store you like; ours is [Qdrant](https://qdrant.tech/), one collection per domain.
  [Reference corpora](references/reference-corpora.md) lists the public documents per domain (Debian packaging, the kernel's display stack, video and containers, graphics, Wine and Proton, virtual machines) with publisher, version, licence and URL, one working chunking and embedding setup, and the payload fields that make a hit citable.
- **Consult it first,** before a web search and before writing a fact from memory. A model's recall is the least reliable source in the chain.
- **A hit is a lead, not an authority.** Read its score, open the original and quote the clause: the specification section, the commit or the manual page. Never cite "the corpus".
- **Record what you consulted** in the handoff: the collections, the queries, and what was used or missing. A miss shows which document the index still needs.
- The index holds public references only. Private correspondence and credentials never go into it.

## Handoff

```text
Task and source revision:
Status and changed paths:
Environment and commands:
References consulted (collections, queries, used or missing):
Expected / observed result, including control:
Evidence paths and hashes:
Dependencies added or changed (name, source, version, how it was checked):
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
[Unattended agent runners](references/agent-runners.md) collects what was measured running partners without a person at the keyboard: a runner that stops after turns without a tool call, cannot write, will not stop or hands back to nobody, and the traps of a machine shared with a person's desktop.
Preserve useful evidence before deleting rebuildable intermediates.

Extend the existing domain skill when a repeated failure teaches a reusable lesson.
Keep the operational rule in the skill, substantial conditional detail in a linked reference, and individual run history in its evidence record.

HDMI®, HDMI® High-Definition Multimedia Interface and the HDMI® Logo are trademarks or registered trademarks of HDMI Licensing Administrator, Inc.
