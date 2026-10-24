---
name: contrib-handbrake
description: >-
  Contribute to HandBrake on GitHub with focused behavior changes, encoder output
  evidence and maintainer review replies. Load with upstream-outreach before a
  HandBrake pull request.
metadata:
  requires-packages: handbrake-cli
---

# Contributing to HandBrake

Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this is HandBrake's own practice.
Re-read the public contribution guide and the current pull-request template before proposing a change.

## Where
- Pull requests are https://github.com/HandBrake/HandBrake.
- Keep review, logs and follow-up in the pull request.
- Do not open private channels or use a private review path.

## The change
- Keep one behavior per pull request.
- Rebase on the public default branch before asking for another review.
- Separate fixes, release-note changes and packaging changes.
- Describe the symptom, the cause and the exact path that was exercised.

## Tests
- Follow the project's current build command for the relevant CLI or GUI target.
- Run the encoder path with a small input that reproduces the claim.
- Preserve the input layout and the output declaration in the evidence.
- State which encoder and platform were tested, and do not extend that claim.

## Public record
- Merged pull request [#8100](https://github.com/HandBrake/HandBrake/pull/8100) shows a direct review on GitHub.
- The review accepted a concrete encoder fix and requested the normal project evidence.

## Replies
- Disclose AI assistance once in the pull-request description.
- Answer each review point with the patched code, command or output that proves it.
- Keep the thread short, factual and polite.
