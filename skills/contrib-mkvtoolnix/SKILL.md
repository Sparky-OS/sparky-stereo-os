---
name: contrib-mkvtoolnix
description: >-
  Contribute to MKVToolNix on Codeberg through behavior tests, Matroska field evidence and maintainer-led review.
metadata:
  requires-packages: mkvtoolnix
---

# Contributing to MKVToolNix

Written on 2026-10-24 from MKVToolNix's README (`https://codeberg.org/mbunkus/mkvtoolnix/raw/branch/main/README.md`, read 2026-10-24) and public merge requests !6311 and !6312 (read 2026-10-24).
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is MKVToolNix's own practice.
Re-read the README, the active merge request and the repository's test tree before every round.

## Where
- A change is submitted as a merge request on `https://codeberg.org/mbunkus/mkvtoolnix`.
- The Git default branch named in the README is `main`.
- The development build is configured with `./autogen.sh` and `./configure`, then built and installed with `rake` and `rake install`.
- Build-system output is shown by adding `V=1` to `rake`; the README also names `drake` as a replacement when Ruby's parallel job handling misbehaves.

## Tests
- The README says MKVToolNix has "a lot of test cases in order to detect regressions as well as changes from expected program behavior".
- Unit tests use Google Test under `tests/unit` and run with `rake tests:run_unit`.
- The README says a later suite "targets the program behavior" through input files in the project's `tests` tree.
- Continuous integration builds all components and runs both the unit and test-file suites against every commit.
- For muxer evidence, record `mkvmerge` options and demonstrate the exact resulting EBML or bitstream field.
- Public MR !6311 added the AVC frame-packing SEI path while preserving a `StereoMode` element for existing stereo files.
- Public MR !6312 added the same HEVC behavior after AVC was settled, without reusing its commit messages.
- The maintainer asked for `ffmpeg -loglevel debug` output as concrete SEI evidence.
- The maintainer asked the contributor to extend `mkvmerge --list-extensions` to describe the new recognized bitstream type.
- The maintainer required upstream regression files before merging the AVC and HEVC work.
- In !6311, the maintainer accepted the approach but asked for comments describing the bitstream-detection rule for the two possible HEVC layouts, rather than a larger rewrite.
- !6312 was merged as the HEVC companion after !6311's AVC work, with a maintainer test run and no review objections.

## AI policy
- MKVToolNix's README states nothing about AI, AI assistance, LLMs, generated code or policy for either (checked 2026-10-24).
- On 2026-10-24, I checked `README.md`, `CONTRIBUTING.md` and `docs/` in the public tree; those files are absent.
- Do not add an AI mention to upstream prose unless a later project document introduces one.
