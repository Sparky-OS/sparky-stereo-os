---
name: contrib-mkvtoolnix
description: >-
  Contribute to MKVToolNix on Codeberg through behavior tests, Matroska field evidence and maintainer-led review.
metadata:
  requires-packages: mkvtoolnix
---

# Contributing to MKVToolNix

Written on 2026-10-24 from MKVToolNix's README (`https://codeberg.org/mbunkus/mkvtoolnix/raw/branch/main/README.md`, read 2026-10-24) and public merge requests !6311 and !6312 (read 2026-10-24).
The rules that come first were added on 2026-11-02 from the README and `CODE_OF_CONDUCT.md` on `main` and from [Codeberg's Terms of Use](https://codeberg.org/Codeberg/org/src/branch/main/TermsOfUse.md), read that day.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is MKVToolNix's own practice.
Re-read the README, `CODE_OF_CONDUCT.md`, the active merge request and the repository's test tree before every round.

## The rules that come first
- **MKVToolNix's Code of Conduct** (`CODE_OF_CONDUCT.md`, the Contributor Covenant 1.4, in the tree since 2017-11-18).
  README section 5: "By participating in this project you agree to abide by its terms."
  Its standards: welcoming and inclusive language, respect for differing viewpoints, accepting constructive criticism gracefully, focusing on what is best for the community, empathy.
  Reports go to the project team at the address the file gives.
- **Codeberg's Terms of Use apply on the platform** (§ 2, "Rules"): no content that expresses hate or encourages violence, no harassment, doxxing or brigading among them (§ 2 (1) 6).
  § 2 (1) 7: "You must not share projects that mostly consist of code written by "generative AI"-tools (including services such as *Claude*, *OpenAI Codex*)."
  The edition's fork there carries MKVToolNix's own code with a few assisted changes; a project of the edition's own that mostly consists of assisted code is not hosted on Codeberg.
  § 2 (6) lets maintainers set stricter rules, "for example by adding an easily discoverable Code of Conduct as a file in the repository root", as MKVToolNix does.
- **The route:** merge requests on Codeberg (below).
  Bugs go to Codeberg's issues with the command line, the system and sample files where possible.
  A security issue goes privately by mail to the author, never as a Codeberg issue, because Codeberg has no private issues (README 3.2).
  Questions go to the MKVToolNix help forum, Doom9's MKVToolNix thread or `#matroska` on Libera, not to the issue tracker (README 3.3).
- **AI:** MKVToolNix states nothing about AI, AI assistance, LLMs, generated code or policy for either: not in its README (checked 2026-10-24 and 2026-11-02), not in `CODE_OF_CONDUCT.md`, and the tree has no `CONTRIBUTING.md` or `docs/` (2026-10-24, the same on 2026-11-02).
  The platform rule above is Codeberg's.
  Do not add an AI mention to upstream prose unless a later project document introduces one.
  - Its maintainer's own stance is in issue [#6278](https://codeberg.org/mbunkus/mkvtoolnix/issues/6278), "meta: AI Policy" (2026-07-08): Moritz Bunkus is "very skeptical about what LLMs can do" and does not use them, is "not fundamentally against their use", and needs no written policy yet.
  - The policy he would likely write: "you may use LLMs for assisting during coding, but you-the-human must understand all changes, their effect & be able to explain the reasoning behind why they're correct before submitting PRs", likely "no LLMs for documentation", and he "will outright close & ignore overly verbose & meandering issue requests".
  - He speaks of LLMs, not of AI in general: "AIs is an overly broad term that usually includes a lot of technologies that we've been using for decades".

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
