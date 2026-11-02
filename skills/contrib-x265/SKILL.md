---
name: contrib-x265
description: >-
  Contribute to x265 on GitHub with CLA-signed patches, bit-depth builds, TestBench, bitstream bytes and public review evidence.
metadata:
  requires-packages: x265
---

# Contributing to x265

Written on 2026-10-24 from x265's `CONTRIBUTING.md` (`https://raw.githubusercontent.com/Multicorewareinc/x265/master/CONTRIBUTING.md`, read 2026-10-24) and public pull requests #986 and #999 (read 2026-10-24).
The rules that come first were added on 2026-11-02 from `CONTRIBUTING.md` and the repository's files on master, read that day.
Load [`upstream-outreach`](../upstream-outreach/SKILL.md) first; this skill is x265's own practice.
Re-read `CONTRIBUTING.md`, `.clang-format` and the active pull request before every round.

## The rules that come first
- **x265 publishes no code of conduct:** no such file in the repository and none named in `CONTRIBUTING.md` (checked 2026-11-02).
  Its development list runs on VideoLAN's mailing-list server, where VideoLAN's rules for its lists apply ([`contrib-vlc`](../contrib-vlc/SKILL.md#the-rules-that-come-first)).
  Elsewhere the same manners hold: respectful, concise, in the project's own venue.
- **The route:** the signed Contributor License Agreement first, then a GitHub pull request against `master` or patches on the development list (below).
  Bugs reproduce on the tip of `master` first; a memory-safety issue is reported privately, as `SECURITY.md` says, never as a public issue.
- **AI:** `CONTRIBUTING.md` has no rule on AI assistance, AI-generated or machine-generated code (checked 2026-10-24 and 2026-11-02).
  The nearest clause is its provenance rule ("Legal / licensing"): contributions must be "your own work (or work you are authorized to submit)", licensable under both the GPL v2 and the commercial licence, and "Do not paste code from GPL-incompatible or unknown-provenance sources."

## Where
- Pull requests are on `https://github.com/Multicorewareinc/x265`.
- The contributor guide also accepts mailing-list patches to `x265-devel@videolan.org`, flagged with the target branch in the subject.
- A change submitted on GitHub targets `master`.
- Because x265 has GNU GPL v2 and commercial distributions, every contributor must sign a Contributor License Agreement before a patch can be accepted.

## The change
- The contributor guide says a GitHub pull request must remain "focused on a single logical change".
- It says to keep the change current master and not to fold unrelated cleanup into the same change.
- When a review reveals a master-only defect, that defect becomes its own pull request; in #986 the reviewer asked to split the `m_bs` reset fix into #988 because it "also affects master independently of frame packing".
- A new public API member requires documentation, parameter parsing, parameter-to-string output, CLI handling and help text, ReST documentation, a build-number bump and test coverage.
- The guide says the style is four-space indentation, Allman braces and a 120-column soft limit, captured in `.clang-format`.
- Run `git clang-format origin/master` so the Code Quality check sees only the lines you intended to change.
- Answer review by pushing follow-up commits; `CONTRIBUTING.md`: "the maintainers will squash if needed".

## Tests
- The guide says the patch must build in 8-bit, 10-bit, 12-bit and multilib configurations.
- It says `TestBench` must pass on every architecture your change affects.
- It says to run at least the smoke tests and the relevant `TestBench` primitives locally; CI then runs the CLI, regression and threading suites.
- For a bitstream field, compare the emitted bytes against an independent reader or writer; a decoded picture alone is not proof of the field.
- Pull request #986 added `--frame-packing` types 3, 4 and 5, with H.265 syntax D.2.16 and semantics D.3.16 compared byte for byte.
- Review of #986 produced fixes for type 5 under `--interlace` or `--field`, rejection for `--num-views 2`, the older `m_bs` split-out fix, `--frame-dup` frame accounting and repeated SEIs on `--intra-refresh` cycles.
- Pull request #999 supplied independent validation of a separate field-control change: 48 synthetic encodes, 24 top-field and 24 bottom-field indications, byte comparison against an FFmpeg-separated field input, and acceptance by both an independent SEI reader and FFmpeg's decoder.

## AI policy
- On 2026-10-24, `CONTRIBUTING.md`, `readme.rst`, `COPYING` and `doc/` in the public tree contained no AI policy; the rules above record the 2026-11-02 reading.
- In pull request #999, the validation scripts were disclosed as "prepared with Codex assistance" while the contributor reported and ran the checks.
- Do not invent a policy clause; follow the project's absence until it publishes one.
