---
name: ai-partners
description: >-
  How people and AI partners work together on the edition: a task brief that fits a small context, the hand-off format,
  evidence and status words (proposed, implemented, tested, packaged, published, accepted upstream), security habits (a
  dependency must exist, versions from the source, secrets never written, outside input is data), the local reference
  index consulted before the web, unattended agent runners (Codex, Claude Code, local models) that stop without a tool
  call, loop or cannot write, and how skills are kept as you go: the recipe first, each trap with its symptom, cause,
  fix and how the cause was found, a description written as a trigger clause so sparky-stereo-skills find, a local
  vector index or an MCP (consult_skills) routes a symptom to the skill. Load it to write or review a brief or a
  hand-back, to extend a skill after a piece of work, when find returns nothing for a symptom, when a subagent cannot
  write its report, or when a partner invents a path, a package name or a result.
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
Use `sparky-stereo-skills context` (from a checkout, `SPARKY_STEREO_REFERENCE=$PWD sparky-stereo-skills context`) for a reader without filesystem access.
When the brief does not name the skill, `sparky-stereo-skills find "<task or symptom>"` ranks the skills offline by name, description and the index's task table; a small model can run it and then load only the first one's context.
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

### Second-model review of new strings (nine languages)

Recipe, in this order:
1. Find the strings in the package's own files (`git log -p` on its `lang/` folder, a JSON catalogue, a generator table) and build the packet with a script, never by hand: one block per string, `### N. [KEY]`, a context line, the English, then every language's current text. Keep one packet per language family (CJK, European) so the reviewer's language list is short.
2. The context line says where the string appears (dialog label, drop-down choice, terminal prompt, message box), what each placeholder holds, which words are literal commands, and the glossary the batch shares (for example one rendering of "skill").
3. Send each packet to a model of another lab (routes in order: the Ollama cloud models; the Codex CLI on its ChatGPT login, `codex exec -m MODEL -s read-only --skip-git-repo-check -c model_reasoning_effort=high -C FOLDER "$(cat prompt.txt)" > answer.md 2>&1`, one call per packet, prompt text first and the packet appended, about two minutes each; ACIG's OpenAI route only when an account is configured) with the rules: report only real errors; per error the number and key, language, current text, corrected text, one-line reason; keep placeholders; do not polish style.
4. Keep every answer word for word; judge each finding as accept or reject with its reason and a precedent (a translated usage metavariable such as FILE is Debian and GNU practice; "download" is the ordinary pt_BR noun).
5. Ask the translator-facing questions too: which English words cannot be rendered well (an ambiguous noun, a placeholder with no description).

Traps:
- Symptom: every request returns HTTP 429. Cause: the Ollama cloud account reached its weekly usage limit (the body says so; the status code alone does not). Fix: record the exact body and stop that packet; a Claude model is not a second lab, so do not substitute one. Found by: `curl -i -X POST .../api/chat` with a one-word prompt.
- Symptom: "GPT limits are back" but ACIG's `ask_chatgpt` still fails. Cause: the ChatGPT login belongs to the Codex CLI, not to ACIG, which needs its own API account. Fix: use `codex exec` as above. The answer file keeps the banner and the reasoning log; the final answer is repeated after the line `tokens used`. Found by: the coordinator pointing to the route the GPT lanes use.
- Symptom: the OpenAI route answers "ACIG bootstrap pending" and lists no accounts. Cause: no account is configured in ACIG. Fix: record the error and stop; do not read ACIG's private configuration folder to repair it. Found by: `list_accounts`.
- Symptom: a reviewer's corrected string reads wrongly in its language (for example a translated placeholder followed by a word that turns it into a noun phrase). Cause: the model fixed the flagged spot without rereading the sentence. Fix: accept the finding, restate the sentence so the command comes after a colon, and keep the metavariable out of the grammar.
- Symptom: a packet's regex finds fewer strings than the language file holds. Cause: multi-line values (a `--help` block) end on a line that is not the closing quote. Fix: match from `LOCALn="` to the first `"` at a line end, with the dot matching newlines, and count items against the English file.

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

## Skills as you go

Daniel, 2026-11-06: "we register skills as we go to make the next work easier to tackle and by doing so, we do the hard consuming part once and keep enhancing as we go, each time better and better"; "the easier we make, the less energy other people and partners will spend".
A skill is written while the work happens, not reconstructed after it, and the skill folder is the one place the next person looks.

- **Every brief names the skill to leave behind,** and every hand-back has a "Skill changes" section: the branch and commit, and what each change saves the next worker.
  The skill is reviewed and merged with the work, in the same review.
- **Extend the skill that owns the part before creating a new one.** A new skill is for a new kind of work; a new trap in an old kind goes into the old skill.
  Keep the short working recipe first and the detail in `references/`; a skill's `SKILL.md` stays readable in one sitting.
- **What goes in, each time:**
  - the working recipe: the commands, in order, and the result to expect from each (the count, the exit status, the line the log prints);
  - each trap you hit: the symptom as it appeared (the exact error line or the wrong result), the cause, the fix, and how the cause was found (the log line, the tool or the command that showed it), so the next person can tell the same trap from a new one;
  - the part's own perks: a shortcut, a property or a tool that makes the next job easier;
  - a measured fact worth keeping, with its setup and date.
- **Public-safe always:** no machine paths, hosts, addresses, accounts, private plans or personal matters; generalise a fact about one machine ("on a host whose /tmp is a tmpfs") or leave it out and hand it to the coordinator's record.
  Say "Daniel", never "the owner"; one sentence per line; no dash in the middle of a sentence.
- **Never lose knowledge:** move detail into a reference, never delete a measured fact or a trap; correct what is wrong and say where the correction came from.
- **The lessons files:** each skill that gained more than a few lessons in a review keeps them in `references/lessons-2026-11.md` (or the next date), grouped as recipes, traps, perks and facts, each entry naming the lane it came from; shorter lists sit at the end of `SKILL.md` under "Lessons from the lanes".
  Read a skill's lessons before changing its part.

### The description routes, the body executes

A skill is found by its `description`, in the task table, through `sparky-stereo-skills find`, and through any local search or MCP that embeds the skills (ours is ACIG's `consult_skills` over Qdrant, one point per skill, name and description embedded, the file path in the payload, two tiers merged: a general collection and the project's).
So the description is written as a trigger clause, within 1024 characters:

1. what the skill is for, in one clause;
2. then the symptoms, error strings, programs and components that should bring a reader to it, as a person would type them ("Show Screen Contents says the process is not authorized to take a screenshot", "dpkg-stereo restore says original-mismatch");
3. then what it is not for, naming the skill that is, when two skills sit close.

Measured on 2026-11-06 with 157 real symptoms from the lane reports (one skill expected for each): the old one-line labels found the right skill first for 23 % of them and in the top three for 41 %; the trigger clauses found it first for 58 % and in the top three for 82 %, with the same index and embedding (sentence-transformers/all-MiniLM-L6-v2 through FastEmbed, 384 dimensions).
The misses that remain are symptoms whose words belong to a neighbouring skill (a Debian error routed to `contrib-debian` instead of `edition-packaging`), which is why the third clause names the neighbour.
Keep the test: `data/routing/symptoms-157.tsv` of the skills engine (sparky-os/skills-mcp in the build tree), which every change to the engine or to the descriptions is checked against for the offline finder, and a symptom list for the embedded index, and add the symptom of every new lesson to it.
The embedding model reads only the first 256 tokens of name plus description (FastEmbed's tokenizer truncates there), which is about 170 words of plain text and fewer when the words are technical names, each cut into several tokens.
On 2026-11-06 the seven longest descriptions had grown past that window and lost their closing symptoms until they were cut, so the words that route go early, and a description stays within the window, not only within 1024 characters.
Measure a description's tokens with the same tokenizer before trusting its tail.

### Finding a skill locally

The files are the source; every index is derived from them and rebuilt after a merge.
- In a checkout or on an installed system: `sparky-stereo-skills find "<symptom>"` (on a checkout, with `SPARKY_STEREO_REFERENCE=$PWD` in front) ranks the skills offline by name, description and the task table, the same every time, and prints each path with the `context` command to run next.
- With a local vector index: one point per skill, the name and description embedded, the path in the payload; the search returns the skill's name and path and the reader opens the file, never a copy of its body.
  Any vector store does; the index is rebuilt after every merge that changes a skill, and a skill removed from the folder is removed from the index.
- With a second local index of the bodies: one chunk per section of every `SKILL.md` and references file, the heading path embedded with the chunk, the file and the first and last line in the payload.
  It exists because a symptom's error string usually lives in a lessons file, which a description cannot hold; the search returns the skill, `file:first-last` and the heading path, and the reader opens those lines.
  A chunk is a whole section, or, when the section is over the model's 256-token window, whole paragraphs or list items; a numbered list, a table and a fenced code block are never split, because half a procedure (step 4 without steps 1 to 3, a command without the invariant that guards it) still looks actionable.
  A single item over the window stays whole, is embedded by its first 256 tokens and keeps its full text in the payload, so write the symptom first in every lesson.
  Measured on 2026-11-06 with the same 157 symptoms: descriptions alone first for 58 % and top three for 82 %; bodies alone 85 % and 95 %; both, a skill scored by the larger of its description score and 0.7 times its best chunk score, 75 % and 97 %.
  Of the 28 symptoms the descriptions missed, the bodies' chunk found the right skill in the top three for 26, and the chunk shown holds the lesson line for the error string.
  The symptom list was harvested from the same lane reports as the lessons, so the bodies' share is the best case; a symptom nobody wrote down is found only if a body says it.
  The indexing script also lists every skill whose name plus description is over the 256-token window and exits non-zero, so a description cannot silently lose its tail.
  Searching the bodies needs no new tool: the generic knowledge search includes the collection, and the finder prints both lists and the merged ranking.
- An MCP that serves the skills gives every partner (hosted, local, or a person's own tool) the same one call, "which skill answers this symptom", and the file to read.
  The Markdown files stay what people read; an MCP only routes to them.
  [Serving skills over MCP](references/skills-over-mcp.md) has the protocol eras a server must speak, the Skills extension, how each assistant registers a local server and where it reads skills, and what Debian ships.

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (13 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

HDMI®, HDMI® High-Definition Multimedia Interface and the HDMI® Logo are trademarks or registered trademarks of HDMI Licensing Administrator, Inc.
