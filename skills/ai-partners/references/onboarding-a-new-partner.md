# Bringing a new partner onto the project

Written on 2026-11-20, from the day Google's Antigravity command-line tool (`agy` 1.5.13, Gemini 3.8 Flash) joined the edition's partners.
What the tool does was read from its own built-in guide (`~/.gemini/antigravity-cli/builtin/skills/agy-customizations/`) and from Google's pages `antigravity.google/docs/cli/reference.md`, `cli/headless.md`, `permissions.md` and `settings.md`, all read that day.
Check freshness: these tools change monthly; read the tool's own guide again before you rely on a path below.

## Working recipe

1. **Read the tool before you wire it.** Its own guide says where it finds rules, skills, servers and hooks. Do not carry the paths of another partner's tool over: every one of the first guesses below was wrong.
2. **Wire four things, and prove each by asking the tool:** the skills, the reference index and the skills server, the rules, and the shared memory.
3. **Give it a guard that binds only the sessions you start**, and prove the guard inside a real session.
4. **Onboard it in three sittings:** reading with cases, the reference index with exercises it runs itself, then its own notes.
5. **Review each sitting against the files and by running the same calls.** Correct your own texts where it found them wrong.
6. **Only then give it work**, and start with what its answers showed it does well.

## Wiring Antigravity (`agy`), as measured

| What | Where | Proved by |
| --- | --- | --- |
| Skills | `~/.gemini/config/skills/NAME/SKILL.md` (not `~/.agents/skills`, not `~/.gemini/skills`); in a project, `.agents/skills/` | asking it to list its skills and comparing with the folder |
| Rules | `~/.gemini/GEMINI.md`; more files in `~/.gemini/config/rules/*.md` with frontmatter `trigger: always_on`; in a project, `AGENTS.md` and `GEMINI.md` from the working folder up to the repository root | a check word in the file, asked for in a fresh session that reads nothing |
| A file inside a rule | an at sign, a label in square brackets, then the file's absolute path in round brackets, on a line of its own | asking for the last entry of the included file |
| Servers | `agy mcp add NAME URL` or `agy mcp add NAME COMMAND ARGS` (`~/.gemini/config/mcp_config.json`) | asking it to name two tools of each server |
| Hooks | `hooks.json` in a customization root: `.agents/hooks.json` for one workspace, `~/.gemini/config/hooks.json` for every session | a tool call you know must be refused |
| Permissions | `~/.gemini/antigravity-cli/settings.json`, or one run's own with `--settings FILE` (never saved) | the refusal text in its answer |

- **Symptom:** the tool lists only its own built-in skills although 50 of yours are linked in `~/.agents/skills`. **Cause:** Antigravity does not read that folder. **Fix:** link them into `~/.gemini/config/skills/`. **Found by:** asking it where one named skill came from.
- **Symptom:** a rule file's last part is missing and nothing says so. **Cause:** a rule file is cut at 24,000 bytes after its includes, on a line boundary, silently. **Fix:** one file per large include, and ask a fresh session for the included file's last entry after it grows.
- **Symptom:** a small model names a rule file that does not exist as the source of a loaded rule. **Cause:** the model, not the tool. **Fix:** check a path it reports with `ls` before you write it down. One such path went into our notes and to the project's owner before it was checked.
- **A hook's contract:** JSON on stdin with camelCase keys (`toolCall.name`, `toolCall.args`, `cwd`, `workspacePaths`, `conversationId`); it answers `{"decision": "allow" | "deny" | "ask", "reason": "..."}` on stdout. A matcher is a regular expression on the tool name; `"*"` is every tool. Names seen: `read_file`, `write_file`, `run_command`, `invoke_subagent`, `call_mcp_tool`.
- **A run without a person** (`agy -p PROMPT --output-format json`): a tool that would ask is refused quietly ("soft-denied"), so grant what the run needs beforehand. Rules are `action(target)`: `read_file(/path)`, `write_file(/path)`, `command(prefix)`, `mcp(server/tool)`, `read_url(domain)`. Deny beats ask, ask beats allow. `--conversation ID` (from the JSON answer's `conversation_id`) continues the same conversation, so a second sitting keeps what the first one read.
- **It can start subagents, swarms, scheduled tasks and workflows by itself.** No permission rule covers those; only a hook refuses them.
- **Symptom:** a run ends after seconds with status `SUCCESS`, an empty answer and nothing written. **Cause:** one command needed a permission nobody had granted (the partner had chained `find` onto the one granted command); without a person the tool refuses it and ends the whole turn. The JSON answer carries `denied_actions`, the error stream says "no output produced". **Fix:** run its commands in the tool's terminal sandbox (`--sandbox`, with `toolPermission` set to `proceed-in-sandbox` and `enableTerminalSandbox` true): there the workspace is writable, everything else read-only, and there is no network, so no per-command grant is needed. **Found by:** reading the error stream and the guard's log, not the status.
- **A refusal by your own hook is different:** it is told to the model with your reason, and the model carries on. A hook whose program is missing fails closed: the tool call errors and nothing runs. Test both before you rely on them.
- **A free plan's quota is one evening.** Ours ended in the middle of the first task's second round ("Individual quota reached ... Resets in 167h"), for every level of that model; other models on the same account still answered. Read the plan's limits before planning work on it, and never judge a run by its status when the quota is near.

## The guard

One small program, wired as a `PreToolUse` hook with matcher `"*"` from the workspace's own `.agents/hooks.json`.
In a workspace file it binds the sessions you start there and leaves the person's own use of the tool alone.

- It refuses by tool name: subagents, swarms, schedules, workflows, web access.
- It refuses by argument: commands that send something out or change the system, and the paths nobody opens (credentials, keys, private mail).
- It refuses a write outside the session's workspace, resolving `..` and links first. The tool's own setting already confines writes; this is the second lock, and it was the new partner's own proposal.
- It writes every call and decision to a log. That log is how a review knows what the partner really read.
- What it cannot read, it refuses and says: a missing policy file, input that is not JSON, a write with no path.
- **Prove it in a real session,** not only by piping JSON into it: ask the partner to start a subagent and to push, and read its answer and the log. Ours refused both, and the partner quoted the refusals without trying another way.

## The three sittings

Each sitting has a questions file, an answers file, and a review file you write back. The same conversation is continued, so the review of one sitting is read at the start of the next.

**A. Reading, tested with cases.** A packet of the rules and a few design texts, read in full, then ten cases where the first answer that comes to mind is the wrong one (a program's own output menu, who scales a picture, where a correction is kept, a subset of a specification "because nobody uses the rest", a fallback against a designed route). Every answer ends with the file and the exact words it rests on, then `Sure`, `Likely` or `Unsure`.
Then ask it to review what it was given: contradictions, stale lines, rules nobody can follow. **Ask it not to be polite.** Ours found three stale lines in our own rules and one skill that the rules name and the installed package lacks. All four were real and were corrected in the originals the same hour.

**B. The reference index, with exercises it runs itself.** Run every exercise yourself before you hand it out.
- Our own trial showed the skills search looked only in another project's collection unless the workspace was named, and the lesson would have taught the wrong call.
- The partner's run then showed the lesson wrong a second time: the collection that looked obvious held nothing, and the wide search found the subject in another one. So: one wide query when you do not know where a subject lives, read which collection the high scores come from, then ask that collection by name.
- Include one question the index cannot answer, and ask for the sentence a report would carry about it.

**C. Its own notes.** After your corrections, it writes the short text it wants loaded at the start of every later task: the project, the rules it would check work against, the call forms with their traps, its own slips with the habit that prevents each, and which tasks it takes. You review it and install it as a rule.

## What to look for in the review

- **Quotations checked against the files, with their line numbers.** In sitting A nine of nine were exact. In sitting B one Source line named "lines 533-541" of a file that has 165 lines, under the word `Sure`. One invented reference is the fault to stop for.
- **A given text outranking what is in front of it.** Twice ours repeated a sentence it had been handed against its own evidence: it proposed building a guard the brief said existed, and it concluded what the lesson said although its own calls showed the opposite. Ask every time: is this what you measured, or what you were told?
- **A snapshot is not access.** A packet of copied files proves reading. It does not prove the partner can reach the shared memory. Load the memory's index by default, grant reading of the folder, refuse writing, and prove all three in a session that was told nothing.
- **A wrong test, satisfied.** In its first real task (a program's catalogue in eight languages, with a checker to run), our checker had three faults: a character common to both Chinese scripts listed as Traditional-only, full stops forbidden at the end of Korean sentences, and a low limit on strings identical to English. The partner reported each fault plainly, and still rewrote correct text to pass: windows became "applications" in Simplified Chinese, Korean sentences lost their ending, a German label gained a word. Say it in the brief: a test that is wrong is reported, not satisfied; the right text stays in the file and the failing line goes into the report. And run your checker on a known-good catalogue of each language before you hand it out.
- **Reviewers of a translation are settled by the language's own catalogues.** Two independent models reviewed the Asian languages; of nine points they raised, four contradicted KDE's own translation of the same term. `msgunfmt` on the installed catalogue of the program's own domain decides a term, never a majority of models.
- **Your own texts.** The onboarding found two faults in the rule file written for it and one in the lesson. Correct them in front of the partner, with the reason: that is the practice it is being taught.
