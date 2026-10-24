---
name: contrib-handbrake
description: >-
  Contribute to HandBrake on GitHub with its issue-first template, AI disclosure
  rules and tested-platform declarations. Load with upstream-outreach before a
  HandBrake pull request.
metadata:
  requires-packages: handbrake-cli
---

# Contributing to HandBrake

Written on 2026-10-24 from HandBrake's own documents, read from the current tree and web.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is HandBrake's own practice.
Re-read `CONTRIBUTING.md` and `.github/PULL_REQUEST_TEMPLATE.md` in the current tree before every round.

## Where
- Pull requests are on https://github.com/HandBrake/HandBrake.
- The official contribution guide is https://handbrake.fr/docs/en/latest/contributing/contribute.html.

## The pull-request template
- The template demands an issue first: "Create an issue describing the change."
- It demands agreement before code: "Discuss the issue with the HandBrake team to ensure that the idea has been accepted." The template adds: "(An open enhancement request does not equal acceptance)."
- The template demands a "Tested on" checkbox for Windows, macOS or Ubuntu; the pull request must state which one.
- The guide says to introduce the proposal on one of its community channels first: "Failure to communicate what you are working on may lead to duplicated efforts or rejection of your contributions."

## AI policy
- The HandBrake contribution guide (`https://handbrake.fr/docs/en/latest/contributing/contribute.html` and `https://raw.githubusercontent.com/HandBrake/HandBrake/master/CONTRIBUTING.md`, read 2026-10-24) contains the clause: "contributions not meeting the project's goals or standards may be rejected".
- The same guide documents an AI disclosure rule; pull requests may be rejected for "Inappropriate use of AI".
- UI translations belong in HandBrake on Transifex; the guide forbids AI services to translate HandBrake.
- Disclose AI assistance in the pull request; the reviewer decides whether the result is accepted.

## Tests
- The template provides "Log file output (If relevant)" and "Screenshots (If relevant)" fields for project-specific evidence.
- Run the affected encoder path with a small input and preserve the input layout and output declaration.
- The template's log-file and screenshot sections exist for a reason; attach relevant evidence there.

## Public record
- Merged pull request [#8100](https://github.com/HandBrake/HandBrake/pull/8100), merged 2026-09-16, added an option so the x264 encoder writes the AVC frame-packing SEI from the input layout.
- The review in that pull request asked for the normal project evidence: the tested platform declaration and the log output.
