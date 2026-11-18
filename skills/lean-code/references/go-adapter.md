# The Go adapter: the plan, with the measurement that grounds it (not built yet)

**For** whoever builds the Go adapter for Lean Code or reviews a Go program built through it. Part of the [`lean-code`](../SKILL.md) skill.
Written on 2026-11-18 for toolkit 0.1.29 after OpenLinkHub 0.9.4 was carried (its Go files are left authored, named in the record). Status: **planned**; the rules are decided (the main session, milestone 7: doc comments go from the build input, directives and the cgo preamble stay, vendor trees are preserved as authored, no switch), the code is not written.

## How the Rust adapter was added (the pattern to follow)

`lean/lang_rust.py` (396 lines) holds the lexer, the rule per kind of comment and the reader checks; `consumers.py` names its extensions and the consumers that keep a file whole; `project.py` dispatches `render_text` by language and runs the check; `source_tree.py` adds the extension to `EXTENSIONS`, primes the batch check and reads the language plan (`debian/sparky-lean-languages.json` names `rust`); `lean/tests/test_rust.py` (382 lines) has one red case for each kind of data. The gate checks each file before it is written: the compiler's own lexer gives the authored and the lean text the same tokens, and a file the lexer refuses stays authored with the reason.

## The rules, one line for each kind of comment

| In the source | Rule |
| --- | --- |
| `// text` alone on its line | goes (the line stays empty: the position of every later line is kept) |
| `// text` after code | goes with the blanks before it |
| `/* */` without a newline | one space (a general comment acts like a space) |
| `/* */` with newlines | the same number of newlines (the Go spec: such a comment acts like a newline, so it takes part in automatic semicolon insertion) |
| doc comments (the group before a declaration) | go from the build input; the HR text keeps every one (option B) |
| `//go:build`, `// +build`, `//go:generate`, `//go:embed`, `//go:linkname`, `//go:noinline` and the other `//go:` pragmas, `//export NAME`, `//line`, `/*line */` | stay: the compiler, cgo or `go generate` reads them |
| the comment group directly before `import "C"` (the cgo preamble) | stays: it is C source for the C compiler (a later step may hand it to the C adapter) |
| `// Code generated ... DO NOT EDIT.`, copyright and SPDX lines | stay (tools read the marker; the licence obligation) |
| `// Output:` in an Example function of a `_test.go` file | stays: `go test` compares it; test files are left whole |
| a file with a `//go:generate` that reads source text (stringer and the like), an `embed`ded file, a file with a carriage return or a byte-order mark | left as authored, with the reason |
| strings, raw strings, runes, struct tags | data, never edited (`go/scanner` tells them apart) |

## How equivalence is proved

1. Before a file is written, a helper (a small Go program using `go/scanner`, built once with the installed `go`, one start for a batch of files) scans the authored and the lean text and compares the token streams, **including the semicolons the scanner inserts**; `go/parser` must still parse the lean text. A mismatch stops the projection; a file the scanner refuses stays authored.
2. After the build, `go build -trimpath` of the authored tree and of the projected tree give the same program. Measured with a throwaway projector that follows the table above: OpenLinkHub's 224 Go files outside `vendor/`, 10.37 MB (398,653 lines), hold 23,559 comments: 11,252 doc comments (647 KB), 12,296 other line comments (265 KB), 11 block comments (3 KB); 915,476 bytes (8.8 %) go, one comment group (the cgo preamble) stays, no file is refused, the token streams of all 224 are equal, `go vet ./...` is clean, and the two binaries (41,222,872 and 41,222,864 bytes) have byte-identical `.text`, `.rodata` and `.gopclntab`. They are identical because comment-only lines become empty lines; removing the lines would move later positions (panic traces, `log.Lshortfile`) and the report would list them as `position_lines` does for Rust.

## What it costs

About 250 lines of Python for the adapter, 120 of Go for the helper, a few lines in `consumers.py`, `project.py` and `source_tree.py`, and tests of about 300 lines (one red case per row of the table: a `//go:build` file that drops out of the build, a cgo preamble that no longer compiles, an Example whose output check is lost, a semicolon that disappears with a block comment). The projection of OpenLinkHub's 224 files took under five seconds including the helper's compile. Every package built through the toolkit has to be rebuilt after the toolkit changes (the embedded toolkit copies hold the whole `lean/`).
