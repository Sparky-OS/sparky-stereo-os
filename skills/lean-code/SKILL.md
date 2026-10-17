---
name: lean-code
description: How Sparky Stereo OS ships text files in their machine form (Lean Code) - what is removed, what is always kept, how each format is checked, and how to verify, explain or undo a projected file with dpkg-stereo. Load it before changing a package's text payload, before reading an error that points into an installed script, unit or QML file, and before reviewing a Lean Code report.
---

# Lean Code on Sparky Stereo OS

**Check freshness first.**
Written on 2026-10-16, numbers of 2026-10-17 (dpkg-stereo 0.1.4).
If the edition's README or the pages it links say something different, they win and this skill is history.

## The idea in one paragraph

A program reads its scripts, settings, units, rules and QML at every start; their comments are written for people, and the machine skips them every time.
Sparky Stereo OS keeps the authored file as the authority (HR, human-readable) and installs its machine form (MR, machine-readable): the same file without the comments the machine never reads.
The paradigm is Daniel Campos Ramos's dual code, published in Knowledge3D ([DUAL_CODE.md](https://github.com/danielcamposramos/Knowledge3D/blob/main/docs/DUAL_CODE.md), [HR_MR_STANDARD.md](https://github.com/danielcamposramos/Knowledge3D/blob/main/docs/HR_MR_STANDARD.md), and for the W3C PM-KR Community Group [PM_KR_MR_HR_PARADIGM.md](https://github.com/danielcamposramos/Knowledge3D/blob/main/docs/W3C/PM_KR_MR_HR_PARADIGM.md), "Comments as Runtime Waste").
The renderer that makes the MR also gives the map from every MR line back to the authored line, so an error in an installed file is reported where a person can fix it.

## Who does it

- **Nobody by hand.** Contributors write and package code in its upstream style, comments included. Lean Code is a step of the edition's own pipeline.
- **The ISO**: the packer's pre-squashfs step projects the image's packages and records them in the image's `/var/lib/dpkg-stereo`.
- **Installed systems**: `dpkg-stereo`, after every dpkg run, projects what dpkg installed. The `.deb` files stay exactly as their distributions built them.

## What goes, what always stays

Removed: comments and the lines a removed comment leaves empty; runs of empty lines become one.
Never touched: anything a consumer reads.
- Interpreter lines (`#!`), encoding declarations (`# -*- coding`), editor modelines.
- Licence and copyright notices, SPDX lines.
- Directives that look like comments: Perl's `# line N`, JavaScript's `//#` and `//@`, `/*!` and `@license` blocks, Qt's translator comments (`//:`, `//=`, `//~`), GCC's fall-through comments.
- Data that looks like a comment: heredoc bodies, quoted strings, template literals, regular expressions, YAML block scalars, multi-line strings.
- Python docstrings (they are runtime data, `__doc__`) and Perl POD.
- Documentation, manuals, translations, licence files, JSON (it has no comments).
- Files that read their own text or line numbers (`$0`, `BASH_SOURCE`, `LINENO`, `inspect.getsource`, Perl's `__LINE__`), and conffiles a person has changed.

Each lean file keeps **one pointer line** at its top: where its full HR text is (`/usr/share/doc/<package>/hr/` plus the file's own path) and the page with the resolver.
A file whose comments are smaller than that line stays as it is.

## How each format is checked (every projection, before it is written)

| Format | Who decides that the lean file means the same |
| --- | --- |
| sh, bash | bash parses both as one function body; `declare -f` must print the same program (dash also runs `dash -n`) |
| Python | the same abstract syntax tree (`ast.dump`, positions excluded) |
| QML, JavaScript | acorn gives the same tokens with the same line breaks (semicolon insertion depends on them) |
| C, C++ | GCC: the same tokens and directives (`-fpreprocessed`), and the same full preprocessing where the file preprocesses on its own; `#line` keeps every authored line number, so `__LINE__`, `assert` and debug line tables do not move, and include guards keep GCC's read-once optimisation |
| systemd units and its configuration, udev rules, KConfig, desktop entries, tmpfiles, sysctl, kmod | each consumer's documented comment rule (whole lines only; none of these parsers has inline comments) |
| YAML, TOML | PyYAML composes the same node graph; tomllib reads the same document |
| Perl | B::Deparse prints the same program |

A failed check leaves the file as it is, and the manifest says why.
A file that comes back in bytes already checked (a reinstall, or a file an upgrade did not change) is rendered again and kept only if it gives the recorded lean bytes; anything else gets the full check.
dpkg-stereo's own files are never projected: the tool that undoes projections stays as it was built.

## dpkg-stereo, the commands

- `dpkg-stereo --status`: what is projected, by format, and why the rest is left alone. Records live per package in `/var/lib/dpkg-stereo/records/`, so a dpkg run reads only what it touched.
- `dpkg-stereo --verify [package]`: every projected file against its record; `--deep` checks every original against its `.deb` and dpkg's md5sums. `dpkg --verify` and debsums report projected files as changed; this is the check that knows why.
- `dpkg-stereo --resolve /path/to/file:LINE[:COL]`: an error location in a lean file, mapped to the authored line. (C and C++ need no mapping: their line numbers are the authored ones.)
- `dpkg-stereo --hr /path/to/file`: writes the full HR text to `/usr/share/doc/<package>/hr/<path>`. The HR copies of projected settings arrive by themselves with the first successful online update.
- `dpkg-stereo --restore [package]`: the way back (removing dpkg-stereo runs it for everything). Originals come from the pristine copies of conffiles and from each package's `.deb`, read once per package from APT's cache or the archive. When the installed version is no longer in either, its files stay lean and recorded, and the package is named: `apt-get install --reinstall <package>` brings them back. `--hold package|path`: never project it again.
- Conffiles: before dpkg runs, a projected conffile still in its lean form goes back to its pristine bytes, so dpkg never asks; a conffile you edited is yours, and dpkg's usual rules apply to it.

## Verifying a projected package by hand

1. `dpkg-stereo --verify <package>` prints no problem lines.
2. For a script: run it, or its own tests, with the lean file and with `dpkg-stereo --hr` output; the results must match.
3. For a unit or a rule: `systemd-analyze verify` and `udevadm verify` accept it.
4. For C and C++ headers: build something against them; the objects match the ones built against the authored headers (outside debug information, where a removed inline comment moves column numbers).

## What it gives, measured (beta 2, October 2026)

- The ISO: 10.09 MiB smaller, after paying for dpkg-stereo and its records; 20,363 files projected, 287 MB of them becoming 238 MB.
- A boot reads 142 KB less (420 lean files: udev rules, units, scripts, settings); four program starts read 50 KB less (mostly QML).
- Parse time per file falls by microseconds (on an AMD A10 laptop: udev rules 30-79 µs, shell scripts 16-29 µs, QML 8-16 µs), about 7 ms per boot.
- Compiled programs keep their machine code, checked byte for byte; compile times stay within the noise (GCC skips comments cheaply).
- An installed system's package files: 140 MB fewer on an AMD A10 laptop (55,442 files projected; records 24 MB).
- Program starts with an empty page cache: 1-5.5% faster on the A10 (plasmashell -5.5%, Dolphin -3.1%, Discover -2.3%, System Settings -0.9%; 22 of 32 pairs). Warm starts and boot to desktop move less than their spread.
- Session memory does not change: comments never reach memory.
- The cost: dpkg runs take longer while dpkg-stereo projects and checks what they installed (three big packages reinstalled: +1.8 s with 0.1.4), and the image carries 5.5 MB of records. The first projection of an existing big install takes time once (the A10 with 770,000 package files: about an hour on two cores); systems installed from the ISO start projected.
