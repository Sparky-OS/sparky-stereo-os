# Wiring the hooks into a tool

**For** anyone who wants these hooks to run in their own AI tool: what the wiring is for Claude Code, what Codex takes today, and what each other tool offers and lacks, from each tool's own documentation as read on 2026-11-12.

A hook here is a program: one event as JSON on stdin, one answer as JSON on stdout.
The logic never names a tool.
[`lib/hookkit.py`](lib/hookkit.py) holds one dialect per tool: the names of its events and tools going in, the shape of its answer going out.
Each hook's `wiring.json` says on which events and tools it wants to run, and [`install.py`](install.py) turns that into the tool's own settings.

## Claude Code

Wired and tested: [the hooks reference](https://code.claude.com/docs/en/hooks) says "Hooks are defined in JSON settings files", and a command hook "receives the event's JSON input on stdin and communicates results back through exit codes and stdout".

```sh
python3 hooks/install.py wire claude WORKSPACE                         # prints the "hooks" block
python3 hooks/install.py wire claude WORKSPACE --write FILE            # merges it into FILE, keeping a copy beside it
python3 hooks/install.py unwire FILE                                   # takes these hooks out again, and only these
```

`FILE` is one of the settings files the reference lists: `~/.claude/settings.json` for all your projects, `.claude/settings.json` for one project, `.claude/settings.local.json` for one project on one machine.
`--write` replaces this folder's earlier entries and touches no other entry of the file.

What the dialect uses, with the reference's words:
- **Events:** `SessionStart` (matcher `startup|resume|clear|compact`), `UserPromptSubmit`, `PreToolUse`, `PostToolUse`.
- **Refusing:** a `PreToolUse` hook returns `permissionDecision` `"deny"`; "`"deny"` prevents the tool call", and the reason is "shown to Claude".
- **Asking the person:** `permissionDecision` `"ask"` "prompts the user to confirm".
- **Adding context:** `additionalContext`, capped at 10,000 characters; the kit cuts at 9,000 and says so.
- **Reading:** the `Read` tool, whose `file_path` is "always absolute"; a read with `offset` or `limit` is not a read in full.
- **Lanes:** "Hooks from settings files ... also run inside subagents", and the input then carries `agent_id`, which is how each lane gets a state of its own.
- **Telling the person:** `systemMessage`, the "Warning message shown to the user", which is how a hook that failed says so.

Two things to know:
- **A hook that cannot start does not stop anything.** "On most events, when a hook fails or times out, Claude Code still carries out the action. A policy hook with a wrong path or a crashing script then lets everything through." The watch for it is the `<hook name> hook error` notice on the first run.
  Claude Code v2.1.295 and later take `"onFailure": "block"` on a handler; `install.py wire claude WORKSPACE --on-failure block` writes it for a workspace that prefers a refused call to an unchecked one.
  The scripts themselves always exit 0, so this only changes what happens when Python or the script's path is missing, or the timeout passes.
- **A file named with `@` in a prompt is not a tool call.** "By default, files you reference with `@` in your prompt are added without any tool call", so no hook sees that read.

Not proved by this work: a live Claude Code session running these scripts.
The tests pipe events shaped as the reference shows them and as a workstation's own hooks receive them.

## Codex

The dialect and the wiring are written from [Codex's hooks page](https://developers.openai.com/codex/hooks) and tested by piping events shaped as that page shows; they were not run under Codex.

```sh
python3 hooks/install.py wire codex WORKSPACE          # prints the content for ~/.codex/hooks.json or REPO/.codex/hooks.json
```

Codex reads hooks from `~/.codex/hooks.json`, `~/.codex/config.toml`, `<repo>/.codex/hooks.json` and `<repo>/.codex/config.toml`, and "Non-managed hooks must be reviewed and trusted before they run": open `/hooks` in its CLI once after wiring.

What is the same: the event names (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`), the JSON on stdin, `permissionDecision: "deny"` with its reason, and `additionalContext`.

What differs, and what the dialect does about it:
- **It cannot ask the person from a hook.** "`permissionDecision: "ask"` ... are parsed but not supported yet. Codex marks the hook run as failed, reports the error, and continues the tool call." So an "ask" becomes a refusal whose reason says why, or context only, as `ask_becomes` says in the hook's configuration.
- **It has no file-reading tool.** Shell commands "Match as `Bash`", and a file is read with a shell command. A plain `cat FILE...` with nothing after it counts as reading those files in full; `head`, a pipe or a redirection does not.
- **Edits are patches.** File edits go through `apply_patch`, which a matcher can also name `Edit` or `Write`, and "hook input still reports `tool_name: "apply_patch"`" with the patch in `tool_input.command`. The dialect takes the paths from the patch's `*** Add File:` and `*** Update File:` lines, and the patch text as the text written.
- **Hosted tools are not seen.** Its coverage table has "Hosted tools, such as `WebSearch`" with "No" for both events.
- **No hand-back tool.** The hand-back check runs on a final `REPORT.md` written whole; a report written through a patch is not checked.

Its own page says what a contributor should expect: "Treat tool hooks as a useful guardrail, not a complete enforcement boundary."

## Other tools

No dialect is written for these.
Each row says what the tool's own page offers, so that whoever writes the dialect knows where the differences are.

| Tool | Where hooks are set | Before a tool runs | What it lacks for these hooks |
| --- | --- | --- | --- |
| [Gemini CLI](https://geminicli.com/docs/hooks/) | `hooks` in `settings.json` (`.gemini/`, `~/.gemini/`, `/etc/gemini-cli/`); JSON on stdin, JSON on stdout | `BeforeTool`: "Set to `"deny"` (or `"block"`) to prevent the tool from executing", or exit code 2 | Other names (`BeforeTool`, `AfterTool`, `BeforeAgent`; tools `run_shell_command`, `read_file`, `write_file`, `replace`); no way to ask the person; no context before a tool, only after one, at a prompt or at session start; `SessionStart` has no compaction source and `PreCompress` "cannot block or modify the compression process"; timeouts are in milliseconds |
| [Cursor](https://cursor.com/docs/hooks) | `hooks.json` in `<project>/.cursor/` or `~/.cursor/` | `beforeShellExecution`, `beforeMCPExecution`, `beforeReadFile`, `preToolUse` answer `"permission": "allow"`, `"deny"` or `"ask"`; "Exit code `2` - Block the action" | Other event names and another answer shape |
| [GitHub Copilot CLI](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-hooks) | `.github/hooks/*.json` in a repository, `~/.copilot/hooks/*.json` for a person | `preToolUse` "can approve or deny tool executions" | Other event names (`sessionStart`, `userPromptSubmitted`, `preToolUse`, `postToolUse`); its page warns not to "assume that the same events, input, or output work unchanged across surfaces" |
| [goose](https://goose-docs.ai/docs/guides/context-engineering/hooks) | `hooks/hooks.json` inside a plugin folder, after the Open Plugins hooks specification; the payload is JSON on stdin | `PreToolUse` and `Stop` can block: exit code 2, or `{"decision":"block","reason":"..."}` on stdout | No way to ask the person; hooks live in a plugin, so the wiring is a small plugin; `on_failure` is `allow` unless set to `block` |
| [Cline](https://docs.cline.bot/sdk/plugins) | Functions in a plugin's `hooks` object (`beforeTool`, `afterTool`, `beforeRun`) | `beforeTool` returns "`skip` and `reason` to block the call" | Not a command on stdin: a plugin would have to start these scripts and pass their answer on |
| [OpenCode](https://opencode.ai/docs/plugins) | Plugins in TypeScript or JavaScript, under `.opencode/plugins/` or named in `opencode.json` | Not read in enough detail to say | Not a command on stdin: the same as Cline |

A dialect is small: a table of event and tool names and one function that writes the answer (see `DIALECTS` and `render` in [`lib/hookkit.py`](lib/hookkit.py), and the Codex one as the example of a tool that cannot ask).
It is finished when the hooks' tests pass with it and when it has run once inside the tool itself.

## git

The publish check also runs as two git hooks, for commits made by anyone, with or without an AI tool.
[githooks](https://git-scm.com/docs/githooks): "By default the hooks directory is `$GIT_DIR/hooks`, but that can be changed via the `core.hooksPath` configuration variable", and for `pre-commit`, "Exiting with a non-zero status from this script causes the `git commit` command to abort before creating a commit."

```sh
python3 hooks/install.py git REPOSITORY WORKSPACE      # prints the two git config commands; it runs nothing
```

`core.hooksPath` replaces the repository's own hooks folder, so a repository that already has hooks of its own calls [`publish-check/git/pre-commit`](publish-check/git/pre-commit) and [`commit-msg`](publish-check/git/commit-msg) from them instead.
