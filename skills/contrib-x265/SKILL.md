---
name: contrib-x265
description: >-
  Contribute to x265 on GitHub with one encoder behavior per pull request,
  measured encodes and bitstream proof. Load with upstream-outreach before a
  change.
metadata:
  requires-packages: x265
---

# Contributing to x265

Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this is x265's own practice.
Re-read the active pull request and project guidelines before the next round.

## Where
- Pull requests are https://github.com/Multicorewareinc/x265.
- GitHub review is the public conversation surface.
- One encoder behavior belongs to one pull request.
- Keep build-system corrections separate from encoder behavior.

## The change
- Rebase on the current source before a second review.
- State the option, the affected SEI or coding path and the measurable proof.
- Do not fold unrelated cleanup into a new option.
- Expect a reviewer to ask for a related defect as its own pull request when it affects the current branch.

## Tests
- Record the encoder command, options, input profile and output comparison.
- Demonstrate the bitstream field or header correction, not just the absence of a warning.
- For performance claims, use identical inputs and report the measured comparison.
- Use many short encodes and byte comparisons when the options interact with field coding.

## Public record
- Merged pull request [#986](https://github.com/Multicorewareinc/x265/pull/986) shows review through focused maintainer comments.
- Pull request [#999](https://github.com/Multicorewareinc/x265/pull/999) shows a review report becoming its own measured follow-up.

## Replies
- Disclose AI assistance once in the pull-request description.
- Give the exact command, profile, file or output that proves each answer.
- Preserve the project's measured, conservative tone.
