# The Rust adapter: what is projected, what is data, how to check a crate

**For** whoever builds a Rust program through Lean Code or reviews such a build: the rule for each kind of comment, the counts that ground it, the commands, and the traps met while writing it.

Part of the [`lean-code`](../SKILL.md) skill.
Written on 2026-11-12 for toolkit 0.1.29 (`lean/lang_rust.py`), measured on storytold's PhotoCraft 0.23.1 and LightCraft 0.21.1 built as one workspace.
The adapter acts on build inputs only, in a source tree whose language plan names `rust`; an installed Rust file stays as authored.

## The rule, tied to the Rust reference

- [Comments](https://doc.rust-lang.org/reference/comments.html): "Non-doc comments are interpreted as a form of whitespace."
- [Whitespace](https://doc.rust-lang.org/reference/whitespace.html): "A Rust program has identical meaning if each whitespace element is replaced with any other legal whitespace element, such as a single space character."

So the adapter follows the C form of toolkit 0.1.20:

- a line that holds only a comment goes completely;
- a comment after code goes with the blanks before it;
- a block comment with code after it on its line becomes one space, so two tokens never join;
- the authored empty lines stay, there is no line directive and no stored line map.

`dpkg-stereo --resolve` (the content resolver, `lean.locate`) finds a lean line in the authored text by its content.

## What is data, and what happens to it

| In the source | Why it is not a comment | Rule |
| --- | --- | --- |
| `///`, `//!`, `/** */`, `/*! */` | The reference: doc comments "are interpreted as a special syntax for doc attributes". rustdoc publishes them and runs their code blocks as tests, `#![deny(missing_docs)]` fails a build without them, and macros read them (a derive such as clap's builds `--help` from them). | Kept, byte for byte. `////`, `/**/` and `/***/` are plain comments by the reference's lexer and go. |
| A file named by `include_str!` or `include_bytes!` | Its bytes are the including program's data. | Left as authored, with the reason. A path the adapter cannot read as a literal (built with `concat!` or `env!`) keeps the including file's whole folder. |
| A crate whose build script reads Rust source text | A generator that reads comments is a consumer no compiler check sees (the Linux kernel's Kbuild cuts `rust/kernel/*.rs.S` at the comment `// Cut here.`). | The crate stays authored whole. The sign: the script opens files and names a source folder (`src`, `tests`, `examples`, `benches`) or a `.rs` file by a path, or calls `syn::parse_file`. A bare `"generated.rs"` written into `OUT_DIR` is not a source path. |
| A procedural macro that asks a span for `source_text()`, `local_file()` or `source_file()` | It reads its callers' files as text, and the adapter cannot list its callers. | The projection of the whole tree stops and names the crate, until `debian/sparky-lean-rust-readers.json` records its review (`{"crate folder": "what was reviewed"}`). |
| `line!()`, `column!()`, `Location::caller()`, `#[track_caller]`, every panic message, debug line tables | They carry the position of code, and positions move when lines go. | Projected. The values name lean lines, as `__LINE__` and `assert` do in C; the build's report (`position_lines` in `.sparky-lc/source.json`) names every file whose own code reads its position, and the resolver maps a lean line back. |
| Vendored crates' `.cargo-checksum.json` | cargo refuses a vendored crate whose file differs from its listed SHA-256. | The source archive keeps the original manifests; a disposable build updates only the entries whose old and new hashes match the projection report, and restores them on clean (the artcraft recipe's `cargo-checksums.py`). |
| Notices, SPDX lines, an interpreter line (`#!` not followed by `[`) | Licence obligations; the kernel reads the interpreter line. | Kept. |
| Strings, raw strings, byte and C strings, character literals | Data. `'a` is a lifetime, `'a'` a character: the lexer tells them apart as the reference does. | Never edited. |
| `// SAFETY:` and other comments that tools read (Clippy's `undocumented_unsafe_blocks`, `//@` and `//~` in test suites) | Read by a lint or a test harness, not by the compiler. | They go from the build input. Run Clippy and a test harness that reads annotations on the authored tree, never on the projection. |
| Carriage returns, cargo-script frontmatter, text that is not UTF-8 | No qualified reader. | Left as authored, with the reason. |

## Recipe

Run it where the build's own `rustc` is installed: the check uses that compiler's lexer.

1. Opt the source tree in: `echo '["c", "rust"]' > debian/sparky-lean-languages.json` (a tree without the file is projected as C and C++ only).
2. Project: `PYTHONPATH=TOOLKIT python3 -m lean.source_tree project TREE` prints `Build-input Lean Code: N/M files projected` and writes `TREE/.sparky-lc/source.json`.
   Each row has `status` (`projected`, `unchanged` or `left`) and `reason`; the authored copies are under `.sparky-lc/authored/`.
3. Read the report before building: the `left` rows and their reasons, and `position_lines`.
4. Build. Compare what the program writes with the authored build's files; they must be equal.
5. Restore: `python3 -m lean.source_tree restore TREE` puts every authored file back and checks each hash.

To see what the adapter would do to one file without writing anything:
`python3 -c "import sys; from lean import project; print(project.render_text(open(sys.argv[1]).read(), 'rust', None, None, None, pointer=False)[0])" FILE`.

## How a projection is checked

Each file is checked before it is written: `rustc`'s own lexer must give the authored text and the lean text the same tokens.
The helper is a procedural macro built once with the installed `rustc`; it hands each text to `proc_macro::TokenStream::from_str` and prints identifiers, punctuation with its spacing, literals and groups.
Doc comments arrive there as `#[doc = "..."]` attributes, so they are compared byte for byte.
A whole tree is read ahead in batches of 400 files, one compiler start per batch.
An authored file the lexer refuses stays as authored, with that reason; a lean file that reads differently fails the projection, and the build stops.

`lean/tests/test_rust.py` holds one red case for each kind of data above: a program whose `--help` text disappears when doc comments go, a `missing_docs` build that fails, a documentation test that is no longer run, an `include_str!` target whose length changes, a generator that counts comment lines, a macro that reads source text.
It also compiles a program in both forms and checks that `line!()` and the panic location name the lean lines, that the resolver maps them back, and that the machine code (`.text`) is identical while `.debug_line` differs.

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: `proc macro panicked` from the token helper on a file with an unterminated string.
  Cause: `TokenStream::from_str` answers some lexer errors with a panic instead of an `Err`.
  Fix: the helper catches the panic and reports the text as one the lexer does not accept; such a text also makes `rustc` exit non-zero, so the helper's own answer file decides, not the exit status.
  Found by: the test that feeds it `let s = "open;`.
- Symptom: every `include_str!` target is reported as "a computed path".
  Cause: the search for the macro ran on the text with its literals blanked and swallowed the blanked path with the trailing spaces.
  Fix: find the call in the blanked text, read the path from the authored text at the same offset.
  Found by: the count over a real graph, 2,649 computed paths out of 2,649.
- Symptom: nearly half of a workspace's files stay authored "because a build script reads Rust source text".
  Cause: the first rule took any build script that reads a file and mentions a `.rs` name; the scripts read locale files and write `generated.rs` into `OUT_DIR`.
  Fix: the rule above; it still catches `wasm-bindgen-shared`, whose build script hashes `src/lib.rs` and `src/tys.rs` into a schema version.
  Found by: reading the four build scripts the first rule had named.
- Symptom: `cargo vendor` stops with `found duplicate version of package ... vendored from two sources`.
  Cause: two apps pin two revisions of one git repository whose crates have the same version, and one vendor folder holds one copy of a name and version.
  Fix for a measurement: project the copies cargo keeps under `CARGO_HOME` (`registry/src`, `git/checkouts`), which carry no checksum files; for an offline source package, one folder per git revision, written by hand as `[source]` replacements.
  Found by: cargo's own message, which names both revisions.
- Symptom: files in a folder named `build` are neither projected nor listed.
  Cause: the source walker skips folders named `build`, `debian`, `.git`, `.pc` and `.sparky-lc` at any depth.
  Fix: none needed for a build's own output folder; a crate that keeps sources under `src/build/` stays authored there.
  Found by: reading the walker's list of skipped folder names.

## Measured on a two-app workspace (rustc 1.99.1, release build, four CPUs, a busy machine)

Counts over every Rust file of the 783 packages in the resolved graph (22,268 files, 367.8 MB, 9,787,209 lines), with [`scripts/rust-comment-census.py`](../scripts/rust-comment-census.py):

| What | Count |
| --- | --- |
| Comments removed | 355,836 (18.4 MB); the files become 337.8 MB and 9,309,350 lines: 8.1 % fewer bytes, 4.9 % fewer lines |
| Doc comments kept | 902,296 (41.4 MB, 911,938 lines): more than twice what is removed |
| Notices kept | 8,544 |
| `include_str!` and `include_bytes!` | 2,649 uses in 437 files; 97 of their targets are Rust files |
| `line!()` and `column!()` | 70 uses in 15 files; `#[track_caller]` 1,850; `Location::caller()` 25 |
| Panic sites (`panic!`, `unwrap`, `expect`, `assert*`, `unreachable!`) | 391,222 in 11,581 files |
| Files that set `deny(missing_docs)` or `forbid(missing_docs)` | 111 |
| Code fences in doc comments | 31,267 |
| Procedural-macro crates | 51, none asks a span for its source text |
| Crates with a build script | 91; 5 read source text by the rule and stay authored (222 files) |
| `// SAFETY:` comments removed | 5,911; `//~` annotations 333 |
| Files left: carriage returns 237, binary data 10, frontmatter 1 | |

What the compiler read, from its own dep-info (10,390 source files): 188.2 MB and 4,946,950 lines authored, 179.6 MB and 4,810,870 lines lean: 4.6 % fewer bytes, 2.8 % fewer lines.

Four interleaved builds, authored, lean, authored, lean, each from an empty target folder, counted with `perf stat` (user-space instructions of every process):

| Round | Instructions | Wall | User CPU |
| --- | --- | --- | --- |
| authored 1 | 18,736,528,818,155 | 1,901 s | 6,009 s |
| lean 1 | 18,736,057,172,068 | 1,748 s | 5,599 s |
| authored 2 | 18,736,027,196,008 | 1,814 s | 5,732 s |
| lean 2 | 18,735,549,342,931 | 1,884 s | 6,157 s |

Each lean build ran 472 and 478 million instructions fewer than the authored build before it: 0.0025 % of 18.7 trillion.
The two authored builds differ from each other by 502 million, so the saving is as large as the drift between two rounds and is seen only pair by pair.
Wall and CPU time moved more between rounds (the load average went from 5 to 14) than between forms; they show no difference.
Read it as it is: rustc's lexer skips comments at almost no cost, and almost all of a Rust build is type checking, code generation and linking.

The programs: every built file has the same size in both forms, two authored builds are byte-identical and so are two lean builds.
Between the forms the files differ where positions are stored: `.data.rel.ro` (panic locations), `.rodata`, the crate metadata section `.rustc` of the dynamic libraries, the build ID, and a few bytes of `.text` (2 to 8,130 per file); the differing bytes were not classified one by one.
The files the programs write (a PSD and a JPEG from a 4000x3000 picture) have the same SHA-256 in both forms.

## What it is not

- Not for installed files: Debian's `librust-*-dev` packages and `rust-src` are read by cargo, which checks each file against `.cargo-checksum.json`, and by rust-analyzer; `consumers.choose` leaves them with that reason.
- Not a formatter: nothing but comments and the blanks before them changes.
- Doc comments are the larger share of what a Rust tree carries for people, and they stay.
  Removing them where no macro and no lint reads them needs a consumer check that sees macro expansion; that is the next lever, not part of this adapter.
