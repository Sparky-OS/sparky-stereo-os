# The Go adapter: what is projected, what is data, how to check a tree

**For** whoever builds a Go program through Lean Code or reviews such a build: the rule for each kind of comment, the counts that ground it, the commands, and the traps met while writing it.
Part of the [`lean-code`](../SKILL.md) skill.
Written on 2026-11-18 for toolkit 0.1.30 (`lean/lang_go.py`), measured on OpenLinkHub 0.9.4, the first program built through it (package `openlinkhub` 0.9.4-2).
The adapter acts on build inputs only, in a source tree whose language plan names `go`; an installed Go file stays authored.

## The rule, tied to the Go specification

- [Comments](https://go.dev/ref/spec#Comments): "A general comment containing no newlines acts like a space. Any other comment acts like a newline."
- [Semicolons](https://go.dev/ref/spec#Semicolons): a semicolon is inserted after a line's final token when it is an identifier, a literal, `break`, `continue`, `fallthrough`, `return`, `++`, `--`, `)`, `]` or `}`. A comment that acts like a newline takes part in that.

So the adapter differs from the C and Rust forms in one thing: **no line goes**.

| In the source | Rule |
| --- | --- |
| `// text` alone on its line | goes; the line stays, empty |
| `// text` after code | goes with the blanks before it |
| `/* */` without a newline | one space |
| `/* */` over several lines | goes line by line; its newlines stay, so the semicolon lands where it did |
| doc comments (the group before a declaration) | go from the build input; the HR text keeps every one (option B, decided in milestone 7) |
| `//go:build`, `// +build`, `//go:generate`, `//go:embed`, `//go:linkname`, `//go:noinline` and the other `//go:` pragmas, `//export NAME`, `//line`, `/*line */` | stay: the compiler, cgo or `go generate` reads them |
| the comment group directly before `import "C"` (no blank line between) | stays: it is C source for the C compiler |
| `// Code generated ... DO NOT EDIT.`, copyright, licence and SPDX lines | stay |
| strings, raw strings, rune literals (struct tags are strings) | data, never edited |
| a `_test.go` file | left whole: `go test` compares the `// Output:` comment of an Example |
| a file under `testdata/` | left: the input of a test |
| a file with a `//go:generate` line | left: a generator may read this file as text |
| a byte-order mark, a carriage return, binary data, a file go/scanner or go/parser refuses | left, with the reason |
| `vendor/*` | preserved through `debian/sparky-lean-preserve.json`, as for edgetk |

No pointer line is written (`MARKER` is empty): a pointer line would move every position. `core.render` takes a handler whose `keep_empty_after` has the attribute `keep_all`, which keeps every emptied line, the first one included; `project.render_text` calls it with `collapse_blank=False`.

## Recipe

Run it where the build's own `go` is installed: the check uses that toolchain's scanner and parser.

1. Opt the source tree in: `echo '["c", "go"]' > debian/sparky-lean-languages.json` (`c` only when the tree has C files; a tree without the file is projected as C and C++ only).
2. Preserve what stays authored: `debian/sparky-lean-preserve.json` with `vendor/*` and its reason, in the form `lean.debian_prepare` writes.
3. Project: `PYTHONPATH=TOOLKIT python3 -m lean.source_tree project TREE` prints `Build-input Lean Code: N/M files projected` and writes `TREE/.sparky-lc/source.json`; the authored copies are under `.sparky-lc/authored/`. In a Debian build the toolkit does this before compilation (`stage: before compilation` in the record); `golang-go` must be a build dependency, because the helper is built with it (`apt-get build-dep` runs before `dpkg-buildpackage`).
4. Read the record: `languages`, each file's `status` (`projected`, `unchanged` or `left`) and `reason`, the `check` text.
5. Build; compare. `python3 -m lean.source_tree restore TREE` puts every authored file back and checks each hash.

## How a projection is checked

Each file is checked before it is written: a helper (a Go program built once per process with the installed `go`, `-buildvcs=false`, `GOFLAGS` emptied so a recipe's `-mod=vendor` does not reach it) scans both texts with `go/scanner` and prints the token stream, **the automatic semicolons included**, and `go/parser` must accept the text; the streams must be equal, and the number of lines too. A whole tree is read ahead in batches of 400 files, one helper start per batch. An authored file the scanner or parser refuses stays authored with that reason; a lean file that reads differently fails the projection, and the build stops.

## Measured on OpenLinkHub 0.9.4 (a08204cf), 2026-11-18

- The tree: 713 files the plan makes eligible; 224 Go files outside `vendor/` (10.37 MB, 398,653 lines) and one C header projected, 487 vendor files left as authored (preserved), none refused. The record: `Build-input Lean Code: 225/713 files projected in 13 s on 4 processors`.
- 23,263 comments go from the 224 Go files (959,620 bytes with the C header's); the cgo preamble in `src/audio` stays.
- The program built from the projected tree and the one built from the authored tree: every section is byte-identical (`.text` 18,570,332 bytes, `.rodata`, `.gopclntab` 9,027,055, `.data`, `.noptrdata`, `.go.buildinfo`) except the two build-id notes (`.note.go.buildid`, `.note.gnu.build-id`); 116 bytes of 33,425,136 differ, all in them. A panic names the same file and line in both, which `tests/test_go.py` shows on a small program.
- Same program in the systemd container and on `qemu64` as before.

## What a toolkit change obliges

A new toolkit version needs its row in `lean/identities.py` (the digest of the renderer files and every `lang_*.py` moves with the new module). Old rows stay valid, so no package is obliged to rebuild for the new label; a package rebuilds to gain the adapter (OpenLinkHub, edgetk when it is packaged). A package built under the new toolkit differs from one built under the old only in the renderer identity of its `lc1` manifest and what that moves (measured on sparky-stereo-hardware 0.1.32 and sparky-stereo-kernel-settings 20261116.2: rebuilt under 0.1.30, every file equal to the 0.1.29 build's but the one manifest, `usr/share/dpkg-stereo/lc/PACKAGE/all.json`, whose `renderer.identity` and `renderer.sha256` are the only fields that differ).

## Traps met

- **A `go.mod` of the recipe reaches the helper.** *Symptom:* `go build` of the helper fails with `-mod=vendor` or "cannot find main module". *Cause:* the recipe exports `GOFLAGS=-mod=vendor` and the helper's folder has no vendor tree. *Fix:* the helper's environment empties `GOFLAGS`, sets `GOPROXY=off`, `GOTOOLCHAIN=local`, its own `GOCACHE` and `GOPATH`.
- **`go build` outside a work tree asks for `-buildvcs=false`** (*Symptom:* "Use -buildvcs=false to disable VCS stamping" in a temporary folder inside a repository's reach). *Fix:* the helper is built with it.
- **A multi-line `/* */` replaced by one space changes the program.** *Symptom:* the scanner reads `a y` where it read `a ; y` and go/parser refuses the lean text. *Cause:* such a comment acts like a newline. *Fix:* a removable comment over lines becomes one span for each of its lines, so the newlines between them stay.
- **The first line of a file.** *Symptom:* a file that begins with a doc comment lost its first line, and every position moved by one. *Cause:* `core.render` kept an emptied line only after a line that continues (a backslash), and never at offset 0. *Fix:* the handler's `keep_empty_after.keep_all`.
- **`+ 1` on its own line is a statement.** *Symptom:* a test text with `x := a /* over\n two */ + 1` stops compiling with "+1 is not used", authored and lean alike. *Cause:* the comment's newline inserts a semicolon after `a`. *Fix:* test with the comment after an operator.
- **`textStart` is not in the file.** A comment about the neighbouring tool: `repo/cpu-baseline.py` reads the Go function names from `.gopclntab`, whose `textStart` is zero in the file; see cpu-level-packages.md.
- **An Example needs a name that exists.** *Symptom:* `ExampleA refers to unknown identifier: A` in a test of the `// Output:` rule. *Fix:* the test tree declares `func A()`.
- **Where cgo cannot build, say so.** On the workstation `runtime/cgo` failed to build (a MIPS assembler file reached gcc); the cgo case of `lean/tests/test_go.py` probes a trivial cgo build first and skips with that reason, and passes in the build container (go and gcc installed there): all 20 cases of `lean/tests/test_go.py` ran green in `gr108-base`.
