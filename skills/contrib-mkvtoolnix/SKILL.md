---
name: contrib-mkvtoolnix
description: >-
  Contribute to MKVToolNix on Codeberg with focused container or muxing changes
  and reproducible muxer evidence. Load with upstream-outreach before a merge
  request.
metadata:
  requires-packages: mkvtoolnix
---

# Contributing to MKVToolNix

Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this is MKVToolNix's own practice.
Re-read the project's public contribution guidance and the current merge request before the next round.

## Where
- Merge requests are on https://codeberg.org/mbunkus/mkvtoolnix.
- Public review on Codeberg is the conversation surface.
- One behavior belongs to one merge request.
- Do not use private mail for diagnosis or review.

## The change
- Rebase on the current default branch before a second review.
- Keep a muxer behavior and build-system cleanup separate.
- Describe the symptom, the cause and the exact muxer command that changed.
- Keep the input to the smallest file that proves the behavior.

## Tests
- Use the project's documented build and test commands.
- Record `mkvmerge` input options, the expected result and the changed output.
- Verify the resulting container field with a public Matroska inspection tool.
- Do not claim support for a codec path that was not exercised.

## Public record
- Merged request [!6311](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6311) shows the maintainer reviewing a direct muxer change.
- Follow-up request [!6312](https://codeberg.org/mbunkus/mkvtoolnix/pulls/6312) shows the project adding its own regression before merge.

## Replies
- Disclose AI assistance once in the merge-request description.
- Answer every review point with the command, file or line that proves it.
- Thank the reviewer for the specific work that improved the patch.
