---
name: contrib-claude-code
description: >-
  Report to, extend and stay inside the terms of Anthropic's Claude Code: what the public repository holds (not the
  CLI's source), the licence, the routes Anthropic names (the /bug command, issue templates, the HackerOne form for
  security), where plugins and skills are submitted, and how our own changes are made as plugins, mods, hooks and
  skills in our own repository. Load it with upstream-outreach before an issue or a plugin for Claude Code, when someone
  wants to patch or repackage the CLI, use a subscription login in another harness, or point Claude Code at another
  provider's model.
---

# Contributing to Claude Code

**Check freshness first.**
Written on 2026-11-21 from the repositories read that day with the GitHub API, and from Anthropic's documentation and legal pages.
The legal sentences below were read through a fetch tool that summarises pages: read the live page again before quoting one to anybody.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is Claude Code's own practice.

## What the public repository is
- https://github.com/anthropics/claude-code is public, but it is not the CLI's source.
  It holds the changelog, examples (settings, gateway, device management), the issue templates, and the source of the seven mods that ship inside the binary (`mods/`: `sec-default`, `hipaa-default`, `privacy`, `telemetry`, `agents-md`, `diff`, `easel`).
- Its `LICENSE.md` is one sentence: "© Anthropic PBC. All rights reserved. Use is subject to Anthropic's Commercial Terms of Service."
  So there is nothing to fork and change: the code can be read, not relicensed, patched or redistributed.
- It has no contribution guide. Its README names the routes: "Use the `/bug` command to report issues directly within Claude Code, or file a GitHub issue."
- Issues use templates (`bug_report`, `feature_request`, `documentation`, `model_behavior`, `github_connection`); blank issues are off.
  The tracker had about 16,000 open issues that day: search it before filing.
- Security goes to the HackerOne form named in `SECURITY.md`, never to a public issue.

## Where plugins and skills go
- https://github.com/anthropics/claude-plugins-official (Apache-2.0): "Submit and manage your plugin at claude.ai/directory/manage. Do not open a pull request here: pull requests are not monitored".
- https://github.com/anthropics/skills (every skill Apache-2.0): its README states no contribution rule; not read further.
- A marketplace of our own needs no one's approval: the documentation defines it as "a repository or directory with a `.claude-plugin/marketplace.json` file that lists plugins and where to fetch each one".

## Our own changes: the supported ways
Everything we change in how Claude Code behaves is made with what it documents, in our own repository:
- settings, `CLAUDE.md` and memory, hooks, skills, subagents, MCP servers, output styles, the status line, workflows;
- a plugin: "a directory of skills, agents, hooks, MCP servers, or other components that Claude Code installs and loads as one unit";
- a mod: "a plugin that changes how Claude Code looks and behaves", made of JavaScript or TypeScript event handlers.
  The built-in ones are the worked examples: `claude --plugin-dir mods/diff` runs one from source, `claude plugin test mods/diff` runs its tests.
  "Mods aren't sandboxed": a mod runs with the person's permissions, so ours are reviewed like any program we ship.
- A harness of our own is built with the Agent SDK and an API key, never with a subscription login.

## The terms that bind
From https://code.claude.com/docs/en/legal-and-compliance and Anthropic's Commercial and Consumer Terms (read as said above):
- "The Claude Code binary must not be modified. Claude Code must be installed and run as published by Anthropic".
  We install it with Anthropic's own installer, at the person's choice; we do not mirror, patch or repackage it.
- No decompiling or reverse engineering of the service or the binary.
- The subscription login (OAuth) is for "ordinary use of Claude Code and other native Anthropic applications".
  Another harness uses "API key authentication through Claude Console or a supported cloud provider"; it never offers, stores or passes on a Claude.ai login.
- Anthropic "doesn't support routing Claude Code to non-Claude models through any gateway".
  Other providers' models run in their own official tools.
- Account logins and API keys are not shared with anyone else.

## A report that can be acted on
- One finding per issue, in the template that fits; a model's behaviour goes in `model_behavior`, not `bug_report`.
- The version (`claude --version`), the platform, the smallest steps that reproduce it, what was expected and what happened, the exact error line.
- No secret, no private path, no other person's name in the text or in an attached transcript.
- Say once that the text was written with Claude's help, as in every report of ours.
- The text goes to the person who signs it before it is filed.

## Traps
- **Symptom:** a plan to "fix it in the CLI" or to ship a patched build.
  **Cause:** the public repository looks like a project one can fork.
  **Fix:** the change is a plugin, a mod or a hook of ours, or an issue for Anthropic.
- **Symptom:** an open harness asks for the Claude.ai login to save API cost.
  **Fix:** refuse; it gets an API key or a cloud provider's credentials.
- **Symptom:** a pull request to `claude-plugins-official` waits unanswered.
  **Cause:** that repository says pull requests are not monitored.
  **Fix:** submit at claude.ai/directory/manage, or publish in our own marketplace.
