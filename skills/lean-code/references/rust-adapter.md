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

## The compiler itself, measured on a small machine

**Preparation status, 2026-11-13:** source preparation has compiler-backed controls; the compiler build and hardware timings are separate acceptance steps.
This recipe accompanies `tools/rust-lean-experiment` in the distribution build tree; run its source-preparation driver with the pinned toolkit and compiler in a container.
Its recipe is `prepare.py AUTHORED OUTPUT`, then `verify.py AUTHORED OUTPUT`.
For Debian's pinned 1.99.1+dfsg1-1~exp1, pass `--checksum-baseline tools/rust-lean-experiment/debian-1.99.1-checksum-baseline.json` to preparation, as the driver's README specifies.
The complete source pass inventoried 70,016 Rust files: 31,233 passed the compiler lexer checks, and 38,783 stayed authored for recorded consumers, fixtures or carriage returns.
The independent verifier checked all file contents, modes and links against the manifests.
It leaves the authored source intact and makes B with the existing renderer and C with comment-form documentation removed where the consumer scan permits it.
The manifests bind file contents, modes and links; `source-report.json` names preserved inputs and C's crate exceptions.
The preparation compiler checks B's complete token listing, and checks C after excluding doc attributes on both sides.
Explicit doc attributes stay in the source.
This check establishes lexical scope only; keep `build_qualified` false until the fixed compiler build and its consumers pass.

Source-tree totals include fixtures the build never compiles.
Intersect the final manifests with actual build dep-info before calling a number "what the compiler reads".
The measurement kit must retain the source identities and preparation evidence, build each form with the same seed and configuration, and compare installed files and compiler workloads separately.
Full timing and unattended-runner qualification remain required before reporting results.

- Symptom: a source-preparation walker omits Rust code under a directory named `build`.
  Cause: the generic source walker excludes that name at every depth.
  Fix for the compiler experiment: inventory every Rust source independently, apply the same renderer and consumer checks, and list preserved fixtures explicitly.
  Found by: reading `source_tree.EXCLUDED`; a synthetic `src/build/unit.rs` control confirms projection and manifest coverage.
- Symptom: removing docs can change macro expansion although the remaining ordinary tokens match.
  Cause: the compiler's `rustc_macros::rustc_queries!` reads doc attributes and generates replacement documentation when they are absent.
  Fix: keep docs in its caller crate for C and record why; apply equivalent review to other documentation-consuming macros.
  Found by: source inspection of `compiler/rustc_macros/src/query.rs`, `doc_comments.is_empty()` and `doc_comment_from_desc`, and a preparation control that fails without the exception.
  This is a source-consumer finding, not a successful full compiler build.
- Symptom: a modified vendored source is accepted without proving which checksum it replaced.
  Cause: rewriting a Cargo manifest by its current files alone loses the old source identity.
  Fix: change only entries whose old and new digests match the projection ledger; reject a mismatching old digest and retain the authored manifests.
  Found by: the compiler experiment's checksum negative control and complete-tree corruption control.
- Symptom: preparation stops at `blake3` because the Cargo checksum does not name the authored `build.rs`.
  Cause: Debian's rustc 1.99.1+dfsg1-1~exp1 source already has ten Rust files changed by Debian patches while Cargo still records the upstream digests.
  Fix: establish a separate exact-tree baseline, require the old digest to match an applied quilt backup, and accept only the reviewed upstream-to-patched-to-projected hash chain.
  Keep the original metadata in A and count the reconciliation separately from removed source bytes.
  Another tree or an unreviewed hash pair must stop; Debian's later checksum-pruning build step does not replace the provenance check.
  Found by: the full-tree preparation's explicit checksum failure, then all ten discrepancies matched `.pc` backups of patches in `.pc/applied-patches`; negative controls reject an unreviewed replacement.

### Preparing the offline compiler experiment

After the lexical preparation, apply the same edition packaging and C/C++ pass to every form.
Keep the packaged `rust-src` authored: restore each staged Rust file only when it matches either its bound form or its authored original, and refuse any other content.
Seal the final tree after these changes, with a full file/mode/link manifest and an archive checksum.
C must pass a real stage-1 compiler/library/tool check before it can be called build-qualified.
Bootstrap paths differ by command: read `bootstrap check --help --verbose` before choosing targets; in 1.99.1 cargo and wasm-component-ld have build rules but no check rules, so qualify those with an explicit offline build.
Keep failed attempts and build-led documentation exceptions, restore a failing crate from the qualified B tree, and bind its old/new Cargo hashes again in the clean final tree.

The runner recipe is in the build repository's `tools/rust-lean-experiment`.
Its one-command kit uses an immutable image, a fixed seed and offline crates, fresh targets, interleaved A/B rounds, and atomic whole-step receipts.
`./run.sh` starts or resumes; `./status.sh` reads its state; `./pause.sh` requests a pause after the current step.
A receipt binds the kit version, plan, source identity, result hashes and machine state.
An interrupted step is not a result, and a finished result is checked before it is skipped.
Measure a local sample under the preparation CPU limit and state the hardware scaling assumption and uncertainty; a forecast is not a measurement on the small machine.
Keep final compilers from whole builds even when the repeated subject must be smaller to fit the time budget.
See [a long unattended measurement on a laptop](../../test-bench/references/unattended-laptop.md) for the runner controls and their qualification.

- Symptom: C's bootstrap fails in syn's punctuation/delimiter macro invocations although ordinary token equality passed.
  Cause: `syn` 2.0.118 matches documentation attributes in `define_punctuation_structs!`, `define_punctuation!` and `define_delimiters!`.
  Fix: retain that crate's documentation by restoring exact B bytes and list the build error as its reason.
  Found by: the real offline C bootstrap's three macro matching errors in `vendor/syn-2.0.118/src/token.rs`; 38 changed Rust files needed B restoration.
- Symptom: the native census assertion expects seven projected files and rejects the prepared overlay.
  Cause: eight LLVM-wrapper/header inputs have three consumer outcomes, not one: five project, two structured-doc consumers stay authored, and Linker.cpp has no removable comments.
  Fix: bind the complete census and its reasons rather than asserting a guessed projected count.
  Found by: the source pass's report and its explicit failed assertion, then the same verified result for A, B and C.
- Symptom: perf reports nonzero hardware instructions but zero synthetic duration_time/user_time/system_time events.
  Cause: those synthetic counters in the preparation container do not supply usable timing; their presence does not establish a valid measurement.
  Fix: choose the documented plain perf summary for elapsed/user/system time, preserve its raw output and reject absent/zero elapsed time or instructions.
  Found by: an actual perf probe compared with the plain summary; the collector also accepts decimal commas and points and rejects ambiguous grouped numbers.

The completed preparation qualification built C's first full compiler stage, standard library and every named tool with the edition recipe's environment. This establishes the prepared C exception list for that stage, not successful final stage-2 packages or laptop performance. The kit's small container dry run is a separate claim. Restore authored Cargo checksum manifests alongside authored rust-src; verify existing authored entries, and list Debian's removed/regenerated WIT artifacts separately rather than inventing replacement upstream digests.

- Symptom: later C tools fail after the compiler itself built.
  Cause: syn 3.0.3 also matches doc attributes; icu_properties 2.2.0's property macros require them.
  Fix: restore the failing crates' exact B inputs and their bound checksum chain in a clean C tree.
  Found by: actual rust-analyzer dependency errors (three syn macro failures) and Cargo's ICU dependency errors (70 macro failures); the complete stage-1 tool build then passed with 38 and 12 retained files respectively.
- Symptom: direct bootstrap builds fail in libssh2-sys despite installed system libraries.
  Cause: bypassing Debian's make target loses LIBSSH2_SYS_USE_PKG_CONFIG=1 and other recipe environment.
  Fix: invoke the recipe's build target with a reviewed RUSTBUILD_FLAGS target list; retain the recipe environment for repeated stages too.
  Found by: the explicit failure and comparison with debian/rules, followed by a successful complete stage-1 tool build.
- Symptom: a sealed form changes when the recipe regenerates WIT Rust files.
  Cause: Debian creates two Rust literals outside build/, after source preparation.
  Fix: capture the original producer here, project and lexer-check its literals, bind form-specific assets and copy them only after verifying the original native regeneration. Restore their authored bytes in rust-src. Refuse any unexpected generator, version, path or output hash.
  Found by: the recipe's actual generation, an independent rustc lexer comparison, and A/B/C regeneration/restoration controls. Native outputs remain the original recipe's outputs.
- Symptom: the panic resolver refuses stdio.rs as an unknown interpreter.
  Cause: generic consumer discovery reads its first-line Rust #![attribute] as a shebang.
  Fix for the experiment: select the unchanged Rust lexer explicitly for the already manifest-bound .rs input, then use the existing content resolver. Do not change the shipped adapter implicitly.
  Found by: an actual C std panic at lean line 1144; the explicit Rust selection resolves it to authored line 1168. The small fixture includes the same first-line syntax.

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

## A whole suite through the adapter (2026-11-13)

Three applications with every vendored crate (48,463 C-family and Rust files in the source tree), projected in the package build of `craft-suite` by toolkit 0.1.29 with `["c", "rust"]`.

- **Projected:** 26,261 files; 14,810 had no removable comment; the rest stayed as authored with a reason: files read as data by `include_bytes!` and `include_str!` (about 2,100), carriage returns (516), crates whose build script reads Rust source (331), inner attributes on the first line that the reader takes for an interpreter line (3,345 in the 25 most frequent reasons, see the trap below), and the font and catalogue repositories' own tools (preserved by plan: not compiled).
- **What the compiler read**, from its dep-info: 13,660 files, 8,205 of them projected; 309,373,328 bytes and 6,889,873 lines authored, 298,282,892 bytes and 6,721,945 lines lean: 3.58 % fewer bytes, 2.44 % fewer lines.
  Of those bytes 51.3 MB are fonts and data read through `include_bytes!`, which no projection touches.
- **Vendored checksums:** 1,154 `.cargo-checksum.json` manifests were bound to the projection report before cargo ran, each changed entry proved by the report's hash before and after; the manifests are found at any depth, because the suite keeps one vendor folder per source.
- **The time:** about 15 minutes of a 48-minute build on four CPUs, one check per file; the same projection alone on one CPU took 902 s.
- **The programs' work:** the files the command-line programs write equal the static, authored build's, byte for byte.
- **Four interleaved builds** of the three-app workspace (authored, lean, authored, lean; one cargo run each from an empty target, four CPUs, every round on a machine other work was loading, load average 6 to 29), `perf stat` user-space instructions:

  | Round | Instructions | Wall | User CPU | Memory peak of the build |
  | --- | --- | --- | --- | --- |
  | authored 1 | 23,260,286,116,700 | 2,340 s | 7,629 s | 13.2 GB |
  | lean 1 | 23,259,246,093,679 | 2,936 s | 8,470 s | 12.7 GB |
  | authored 2 | 23,259,047,457,558 | 2,806 s | 8,502 s | 15.2 GB |
  | lean 2 | 23,259,782,785,843 | 2,781 s | 8,602 s | 12.7 GB |

  The first lean build ran 1,040 million instructions fewer than the authored one before it (0.0045 %), the second 735 million more than its pair (0.0032 %); the two authored builds differ by 1,239 million.
  So on the whole suite the projection shows no difference in instructions: the means differ by 152 million (0.00065 %), less than two builds of one form differ.
  Time and memory followed the machine's load, not the form.
  Two authored builds gave byte-identical stripped files, two lean builds too; between the forms all ten files differ and every size is equal.

Traps:

- Symptom: the projection stops on a vendored C header with `check failed: clang unavailable: the c token and directive stream needs its raw lexer`.
  Cause: an assembler header (`aws-lc-sys`, s2n-bignum's `_internal_s2n_bignum_arm.h`) is checked with clang's raw lexer, and the build container had no clang.
  Fix: `lean.debian_prepare --build-dependency clang`.
  Found by: the message; it came after 13 minutes, so run the projection alone on the unpacked source before the first full build (`python3 -m lean.source_tree project TREE`, then the checksum step).
- Symptom: more than 3,300 Rust files are left with the reason `interpreter [allow(unused_imports)]: no qualified adapter` (or `[cfg(feature`, `[no_std]`, `[warn(rust_2018_idioms)]`).
  Cause: a file that starts with an inner attribute `#![...]` is taken for a file with an interpreter line by the reader that runs before the Rust adapter, although the Rust reference says a shebang is `#!` not followed by `[`.
  Fix: not made in this round; those files stay authored, which is safe and costs part of the saving.
  The next change to the toolkit is to let the Rust adapter decide for `.rs` files, with the red case a crate root that opens with `#![no_std]`.
  Found by: counting the report's `left` rows by reason.
- Symptom: a patch for the generated workspace applies to the authored tree and fails on the lean one.
  Cause: its context lines hold a plain comment.
  Fix: change whole lines by content, never by context (the suite's `suite-fixups.json`).

## What it is not

- Not for installed files: Debian's `librust-*-dev` packages and `rust-src` are read by cargo, which checks each file against `.cargo-checksum.json`, and by rust-analyzer; `consumers.choose` leaves them with that reason.
- Not a formatter: nothing but comments and the blanks before them changes.
- Doc comments are the larger share of what a Rust tree carries for people, and they stay.
  Removing them where no macro and no lint reads them needs a consumer check that sees macro expansion; that is the next lever, not part of this adapter.
