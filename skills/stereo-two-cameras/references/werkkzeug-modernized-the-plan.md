# werkkzeug, modernized: the plan

Written on 2026-11-10 (ORDER 514, milestone 1), by Claude Fable 5.2 with Daniel Campos Ramos.
It holds what Farbrausch's open tools are, what builds where, who already works on them, the plan for an editor on KDE Plasma where people and AI partners build procedural textures together, and, since milestone 2 (11 November 2026), the recipe and the traps of the editor's core: Stereo Werkkzeug, the part without a window.
Since milestone 3 (the same day) it also holds the maths the core carries inside, so that one procedure draws the same bytes with every C library and in WebAssembly, and the partners' server, which an AI partner reaches the open project through.
Since milestone 4 (the same day) it holds the editor's first light: a KDE program over the C interface, its parameter panel made from Farbrausch's table, a live picture drawn in a process of its own, the core's sentences in ten languages, and AI partners working in the open window.
Since milestone 5 (the same day) it holds building in the window: operators dragged onto the page with the core's connection rules shown while they are dragged, a preview that can be pinned and tiled, the two sides of a step side by side, a partner's change marked on the page, and a proof that sends real pointer and key events through the compositor.
Since milestone 6 (the same day) it holds the stereo preview: the three kinds of stereo project and where their values live in the file, the two eyes drawn by the core with the stereo texture module's own mapping, the preview's 3D area in a Qt Widgets dock, a stereo photograph as a project's source with its per-file corrections, and the proofs read from the compositor's own picture of both eyes.
Since milestone 7 (the same day) it holds the fitter as a tool in the window: the fitter behind one small program with five kinds of lines, its modern operators as classes of the core, a found procedure laid on a page, one fit for each eye of a stereo photograph, and the corrections to the stereo preview (3D from the start, no limit on a tool's depth, a picture with its depth map, JPS and MPO marks saved, a floated preview in 3D).
Since milestone 9 (12 November 2026) it holds the Text operator and fonts: FreeType and HarfBuzz compiled into a core that draws the same bytes on four targets, how a document names a font so that it draws on another machine, what the window says when a font is missing, glyphs as drawing seeds with a browser for them, and how an editor's own copy of a shared library's work is dropped for the library's call.
Later milestones grow this page into the editor's contributor skill.

**Check freshness first.**
Every count and date below was read on 2026-11-10 from `farbrausch/fr_public` at commit `8c8f82c2ae01` (9 April 2017, the tip of its default branch on that day) and from each project's own pages.
Read them again before relying on one.

## Working recipe: reconcile before you plan

1. Read the repository's own README and each directory's licence file. `fr_public` states its licences per project, and GitHub's licence field shows none.
2. List what a tree needs to build, from its own files: `find . -iname '*.sln' -o -iname '*.vcxproj' -o -iname 'CMakeLists.txt' -o -iname 'Makefile*'`, then `grep -c '__asm'` and `grep -c '_mm_'` on the files you mean to build.
3. Search for existing work in three places, in this order: the upstream repository's pull requests and issues (`GET /repos/OWNER/REPO/pulls?state=all&per_page=100`), repositories by name, and the established programs of the same kind.
4. Read the earlier work of this folder: [a procedure fitted to a bitmap](procedural-texture-from-a-bitmap.md) holds the operators as they build on Linux, the readers of the game's project file and the fitter.
5. Write the plan with one reason and one source per choice, and say what was not run.

## What `fr_public` holds

| Directory | What it is | Licence, as its own file states | What it needs to build |
|---|---|---|---|
| `werkkzeug3` | The editor and engine behind many Farbrausch demos, with .kkrieger's project files in `data/` | BSD 2-clause, Copyright 2002-2012 Dierk Ohlerich, Fabian Giesen, Thomas Mahlke, Christoph Muetze, Tammo Hinrichs, Bastian Zuehlke; `data/` is CC-BY 3.0 | Visual Studio 2010 and YASM; Win32, Direct3D 9, DirectInput and DirectSound in `_start.cpp`; its own GUI (`_gui.cpp`); 14 `__asm` blocks of MMX in `genbitmap.cpp` |
| `werkkzeug3_kkrieger` | The kkrieger branch, "not the actual kkrieger code" in the README's words | The same BSD text | Visual Studio projects of the older `.vcproj` form only |
| `werkkzeug3/w3texlib` | The texture generator as a library, used for fr-033 | BSD, with werkkzeug3 | An nmake Makefile for `cl` and `lib` |
| `altona_wz4` | The Altona framework and Werkkzeug4, "should actually be fully functional" | BSD 2-clause, the six names above and 49Games GmbH | Visual Studio 2008 or newer, the DirectX SDK, YASM, and `makeproject` to write the projects; a `Makefile.linux.boot` builds the console tools |
| `altona_wz4/wz4/wz4frlib/wz3_bitmap_code.cpp` | werkkzeug3's texture operators inside Werkkzeug4, 3,578 lines | BSD, with Altona | No `__asm`; 312 uses of SSE2 intrinsics; this is the file the earlier lanes build with g++ and with `zig c++` |
| `Altona2` | The framework's successor; "Werkkzeug5 is not yet released" | BSD 2-clause, Copyright 2012-2014 Dierk Ohlerich | Visual Studio 2012; it has Linux, Android, iOS and macOS system files and no editor |
| `ktg` | OpenKTG, a 2007 proposal for an open texture generator, 16 bits per channel with premultiplied alpha, "no nice editor for it" | Public domain, Fabian "ryg" Giesen | CMake; `gentexture.cpp` and `demo.cpp` compile to objects with g++ 16.2 unchanged |
| `genthree` | GenThree, used for Candytron | BSD 2-clause, Ohlerich, Giesen, Muetze, Hinrichs | Visual Studio |
| `kkrunchy`, `kkrunchy_k7` | Executable packers for Windows | Public domain, Fabian "ryg" Giesen | Visual Studio; not needed for an editor |
| `lekktor` | A tool that removes code a recorded run never reached | BSD 2-clause, Copyright 2004 Dierk Ohlerich, Fabian Giesen | Visual Studio; not needed for an editor |

The operators of Werkkzeug4 are declared in `.ops` files: one block per operator with its inputs, its shortcut and every parameter's name, type, range and default.
`wz3_bitmap_ops.ops` has 36 such blocks (a 37th, `Paste`, sits inside a comment).
werkkzeug3 keeps the same facts in C++, in the `WerkClasses[]` table of `werkops.cpp`: 218 classes of every kind (two more rows, `Lightmap` and `MapLight`, are commented out), each with an `Edit_*` function that lists its parameters.

The project file has two outer forms, and the repository's files hold four versions.
`kkrieger.k` and most files in `data/` start with the word `nova`; `theta_final.k`, `snowblind.k` and `kkrieger1467_chaos_r.k` start with the `<<<<` marker directly.
`werkkzeug3` writes version 14 and `werkkzeug3_kkrieger` writes version 13 (`sWriteBegin(data,sCID_WERKKZEUG,N)` in each tree's `werkkzeug.cpp`); the reader takes versions 1 to 14.
The repository holds 23 `.k` files, 18 of them distinct: versions 11 (one file), 12 (one), 13 and 14.

## Who already works on it

| Work | State, read on 2026-11-10 | Licence | What it gives |
|---|---|---|---|
| Pull requests [#105](https://github.com/farbrausch/fr_public/pull/105), [#106](https://github.com/farbrausch/fr_public/pull/106), [#107](https://github.com/farbrausch/fr_public/pull/107), [#108](https://github.com/farbrausch/fr_public/pull/108) to `fr_public`, by wxthss82 | Open since 20 August 2026, no review yet | Offered into the BSD tree | Werkkzeug4 outside MSVC: fixes for standard compilers and five bugs found on the way; an OpenGL 2 renderer that draws, through a translator from the shader dialect to GLSL 1.20; a native macOS editor and player; 61 new operators, 30 of them for textures, written to take a plain pixel buffer. Tested by its author on macOS only |
| [kebby/Werkkzeug4](https://github.com/kebby/Werkkzeug4), by Tammo "kb" Hinrichs | Last change December 2019 | BSD | Werkkzeug4 and Screens4 with a new project structure for Windows 10 and Visual Studio 2019 |
| [wzman/werkkzeug4CE](https://github.com/wzman/werkkzeug4CE) | Last change July 2014 | BSD | A community edition of Werkkzeug4 with new operators, for Windows and Direct3D 9; many of its author's changes are merged in `fr_public` |
| [Sanvirtus/KkriegerNet](https://github.com/Sanvirtus/KkriegerNet) | October 2026 | BSD 2-clause | .kkrieger and werkkzeug3's generators written again in C#, with an operator graph editor that saves `.k` files "byte for byte"; tested by its author on Windows only; its README says it was written with an AI model |
| [kznsq/kkrieger-web](https://github.com/kznsq/kkrieger-web), [MasonDye/kkrieger-wasm](https://github.com/MasonDye/kkrieger-wasm), [varrtto/kkrieger](https://github.com/varrtto/kkrieger) | September and October 2026 | BSD for the first; no licence file found in the other two | The whole game in a browser or on macOS; no editor and no texture interface |
| [steven-schronk/Kkrieger-Werkkzeug3](https://github.com/steven-schronk/Kkrieger-Werkkzeug3) | March 2023 | As `fr_public` | werkkzeug3 building with Visual Studio 2022, and documentation of the tool |
| Pull request [#92](https://github.com/farbrausch/fr_public/pull/92), by onitake | Open since July 2016 | Offered into the BSD tree | A CMake script and fixes so Altona2's console tools build on Linux |

Programs of the same kind that do not use werkkzeug's operators or files: [Material Maker](https://github.com/RodZill4/material-maker) (MIT, on the Godot engine, active), [TextureLab](https://github.com/njbrown/texturelab) (active; read its licence file before use) and [Imogen](https://github.com/CedricGuillemet/Imogen) (MIT, last change 2020).
They are where to look for how a modern texture editor behaves; none of them opens `kkrieger.k`.

## The plan in short

- **The operators stay Farbrausch's code, unchanged.** `wz3_bitmap_code.cpp` is built as a small library with a C interface; OpenKTG joins it as a second family. One source gives the native library and the WebAssembly module, and the two must draw the same pixels.
- **The document core is new and written in Zig:** werkkzeug's own model (pages, operators stacked in rows, an operator taking the ones right above it, `Store` and `Load` by name), the `.k` file read and written byte for byte in both forms and both versions, a text form for review, and one journal of edits.
- **The editor is a KDE program:** Qt 6 Widgets and KDE Frameworks for the window, the pages, the stacking canvas and the parameter panel, built from the operator tables above, in the edition's ten languages.
- **AI partners reach it through MCP:** a small stdio server lists the operators, reads and edits a graph, draws it, makes a comparison sheet to judge by eye and runs the fitter. Every edit of a partner is one step in the same journal as the person's, shown with the partner's name, and undone like any other.
- **The fitter becomes one of its tools:** pixels in, operators out, placed on a page as ordinary operators the person can go on editing.
- **Stereo is one declared surface:** the stereo procedure is drawn as full side by side, left eye first, each eye at the texture's own resolution, and declared once. The program's 3D options are enable 3D, render resolution per eye and a shortcut to Display Settings.
- **Our changes live in a fork of `fr_public` and are offered back** to Farbrausch; the open pull requests are carried with their author's credit where we build on them.

## The core (Stereo Werkkzeug): working recipe

The core is a folder, `stereo_werkkzeug`, in the edition's fork of `fr_public`: Zig for everything new, Farbrausch's `wz3_bitmap_code.cpp` compiled as it is, one C header for every front end.
"Stereo" marks the edition's work on a program whose origin is Farbrausch's, as in Stereo KWin; Farbrausch is credited wherever the name appears.

1. Build: `./build.sh OUT` (Zig 0.16). It makes the operator table from Farbrausch's sources, then `OUT/wz` (the command), `OUT/libstereo_werkkzeug.a` with `stereo_werkkzeug.h`, `OUT/capi_test`, `OUT/swz-mcp` (the partners' server), `OUT/libswz_front.a` with `stereo_werkkzeug_front.h` and `OUT/front_test` (the front library), and `OUT/swz-draw` (the drawing process of a live preview). `SWZ_TARGET=x86_64-linux-musl` makes static programs; `SWZ_TARGET=wasm32-wasi` makes `OUT/wz.wasm`, the command only.
2. Prove: `tests/run-all.sh OUT`. One line per step; expect "65 steps passed, 0 failed" (the C test of the interface has 386 checks since milestone 5, the front library's 259) (Python 3 is needed for the step that proves the partners' server; with `SWZ_SDK_PYTHON` naming a Python that has the `mcp` package, the server is also run under the official SDK's client, 119 checks; without it that step says it was not run). The steps that are controls pass when the check under them fails (a change made behind the journal's back, one flipped bit in one picture).
3. Look: `wz textures FILE.k` lists the named textures, `wz draw FILE.k NAME OUT.png --png` draws one, `wz text FILE.k --labels` prints the project for reading, `wz graph FILE.k NAME` prints one texture's operators as typed text.

What to expect on `werkkzeug3/data/kkrieger.k`: version 13, 217 pages, 29,347 operators, 854 named textures; 742 draw, 112 are refused by name because they hold a Text operator (drawn with Text handed on when asked, which the output says).

### The project file, byte for byte

`WerkDoc::Write` and `WerkDoc::Read` (`werkkzeug3/werkkzeug.cpp`) are the specification; `WerkkzeugApp::Write` adds the outer form (the word `nova`, the number 1, the document, then the nova player's document).
A reader that keeps every field writes the same bytes back. What that takes:

- **Let the file say its own layout.** Each operator stores its convention word: bits 0 to 7 are the count of parameter words, 12 to 15 the links, 16 to 18 the strings, 20 to 22 the spline names (four bits, 20 to 23, before version 12: the reader's own workaround). The reader never needs the class table to step through a file.
- **Keep what the reader skips:** the reserved words, the second word of every operator, the fourth header word, the 16 words of the demo's settings.
- **Keep padding as bytes.** A string is its length, then the bytes padded to whole words; `sWriteString` zeroes the padding, the binary objects' padding is whatever was in memory. Hold both as read.
- **The page's first word is derived:** the number of operators on the list the page shows (its own list or its scratch list). Write it from the operators, and keep the file's number only when it differs.
- **An event names its operator by the operator's place in the file.** Give every operator an id that never changes while the document is open, keep the id in the event, and turn it back into a place when writing; an operator that is gone writes -1, and undo brings both back.
- **Keep the tail:** whatever follows the document's `>>>>` (the nova player's document, 32 or 1,964 bytes in the repository's files).
- **Refuse by size before allocating:** a count or a string length that the rest of the file cannot hold is a refusal with a sentence, so a damaged file cannot ask for memory.

The text form (`wz text`) holds every field too, so text made from a file packs to the same bytes. Each parameter word says its own kind (`12` whole, `0.5` decimal with a point, `#aarrggbb` colour, `0x...` the word as it is), so the table is needed only to print, never to read back. A decimal is printed only when it reads back as the same word; otherwise the word is printed as it is.

### The operator table generator

`tools/gen_optable.zig` reads `werkkzeug3/werkops.cpp` and `wz3_bitmap_ops.ops` and writes one Zig file: 218 classes (name, id, what it makes, inputs, convention, column, shortcut, packing), 1,236 parameter lines from the `Edit_*` functions (label, word, kind, default, range, choices) and Werkkzeug4's 36 operators.
The parameter panel, the partner's operator list, the text form and a new operator's default parameters all come from it.

- Strip comments first, keeping strings; the tables have commented-out rows.
- Normalise line ends (CR LF and CR alone both occur) and treat the bytes as Latin-1.
- The table's numbers are C expressions (`COL_NEW|COL_WZT`, `'C'|sKEYQ_SHIFT`, `KK_MAXINPUT`): collect the `#define`s of the headers and evaluate; a name that cannot be resolved stops the generator.
- `TEXTSIZEX` and `TEXTSIZEY` read the editor's default texture size, `DefaultTexSize = 0x909` in `werkkzeug.cpp`; the generator checks that line is still there.
- `DefaultF2` and `DefaultF3` set the defaults of several words at once; several flag lines can share one word.

### Drawing with the unchanged operator file

`src/bridge.cpp` includes `wz3_bitmap_code.cpp` from the tree, and `shim/` stands in for Altona. The test compares the file's git blob with the published one.

- The shim declares the image, font and file classes that only never-called functions use; their definitions refuse by name.
- `sVERIFY` ends the operator with a sentence (a `longjmp` back into the bridge), never an abort.
- `CheckBitmap` starts with `sFatal(L"i hate CheckBitmap")` and then returns 0. In the shim `sFatal` is recorded and returns, so `Bitmap_Paste` and `Bitmap_Wavelet` work as published; the bridge refuses any operator after which an unexpected `sFatal` was recorded.
- Every answer is sized against a memory limit before it is made; the time limit is checked between operators, and `--apart` draws in a process of its own, where the limit also ends a running operator and a crash is said, not suffered.
- Which operator feeds which follows `WerkPage::Connect1` and `Connect2`: the row right above, overlapping sideways, on the page's shown list, ordered by column; a bypassed operator stands for its first input; a name used twice marks both operators, and a marked operator is not drawn. With these rules `kkrieger.k` has the same 854 drawable named textures the first reader counted.

### The journal

Every change is made inside a step with an author (a person or a partner, by name) and a label.
Undo and redo move operators and pages between the document and the journal without allocating, so neither can fail half way.
A partner's step is refused until the person has chosen how partners work: applied and shown, kept as a suggestion, or asked about each time (Daniel Campos Ramos, 11 November 2026: asked once, all three offered, the answer kept). In the two suggesting ways the step is recorded, taken back out of the document and held until the person takes or drops it.

## The maths, carried inside: working recipe

**Why.** Farbrausch's operators call four functions whose results the C standard leaves to the library: `sinf`, `cosf`, `powf` and `atan2f`. Libraries round a few values differently, so one procedure drew two pictures: six of the 854 textures of `kkrieger.k` differed between a glibc program and a musl or WebAssembly one. A procedure that is sent instead of a picture must draw the same bytes wherever it arrives, so the core carries one implementation and compiles it into every program.

**Which.** musl 1.2.6's four functions and the files they need (19 sources, `libm.h`, `fp_arch.h`), copied unchanged into `maths/musl/` with musl's `COPYRIGHT` (MIT; the files' own notices name Sun Microsystems and Arm Limited). Take them from the release archive and check it: `sha256sum` against the published digest, `gpg --verify` with musl's key in a throwaway `GNUPGHOME`. `maths/musl-1.2.6.sha256` lists every file, and `build.sh` stops when one differs.

**How it is wired.**

1. `maths/swzm_prefix.h` is forced in front of every musl file (`-include`): it reads the system headers first, then gives every function and table a name of the core's own (`#define sinf swzm_sinf`, and every name `libm.h` declares as hidden).
2. `shim/base/types.hpp` calls only `swzm_sinf`, `swzm_cosf`, `swzm_powf`, `swzm_atan2f`; square root, absolute value and rounding up are the compiler's built-ins, exact by IEEE 754.
3. Compile the maths and the operators with `-ffp-contract=off -fno-math-errno` for every target.
4. Check what the object still asks of a C library: `nm -u bridge.o | grep -E ' (sinf|cosf|powf|atan2f|exp2f|sqrtf)'` must print nothing.

**How the three builds are compared.** `tests/same-bytes.sh GLIBC_DIR MUSL_DIR WASM_DIR...` runs `wz manifest` in each build (the WebAssembly ones in `wasmtime`), which prints one SHA-256 per texture over every byte of the picture, and compares the tables with `cmp`: glibc with musl, each with WebAssembly, and glibc with the stored table `tests/reference/kkrieger-854.tsv`. Expect 854 of 854 in every pair, with and without SIMD in WebAssembly. Two more steps keep the claim honest: the edition's first renderer for these operators, built with g++ and the carried maths compiled by gcc, draws the same 854 (`kkrieger-854-gxx-carried.tsv`: another compiler, another bridge), and against the first reference, drawn with glibc 2.43's own functions (`kkrieger-854-glibc.tsv`), exactly the six textures of `glibc-differences.tsv` differ, by 1 to 17 bytes of 786,432, each by one step.

## The partners' server (swz-mcp): working recipe

One program, `swz-mcp --project FILE.k`, serves one open project to an AI partner over the Model Context Protocol on standard input and output. It is written in Zig over the core's C header only (`@cImport`), like every front end.

1. The person chooses once how partners work: `wz partners` shows the three ways and what is kept; `wz partners apply-and-show`, `suggest-only` or `ask-each-time` keeps the choice in `~/.config/stereowerkkzeugrc` (group `[Partners]`, key `Mode`; the editor will share the file); `wz partners forget` takes it back. Nothing is preset, and the server only reads the file.
2. Register it with the assistant's own command, for example `claude mcp add --scope user stereo-werkkzeug -- /path/swz-mcp --project /path/FILE.k --person-socket "$XDG_RUNTIME_DIR/stereo-werkkzeug.sock"`.
3. Prove it: `python3 tests/mcp-proof.py OUT`. Expect "123 checks passed, 0 failed". A scripted partner speaks both protocol revisions, a scripted person answers on the socket, and each check compares with something outside the server: the file's own SHA-256, the reference table, what `wz` prints, a PNG decoded in the test.
4. Prove it under the official client: `python tests/sdk-client.py OUT` with the `mcp` package installed (`pip install mcp` into a virtual environment). Expect "119 checks passed, 0 failed": the SDK's three ways of connecting (`legacy`, `auto`, the 2026-07-28 revision adopted directly), each under the three ways of working and with none chosen. Check the negotiated version in each (`auto` must come out as 2026-07-28: a discover answer the SDK cannot validate falls back to the handshake without a word).
5. For a project open in the editor, register `swz-mcp --attach "$XDG_RUNTIME_DIR/stereo-werkkzeug.sock"` instead of `--project`.

What it offers, and to whom:

| Who | What | How |
|---|---|---|
| The partner | Read the project: pages, operators, parameters under the names of werkkzeug3's own panels, the journal | `project_info`, `list_pages`, `list_operators`, `read_operator`, `list_textures`, `list_classes`, `describe_class`, `journal` |
| The partner | Draw a texture: the picture as a PNG and its SHA-256; export a texture's operators or the project's text | `draw_texture`, `export_texture`, `export_project_text` |
| The partner | Change the project, each change one journalled step under its name, taken the way the person chose | `set_parameters`, `rename_operator`, `set_link`, `set_string`, `place_operator`, `set_bypass`, `set_hidden`, `add_operator`, `remove_operator`, `add_page`, `rename_page`, `remove_page` |
| The partner | Take back its own last step, only under "apply and show" | `undo` |
| The person only | Choose the way of working | `wz partners ...` |
| The person only | Take or drop a suggestion, undo and redo anything, save | the person's socket: `take`, `drop`, `undo`, `redo`, `status`, `save PATH` |

Rules worth copying into any server of this kind:

- **Serve both protocol eras.** A request that carries `io.modelcontextprotocol/protocolVersion` in `params._meta` is 2026-07-28 and is answered statelessly (`resultType`, `server/discover`, `-32022` with `data.supported` for another version, `-32602` without `clientCapabilities`); `initialize` selects 2025-11-25 for the process. The step's author is the client's own name: `clientInfo.name` of `initialize`, or of each modern request.
- **Two kinds of refusal** (2025-11-25, server/tools, "Error Handling"). A message the protocol cannot accept gets the protocol's code: `-32700` not JSON, `-32600` not a request, `-32601` no such method, `-32602` wrong params or an unknown tool. What a tool refuses, a wrong argument included, is a result with `isError: true` and the reason as a sentence, so a model can correct itself.
- **Generate from the table.** The class list of `add_operator` is written from the operator table when the tools are listed; `describe_class` returns the JSON Schema of one class's parameters, made from the same table, and `set_parameters` checks against it.
- **The person's choice is read, never written,** and read again at every change, so a change of mind applies to a running server.
- **A partner's tools cannot answer for the person:** no tool saves, chooses the mode, or takes a suggestion; "ask each time" asks on the person's socket and the partner's call waits for the answer (`--ask-seconds`).
- **A partner can set what a person could type:** a number outside the range of werkkzeug3's own panel is refused with the range.
- **The specification asks for a rate limit** ("Servers MUST ... rate limit tool invocations"): `--calls-per-10s`, refused with a sentence.

## The editor (first light): working recipe

The editor is `stereo_werkkzeug/editor`: Qt 6 Widgets and KDE Frameworks 6 (KXmlGui, KConfig, KI18n, KIO, KWidgetsAddons, KCoreAddons), built by CMake on what the core's `build.sh` made.

1. Build: `./build.sh CORE`, then `cmake -S editor -B ED -DSWZ_CORE_DIR=CORE && cmake --build ED`. The core's folder gives `libstereo_werkkzeug.a`, `libswz_front.a`, their two headers, `swz-draw`, `swz-mcp` and `wz`.
2. Check: `ctest --test-dir ED` (the editor's catalogue is the one the built core prints; the nine translated catalogues are whole).
3. Prove the window: `ED/bin/editor-proof SCENARIO FR_PUBLIC OUT [PARTNER...]` inside a private compositor (see "Proving a window" below). Expect, per scenario: `open-edit` 35 checks, `partner-first` 24, `partner-apply` 17, `partner-suggest` 15, `partner-ask` 15, `refusal` 6, `settings` 6, `socket-kept` 4, `socket-stale` 1, and the ones that send real input (see "Building in the window"): `build` 72, `look` 29, `examples` 23, `show-apply` 19, `show-suggest` 20, `show-drop` 19, `show-ask` 14, `partner-draws` 15, `desktop` 12, each ending "N checks passed, 0 failed". Run `refusal` once per language (`LANG`, `LC_ALL` and `LANGUAGE` set, the locale generated in the image): the same refusal of the core comes out as another sentence in each.

### Keep the logic on the core's side of the window

A front end draws and asks; it does not decide what a parameter line means or what a partner may do. What every front end needs sits in one more library over the C interface, `libswz_front` (`src/front.zig`, `include/stereo_werkkzeug_front.h`), so a page in a browser can follow the KDE window without copying its logic.

- **The panel as fields.** `swz_panel_lines`, `swz_panel_line`, `swz_panel_field` and `swz_panel_choice` turn werkkzeug3's own panel lines into fields a window can draw: a whole number, a decimal, a colour, a choice among named values in some bits of a word, a toggle, a row of bits, a link, a string. The rules are werkkzeug3's: a label's leading `*` and one digit after it are marks, not text (`WinPara::Label` in `winpara.cpp`); a choice text is groups parted by `:`, each with `*N` for its first bit and its choices parted by `|`, holding as many bits as the choices need (`sControl` in `_gui.cpp`); the same label for the same words is one line.
- **The partners' tools on a held document.** `swz_partner_call(doc, host, partner, tool, args_json, ...)` runs one tool of `src/partners.zig` on the document a front end holds. The front end gives the person's kept choice and two functions: one that asks the person about a waiting suggestion, one that hears that a suggestion waits.
- **The window itself** (`editor/src`) wraps the handle (`document.cpp`), paints pages (`pagecanvas.cpp`), makes one widget per field (`parampanel.cpp`), and nothing else knows an operator.

### From Qt: linking two Zig archives into a g++ program

- Build each archive with `-fcompiler-rt`, so Zig's own helper functions travel inside it.
- The bridge is compiled against LLVM's libc++; a g++ program has no `std::__1::__libcpp_verbose_abort`. Define it once in the program (a C function given that linker name with `__asm__("_ZNSt3__122__libcpp_verbose_abortEPKcz")`), in a source file of the program itself, not of a static library that is read before the core's archive.
- Link order: the front library, then the core.

### The live picture, in a process of its own

`swz-draw` reads one packed graph on standard input and writes one answer: the picture, or the core's refusal with its number and values. The editor asks the core for the selected operator's packed graph (`swz_graph_pack`, any operator, named or not), starts `swz-draw` with the limits, and replaces a drawing that is still running when a newer picture is wanted. When the time is up it ends the process and says so. A crash of the operator code ends that process only.
The checksum under the picture is the SHA-256 of the width, the height and every byte, the one `wz manifest` prints, so the window can be checked against the reference table.

### Sentences in ten languages

The core says every refusal as a sentence in English and also as a number with its values (`swz_message_number`, `swz_message_value`; an operator's own refusal inside "operator 3 of 7 (Blur): ..." is an inner sentence with its own number).
The number is the FNV-1a checksum of the template as the source writes it, the same in every build.

1. Every template is kept in one section of the program (`swz_msgs`): in Zig by `@export` with `.section`, in the C++ bridge by a `static const char[]` with `__attribute__((section("swz_msgs"), used))`.
2. `wz messages` reads that section out of the running program and prints `number<TAB>template`, the template with `%1`, `%2` for its places: the catalogue is what the program can say, never a list kept by hand.
3. `editor/po/core-catalogue.tsv` is that output; `editor/tools/gen-coremessages.py` makes `coremessages.inc` from it, each sentence marked with `kli18n`, so `po/update-pot.sh` puts the core's sentences and the window's strings into one template.
4. At run time the editor looks the number up, substitutes the values (`KLocalizedString::subs`) and shows the result; a number it does not know is shown as the core said it, with a warning in the log.
5. `ctest` fails when the committed catalogue is not what the built core prints, and `editor/tests/po-check.sh` when a language is not whole or a translation lost one of its places.

Write sentence families so that the changing part stands after a colon in its dictionary form ("out of memory for: the picture"): a noun inside a sentence needs a case in Polish and German, a contraction in Portuguese and French.

### The partners in the window

- The editor holds the socket (`$XDG_RUNTIME_DIR/stereo-werkkzeug.sock`, the person's alone). `swz-mcp --attach SOCKET` passes each tool call there as one line of JSON and gets one line back; the tools run on the document in the window.
- The server tells the editor its client's name as soon as it knows it (a line with `hello`). On the first one, when no way of working is kept, the editor asks once: three choices, none marked, OK greyed until one is chosen, "Not now" leaves every change refused. The answer goes to `~/.config/stereowerkkzeugrc`, `[Partners]` `Mode`, and the settings page offers it again.
- "Apply and show" selects the operator the partner changed and says who changed what. "Suggest only" shows the waiting suggestion with Take and Drop. "Ask each time" opens a dialog inside the partner's call; the call waits for the answer.
- A path that already holds something is never cleared blindly: a socket that answers belongs to another window (said), a socket that does not answer was left by a window ended by force (cleared), anything else is the person's (left, and said).

### Proving a window

The proof program is the editor's own classes with a script instead of a person (`editor/tests/editor-proof.cpp`), run in a private session: a session bus, KWin on a virtual output, one fresh session per scenario ([stereo-proof-rig](../../stereo-proof-rig/SKILL.md)).
Each check compares with something outside the window: the opened file's SHA-256, the reference table's checksum of the texture, the partner's own answers (the official MCP SDK's client, `editor/tests/sdk-partner.py`), the settings file on disk.
Pictures are KWin's (`ScreenShot2`); a picture that is one colour all over fails its check.

## Building in the window: working recipe

The window is where a person makes a texture from an empty page. What it takes, in the order it was built:

### A place is tried in the core, not judged in the window

`swz_place_check(doc, id, class, page, x, y, width, &out)` tries a place without taking it: for an operator of the page, or with id 0 for a new one of a class.

1. werkkzeug3's own rule for a place comes first (`WinPage::CheckDest` and `MoveDest` in `winpage.cpp`): inside the page's grid of 192 columns and 96 rows, and no cell shared with another operator of the same list. A place that fails it is refused with a sentence that names what stands there. `swz_place` and `swz_add_op` refuse the same places, so a partner's tool cannot make what the editor cannot.
2. Otherwise the place is put on in memory, the connection rules are run on the whole document (`graph.connect`, the same function that decides what is drawn), and the answer is read off: what the rules would say of the operator there (0, or why it would not be drawn), which operators it would take, which would take it, and which others the rules would newly mark. The place is put back before the call returns; nothing is journalled.
3. The window calls it once for each cell the pointer crosses and paints the answer: a green, amber or red place, the operators it would take outlined, and the sentence in words under it (colour alone says nothing to some people). On `kkrieger.k` one trial takes 6 to 8 ms on a machine at rest (15 to 17 ms under load), for a page of 583 operators as for one of 748: the cost is the whole project's connections, not the page.
4. On release the window asks for the change itself and shows the core's refusal when there is one. It never looks for a free place nearby: an invalid place is said, not fixed.

Give every operator an id that starts at 1. The first version numbered from 0, and every front end reads 0 as "no operator": the first operator of a new project could not be selected, and `swz_place_check` took it for "a new operator".

### The operator list

All 218 classes in a tree with a search line, grouped as werkkzeug3's own "add operator" menus group them (`WinPage::AddOps`: Misc, Texture, Mesh, Scene, IPP, MinMesh, by what a class makes; the front library's `swz_class_group`). A class the build does not draw is still listed and can be placed, since the project file carries it; the list says so where the person chooses, in italics and in the tooltip.
Two ways onto the page, because both are how people work: drag the class (a `QDrag` with the class id as its data, the page shows the rules while it is over it), or press `a` on the page, type a part of the name and press Enter (it goes under the selected operator and as wide as it, or to the cell that was clicked).

### Keys that belong to the page

werkkzeug3's single-letter keys (`a` add, `b` bypass, `h` hide) and Delete are handled in the page's own `keyPressEvent`, not as shortcuts of the window: a shortcut on a plain letter or on Delete would take the key away from every text field. F2 and Insert are safe as window shortcuts.

### The preview: pinned, sized, tiled

- Pinned, the preview keeps its operator while the selection moves; it redraws whenever the project changes, so the person sees a texture change while working on an operator far above it. When the pinned operator is removed, the preview says so and follows the selection again.
- The picture sits in a scroll area and is painted at a whole multiple when enlarged (no smoothing), fitted by default; "pixel for pixel", larger and smaller go by factors of two.
- Three by three paints the same picture nine times, edge to edge: a seam shows as a line. The proof reads it back from the compositor's picture of the screen: the tile to the right, the one below and the last are the first tile again, and a third of a tile further the comparison fails.
- The time under the picture is the one the drawing process measured, the size the picture's own.

### The two sides of a step

`swz_graph_pack_across(doc, id, ...)` packs a texture as it is on the other side of the journal's last step: for a partner's waiting suggestion as it would be when taken, for an applied step as it was before. The core replays or reverts the step in memory (the journal's own undo and redo, which allocate nothing), packs, and puts it back.
With `swz_graph_pack` for the side the project is on, a window draws "before" and "after" in two drawing processes without changing the document: "Before and After" is a second preview made of that, with Take and Drop for a suggestion and Undo for an applied step. The same widget sits in the "ask each time" question.
`swz_step_ops(doc, step, ids, kinds, max)` says which operators a step changed, added or removed; the window marks them on the page, dashed while the step only waits.
The check that keeps it honest: the "after" picture shown for a suggestion must be the picture the preview shows once the suggestion is taken, and for an applied step the picture the partner itself drew after its change.

### A partner's picture does not hold the window

`draw_texture` used to run inside the window's thread for as long as the operators took. The front library now gives it in two halves: `swz_partner_draw_begin` finds the texture the arguments name and hands out its packed graph, the window draws it in `swz-draw` as it draws its own preview, and `swz_partner_draw_end` makes the answer from the picture (the same bytes as the whole tool: the test compares the PNGs). When the project changed meanwhile so that the name now means another operator, the second half refuses and says so.
Measured in the proof (`partner-draws`) on a machine at rest: a partner drew 54 pictures in 8.2 s, 6.0 s of it the operators' own time, while the proof's person clicked operators on the largest page; every click landed, and the window's longest standstill while a picture was under way was 16 to 32 ms over three runs. With other builds loading the machine the same pictures took 24.7 s of operator time, up to 1.5 s each, and the longest standstill was 131 ms. The tools that only read still run in the window's thread; the longest, `list_textures` over 854 textures, held it for 77 to 141 ms.
Ask of such a measure what it is relative to: the check is "less than a quarter of a second, and less than a fifth of the slowest picture's own time", and it prints the three numbers.

### The examples, the icon and the file type

- The starting projects are kept as the core's text form (`editor/examples/*.txt`), packed by `wz pack` at build time and carried inside the program as resources. An example opens as a project without a file: saving asks for a name, and nothing can write the example.
- The icon is one SVG, installed as `hicolor/scalable/apps/stereowerkkzeug.svg` and also inside the program, where it is drawn with `QSvgRenderer`, so that a build tree and a system without Qt's SVG plugins show it too.
- The file type is `application/x-werkkzeug3-project`: the glob `*.k` and two magic rules, `nova`, the number 1 and `<<<<` for the outer form with the player's part, and `<<<<` with the editor's class number for the document alone. Test the magic on every file you have, and on two that must not match (a text that begins with "nova", any other text).

### Proving it with real input

The checks of milestone 4 posted events into the program. A drag cannot be proved that way: on Wayland the compositor starts it, from a real button press. So the proof sends the person's input to the compositor and lets it come back as the person's would.

1. `editor/tests/realinput.cpp` speaks KWin's `org_kde_kwin_fake_input` on a connection of its own (the protocol file is KDE's; the rig's `fakeinput` tool speaks the same, see [stereo-proof-rig](../../stereo-proof-rig/references/input-delivery.md)). KWin takes it when started with `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1`.
2. The window is shown full screen on the private output, so a point of the window is the same point of the screen (a Wayland client is not told where its window is). Popups are placed relative to their parent, so `mapToGlobal` is right for menus too. A dialog is a window of its own whose place the client does not know: drive it with keys.
3. The steps run in a thread of their own (`runInput`), and the window's thread turns its event loop meanwhile. Reading what the window shows goes through `onWindow` (a blocking queued call).
4. A drag is a press, a dozen moves, a short stay, then the release; while the button is held the steps read the page's state and take a picture of the screen from that thread.
5. Whatever opens a dialog must be answered in the same run of steps: the window's thread stays inside the dialog until it closes.
6. The control: the same scenario with KWin started without the leave for fake input passes one check (the window is there) and fails the next two (nothing could be sent; the first key did not arrive). Make the function that sends say whether anything was sent: the first version returned true with no connection, and a check named "real input reaches the compositor" passed in the control.

The rig's image needs what a Plasma session has: `plasma-integration` (KDE's own file dialog, driven by typing the path and Enter) and `qt6-svg-plugins` (without the SVG icon engine no themed icon is drawn, and every button shows as text).

## The stereo preview: working recipe

What is true for every Qt program's 3D area is in [stereo-window-3d-area](../../stereo-window-3d-area/SKILL.md) and its [lessons](../../stereo-window-3d-area/references/lessons-2026-11.md); this section is the editor's own part.

### Three kinds of stereo project, and nothing else

Daniel's words of 10 and 11 November 2026 fix the kinds: a picture whose relief gives each eye its picture (the relief lies at the surface or behind it, a few pixels in front allowed); two procedures, one for each eye; a stereo photograph as the source, whose two eyes are the targets of two procedures.
Nothing is worked out between the eyes: no matching, no estimate of depth.

- The values are the project's (`swz_stereo`, `swz_set_stereo`): the kind, two operators (the picture and its relief, or the left and the right eye), for a relief its depth (pixels behind and in front for an eye 1920 wide, the three heights, wrap or cut at the edge), for a photograph its file's name. They are journalled as a whole, so undo and redo are one swap.
- **In the file they are a part of their own after the last byte werkkzeug3 reads**: `SWZS`, a version, a length, the values, a checksum, the part's length, `SZWS`. `WerkkzeugApp::Read` takes a pointer, reads the document and the player's document and stops, so it never looks there; `WerkkzeugApp::Write` writes its own model, so a file werkkzeug3 saves again has lost them. A project that is not stereo writes no such part: its bytes are what they always were. Say both facts where the person can read them (`wz info`, the README).
- Operators are named in the file by their place, as werkkzeug3's own events are, and by their stable id in memory.
- The text form has one `stereo` line and packs to the same bytes.
- The start of a relief's depth is the stereo texture module's own (10 behind, nothing in front, black the deepest, white the surface, the picture tiles); the relief itself is always named by the person, an operator or the picture's own brightness.

### One mapping: reuse the stereo texture module's functions, and prove it

The relief's two eyes are drawn by the edition's stereo texture module (`parallaxMap` and `eye`, relief mapping once per eye); the core carries those two functions unchanged in `src/stereo.zig`.
The proof that it is one mapping and not a second: `wz stereograph GRAPH OUT` draws a typed graph with the module's own lines (`lit`, `height`, `depth`, `edge`), and every stereo drawing of the module's native build is compared with it, pixel for pixel, at three eye widths (27 of 27 the same).
The relief's pixels are for an eye 1920 wide and scale with the width of the eye the picture is shown in, in the picture's own pixels: a picture shown once is its own width, three by three is three pictures wide.

### Drawn in the drawing process, as every picture

`swz_stereo_job` packs what a drawing needs (the way, the depth, the eye width, one or two packed graphs); `swz-draw` takes a job as it takes a graph and answers with the two eyes side by side, the left eye first.
The window never runs the mapping in its own thread: a 1024 pixel relief is hundreds of millions of ray steps.
A pair is two pictures of one size side by side; eyes of two sizes are refused with both sizes in the sentence, never resized.

### The 3D area in a Qt Widgets dock

1. `StereoArea::prepareWindow(mainWindow)` first thing in the window's constructor: where the compositor offers the stereo protocol and the declaration library started, the window gets `WA_TranslucentBackground` and an event filter that paints its ground. Elsewhere nothing changes and the window is the ordinary window.
2. The picture's canvas (inside a `QScrollArea`, inside a `QDockWidget`) paints a transparent rectangle with `CompositionMode_Source` where the picture shows, and nothing else there.
3. The surface below the window holds **the part of each eye that shows**, copied from the eyes as the core drew them: a crop at the picture's own pixels, wrapped for three by three. Its destination (`wp_viewport`) is the rectangle that part has in the window. The compositor resizes it once; the program fits nothing to the window. Fitted, enlarged, three by three and pinned all fall out of that one rule.
4. "Render resolution per eye" is a largest eye: the picture's own size first; a wider eye is made smaller by a whole factor, each pixel the mean of its block. Two eyes larger than a surface can hold are said, with the size, never silently made smaller.
5. A 100 ms timer looks at the place again while two eyes are shown (a dock was moved, the window resized); a key of the eyes' serial number, the crop and the place keeps it from committing the same picture again.
6. Messages belong to the preview, in a widget of their own: the desktop takes no declaration; the declaration failed (with the system's words); the two eyes do not fit a surface. They are said for a stereo project only: a project that is not stereo is shown as it always was and says nothing.
7. A dock that can be floated is prepared like the main window, before it is created (`StereoArea::prepareWindow(previewDock)` right after the dock is made): floated, it is a top level of its own with the alpha buffer, and the area follows `window()`. Without that a floated preview cannot show 3D (milestone 6 said so in a message; milestone 7 removed the cause).

### The program's three options, and the project's values

The 3D menu holds Show in 3D, Render Resolution per Eye and Display Settings (`kcmshell6 kcm_kscreen`), and a proof counts its entries.
Show in 3D is marked from the start (Daniel, 10 October 2026: on a stereo desktop stereo content shows in stereo wherever it appears; flat is the person's opt-out, never the default): a stereo project opens in 3D where the desktop takes the declaration, a project that is not stereo is unchanged, and the person's unmarking is kept like every setting.
Milestone 6 started with it off, which was a brief's mistake; a proof now reads the start, the opt-out and its place in the settings.
The relief's depth has no upper limit (Daniel, 14 October 2026: a tool's depth is the user's setting, unclamped, with no forced warning); only a number that is no distance is refused.
Everything else about stereo is the project's and lives in the Stereo panel: it changes by journalled steps and is saved when the person saves.
The program draws its own pictures, so no action of it swaps eyes; the proof looks through the action collection for one.

### A stereo photograph as the source

- Read through the edition's shared readers (`Stereo::Picture::load` of stereo-layer, with the edition's KImageFormats for JPS and MPO and the edition's Qt for PNG's `sTER`): never a list of formats of the editor's own.
- The person's corrections (the input packing and "Swap left and right eyes") are kept for that one file in the program's state file (`KSharedConfig::openStateConfig()`, a group per absolute path), not in the project and not in the photograph. An entry with nothing set is deleted.
- "Save the Correction to the File" writes the format's own mark, reads the file back with nothing chosen, compares the two eyes, puts the file back when they differ, and forgets the stored entry when they are the same. Three marks, none of which touches a picture's bytes or compresses anything again:
  - PNG: the chunk `sTER`, inserted after the header (two eyes side by side, a width divisible by 16).
  - JPEG: the JPS block, an APP3 segment right after the file's first two bytes: `FF E3 00 12`, `_JPSJPS_`, `00 04`, the descriptor's four bytes with the most significant first (flags, layout, type: `00 04 02 01` is a stereo picture, side by side, the left eye first; layout 3 is one over the other, 1 is rows), `00 00`. An older block is left out. The shared reader takes the descriptor in this order only; and it looks for the block in files named `.jps`.
  - MPO: the two pictures' MP Individual Numbers (tag `0xB101`) exchanged, found by walking each `MPF` segment's lists in the byte order its header states. Exactly two bytes change. That is the whole correction an MPO can carry: a packing chosen by hand is refused for it with the reason.
  A correction a format cannot hold (a top and bottom PNG, a depth choice) is refused with the reason, the file untouched, the correction kept.
- A picture with its depth map is a packing like any other (side by side, top and bottom, with a layer in front, with the background, with the depth in a file beside it): the manual list offers every layout the shared reader has, and the shared library makes the two eyes. Its own settings object and controls (`Stereo::DepthSettings`, `Stereo::DepthControls`) stand in the panel for such a picture; what the person chooses there is kept for that one file as the settings' own text. No file format has a mark for that choice, so saving it into the file is refused with that reason.
- The project keeps the file's name; the two eyes are the fitter's targets. The preview shows them beside the two procedures: inside each eye the photograph's eye, then the procedure's, each at its own size.

### Proofs read from the compositor's own picture

With stereo content on the screen, Stereo KWin's ScreenShot2 holds both eyes side by side, each the screen's size; the proof cuts it in two.

1. **The 2D control:** 3D off, 0 pixels differ between the eyes over the whole screen.
2. **Geometry against a prediction:** a relief that is a white square (the surface) on black (the deepest level), 60 pixels behind for an eye 1920 wide. Pixel for pixel on a 256 pixel picture the deepest level is 60 * 256 / 1920 = 8 pixels apart, three by three (an eye 768 wide) 24. The proof finds the whole-pixel shift that lays the right eye's strip over the left eye's and asks for 0 pixels left over; one pixel beside the prediction must not fit (the control). The middle of the square has 0 differing pixels.
3. **Left eye first:** two procedures that differ on purpose, a red picture for the left eye and a blue one for the right; the screen's left eye is red. And the screen's left eye equals the core's left eye pixel for pixel.
4. **The window's own elements:** outside the area's rectangle 0 pixels differ between the eyes.
5. **The declaration:** one fresh run with `WAYLAND_DEBUG=client`: one `get_subsurface`, one `place_below`, one `kde_stereo_content_manager_v1.create` on that surface, one `set_content(3)`, none on the window's surface.
6. **A refused declaration:** an environment switch makes every declaration fail as a compositor's refusal would; the preview says it and the screen shows the left eye's picture once, the same in both eyes.
7. **A compositor without the protocol:** the same scenario under Weston's headless backend; the message is read from the widget, in each of the ten languages.
8. **A photograph per packing family:** MPO, JPS with and without its block, PNG with `sTER` in both modes, a plain side by side pair, a plain top and bottom pair (the packing chosen), a plain pair the wrong way round (the swap); in every case the left eye is the red picture.

## The fitter as a tool: working recipe

The fitter is the edition's [procedures from pixels](procedural-texture-from-a-bitmap.md) program: a picture's pixels in, a procedure out, never from text.
In the window it is a tool the person starts on a picture they chose; its answer is journalled operators on the open project.

### One small program between the window and the fitter

- The fitter's folder is carried as it is, in the layout of its own home (`fitter/pixels`, `fitter/werkkzeug`), every file compared equal: its next version takes its place by replacing the folder.
- `swz-fit` (`src/fitrun.zig`) is the only program that knows how the fitter is started and what it writes. It prints five kinds of lines and nothing else: `note TEXT` (what the fitter says while it reads), `step P K OPERATORS BYTES FILE LABEL` (kept step K of procedure P, as a script), `procedure P X Y SIDE FILE` (procedure P and the window of the picture it draws, in parts of the picture; `0 0 1` is the whole), `done SECONDS`, `refused SENTENCE`.
- The window and the partners' server read those lines only. A fitter that answers with four procedures for one picture prints four `procedure` lines; the window already places each on a page of its own (proved with a stand-in that speaks the lines). What joins four quarters into one picture is the core's next operator, not the window's work.
- The fitter runs as a child with the adapter's own environment (`execv`), asked to die with its parent (`prctl(PR_SET_PDEATHSIG, SIGKILL)`); the adapter answers SIGTERM by ending the child. A proof ends the adapter in the middle and looks for the fitter's process.
- The fitter writes its notes on standard error and its steps when it ends, so the adapter joins both streams, and steps arrive at the end: while it runs, the person sees the notes and the time.

### The fitter's operators are classes of the core

The fitter builds with nine operators of its own (Noise, Cells, Tiles, Ramp, Layer, Shade, Scatter, Wear, Tint), each with a version word and a parameter table.

- They join the operator table after werkkzeug3's 218 classes, with class ids of their own above every id of werkkzeug3 (0x5300 to 0x5308); their rows are made at compile time from the operators' own tables, so the parameter panel, the text form and the partners' tools have them without one hand-written line.
- They are compiled as a named module (`--dep modernops -Mmodernops=fitter/pixels/modern.zig`): a Zig file cannot import a file outside its module's folder, and what the module declares for another program (the fitter's own bridge) is not linked while nothing calls it.
- They have no size of their own. A drawing is asked for at a canvas (512 pixels when nothing is said; `--canvas N`, the limits' `canvas`, View, Draw Procedures Without a Size At), on a margin that the neighbourhood operators read and that is cut away, exactly as the fitter draws them.
- In a `.k` file they stand on their pages like any operator; an earlier version of an operator holds its whole table's words, the later ones at their starting values. A project without one writes the bytes it always wrote.
- werkkzeug3 itself: `WerkOp::Init` takes class `0x04`, its error class, for an id `FindWerkClass` does not know, and `WerkDoc::Read` takes the smaller of the file's and the class's counts. So it shows such an operator as an error and loses its values when it saves. Read from its source, not run.
- **The proof that the core draws them as the fitter does:** one script, drawn by the fitter (`p2p render SCRIPT OUT.ppm 9`) and by the core after `wz place`: the same 786,432 bytes. The checksum of the fitter's drawing is the test's reference.

### A found procedure on a page

`swz_place_procedure` (`src/fit.zig`, `wz place`) reads the fitter's script (`NAME OPERATOR INPUTS WORDS`, the words in hexadecimal, then `out NAME`) and lays it out by werkkzeug3's own rule: an operator takes the operators in the row right above it, from left to right.

- The picture's operator carries the procedure's name. An operator that feeds several others is named `NAME.ITSNAME` and reached through Load operators, which is werkkzeug3's own way to use a picture twice. Stacks stand side by side, in bands when the page's width is used up.
- A name is a store found from anywhere, so a name that the project already has is refused; so are an unknown operator, a wrong number of inputs, too many words, a missing `out` line and a page that holds operators.
- Each step the fitter kept is one journalled step: the first adds the page and the procedure so far, each later one replaces the page's operators with the next. Undo walks back to a simpler procedure; every operator is the person's to change.

### The tool in the window

- Its own dock, a second tab in the preview's place: it has pictures of its own (the picture beside the procedure) and needs that room. In the lower tab group its buttons lay below the fold.
- The picture is read from a file the person chooses. The fitter reads a square whose side is a power of two: the tool takes the largest square from the middle and, when its side is no power of two, makes it smaller to the next one, and says both.
- The fit is a `QProcess`; Stop is `terminate()`. Nothing is placed by a stopped, refused or crashed fit, and each is said with its reason (the fitter's own sentence in its own words).
- The comparison draws the procedure at the picture's size (the canvas), so "1:1" is pixel beside pixel; the two views' scroll bars follow each other.
- Parts that come and go while a fit runs (the bar) keep their room when hidden (`QSizePolicy::setRetainSizeWhenHidden`), and the state sentence has room for five lines from the start: what stands below does not jump under the pointer.
- A fit belongs to the project it was started for. The tool keeps the document's generation at the start; a fit that ends after another project was opened places nothing and says so, and the tool forgets which operators its last fit placed when the project changes.

### A stereo photograph: one fit for each eye, and nothing between them

The photograph's two eyes are fitted one after the other, each the regular way; the pages are `NAME.L` and `NAME.R`, and one more journalled step names the two results as the project's left and right procedures.
Nothing is matched or estimated between the eyes.
What to expect, measured on three real stereo photographs (bark, lichen, sand; each eye 1,024 pixels): the two fits take 21 to 31 seconds together, the two procedures are 9 to 13 operators and 373 to 471 bytes each, and they are not the same procedure: one eye's fit kept furrows where the other kept patches.
Two separate fits know nothing of each other, so do not promise that the pair reads as depth: hand the pair and the photograph's own pair to a person at a 3D screen.
Daniel's order for what follows (11 November 2026): only if the pair does not read as stereo, one eye is fitted and the other starts from that procedure with the separation added. The project's form allows it (a pair names any two operators); it is built on his word only.

### A partner starts the same tool

`fit_picture` takes `"picture": "chosen"` (the picture the person chose in the Fit tool) or `"photograph"` (the project's stereo photograph), an optional name and a reason.
A partner names no file and writes no procedure.
The tool runs in two halves like `draw_texture`: the first checks the call and the person's way of working; the window runs the fit in its own tool, where the person sees it and can stop it; the second lays the answer on its page as one step under the partner's name, applied, held or asked about as the person chose.
Where no window holds the project the tool is refused and says where it works.
`draw_stereo` runs in two halves the same way, so a partner's two eyes are drawn by the drawing process and not in the window's thread.

### Proving it

1. A stand-in fitter (`tests/fake-fitter.sh`) that speaks as the fitter does, takes as long as it is told, refuses, crashes or says nothing on request, and answers with reference scripts: the tool's whole behaviour is proved in seconds. A stand-in adapter (`tests/fake-fit-four.sh`) answers with four procedures.
2. The window's heartbeat: a 2 ms timer records the longest time between two turns of the event loop while a fit runs (11 to 44 ms with the stand-in, 12 to 35 ms with the real fitter on a machine at rest and up to 59 ms with other builds loading it, while the person's real clicks land).
3. The real fitter in the window on real photographs, the pairs exported as stereo PNG files and read back with the chunk parser.
4. A partner under the official SDK's client: refused while the person has chosen no picture (it leaves a marker file at its first refusal, and the proof's person chooses then), applied or held afterwards.
5. The corrections, each against the compositor's own picture or the file's own bytes: the start in 3D and the opt-out, 80 pixels of parallax at 600 pixels behind (600 * 256 / 1920), a floated dock's two eyes, the JPS block's 20 bytes with the rest of the file unchanged, an MPO's two changed bytes, two eyes from a depth map.

## Extending the editor: working recipe

What a later round adds comes in through what is already there: a new fitter through the adapter, new operators through the table, depth and the object view through the drawing process.

### A new fitter version through the narrow interface

- Replace the fitter's folder with the new version and compare every file with its source commit (`cmp`); nothing in it is edited.
- New operators of the fitter are new classes at the end of the list: an operator's class id is its place, so nothing already saved moves.
- An operator that lays whole procedures (`Quad`: four, `Grid`: up to four by four, `Stack`: two to four results over each other) is a procedure's last operator, and each procedure under it is drawn on a canvas of its own. The core's drawing does what the fitter's own program does: for input `q` of a Quad the canvas shows the place `2x - column, 2y - row`; for a Grid tile `s (x - col / cols), s (y - row / rows)` with `s` the smaller of columns and rows; a Stack's procedures share the window and are cut to the picture before they are laid. One margin for all canvases of a Quad or a Grid, the widest any of them needs.
- The adapter does the new work, the window none: `swz-fit --procedures 4|4x2|2x4|16` cuts the picture into tiles (a tile that is not square is laid beside or below its own mirror image into a square), runs the fitter on each tile by the fitter's own recipe (simple procedures, a seed of its own for each, no structure read where a mirror image would be read as a repeat), four at a time, and joins them with the fitter's own `quad` and `grid` commands; `--layers 1,4` lays whole results with its `stack` command. The answer is still one `procedure 0 0 0 1 FILE` line.
- On the page, each procedure under a Quad, a Grid or a Stack is a stack of its own, named, and the joining operator takes it through a Load: sixteen procedures side by side above one Grid are wider than a page's 192 columns.
- Prove it on the fitter's own procedures: every typed procedure of its evidence, drawn by its program and by the core (typed, and placed on a page and drawn from the project file), compared byte for byte. `wz script GRAPH OUT.script` turns typed text into the fitter's script for that.
- The stand-in fitter learns the joining commands too (the parts' operators renamed under one joining operator), and writes every command line it was started with to a log: the proof reads what the adapter asked for.

### Carrying other people's operators

- Read the licence in the files themselves and the pull request's own text first. A file head that says "distributed under a BSD license, see LICENSE.txt" in a tree whose `LICENSE.txt` is BSD 2-clause is carried under that licence, head unchanged, author named from the commits' own author field.
- Carry the files unchanged in a folder of their own with a record beside them: whose work, from which commit, fetched how, each file's SHA-256, what is left out and why, what to do when upstream changes it. A test checks the checksums.
- Where the work comes with its own declaration of parameters (Werkkzeug4's `.ops` file: names, ranges, defaults, choices, and a code block for each operator), generate the table and the calling code from it: a parameter structure filled from the operator's words, and the author's own code block compiled around it. The arithmetic is then the author's, and only the form is ours. Keep the generated files in the tree and have a test make them again and compare.
- Take what the program can use (a texture editor takes bitmap operators, not mesh operators) and say what was left out.
- Carry an operator only when nothing in the table does its work: of OpenKTG's thirteen, twelve are the ancestors of operators already there, and one (the colour matrix) is not.
- A library with its own names for common types (OpenKTG's `types.hpp` beside Altona's) is a translation unit of its own behind one `extern "C"` function.
- Check which maths functions the new code calls. Any that the C library decides (here the natural logarithm) is carried with the others, so the same procedure still draws the same bytes with glibc, with musl and in WebAssembly.
- One reference table (name, checksum of the drawn bytes) for every added operator at its defaults, compared by every build.

### 16 bits a channel, end to end

- Find the depth the operators already hold before adding any. werkkzeug's operators hold fifteen bits a channel (0 to 0x7fff, in sixteen-bit words); the narrowing to eight bits was only at the way out.
- Hand the samples out without narrowing where sixteen are asked for: `(x << 1) | (x >> 14)` makes 0x7fff into 0xffff, and each sample's high byte is then exactly the eight-bit sample.
- A PNG of sixteen bits says the truth about its samples in `sBIT` (15 significant bits; PNG third edition, 11.3.2.4); `sTER` stays right after the header for a pair.
- The depth is the project's own value: journalled like any change, in a part of the file after everything the old program reads, absent for eight bits so that an old file stays the old bytes.
- Every step that works on samples needs its sixteen-bit form (the relief's step between the eyes, the drawing process's answer, the composition of the two eyes for the desktop). The eight-bit form of a step that another program is compared with stays as it is.
- To the desktop: a `wl_shm` buffer of `xbgr16161616` where the compositor announces that format (listen to `wl_shm.format`, and wait one more round trip for the announcements); Qt's `Format_RGBX64` has the same bytes on a little-endian machine. Where the format is not offered, eight bits go over and the window says so.
- A toolkit's own widgets paint with eight bits: say that in the window instead of implying sixteen.
- Proofs read the saved values: the file's own samples counted (how many values a channel takes, how many samples are not an eight-bit value repeated in both bytes), by the writer's reader and by another reader (Qt's PNG reader gave `Format_RGBA64`); the buffer format read from `WAYLAND_DEBUG`.

### The material view: one world, two cameras

- A texture on a lit sphere, plane or cube with its relief is a real 3D scene, so it is drawn with two cameras, never by shifting one picture.
- The cameras stand side by side with parallel axes. Both look through one window, a rectangle in the plane through the object's centre: the ray of a pixel goes from the camera through that pixel's place in the window. That is the off-axis projection, and the window's plane has no parallax.
- Each eye finds its own point of the relief along its own ray (a march below the surface in the surface's own frame), so the relief has depth of its own in the pair; the light and the texture exist once.
- The relief lies below the surface, never above it, and the object's outline stays the smooth shape's.
- Publish the scene's numbers (camera distance, half the window's height, how far apart the cameras are, the wall's distance, the object's sizes) from one call, so that a proof predicts from the numbers and not from the drawing code.
- The prediction in closed form: a point at depth `z` has the parallax `apart * (1 - distance / z)` in scene units, times `eye_width / window_width` in pixels, positive behind the screen. For a sphere, the tangent lines from each camera give the outline's left and right end; for a plane and a cube, each corner turned and projected through the window gives the bounding box. Upright positions do not depend on the camera: the rows of the outline must be the same in both eyes, which is the check that catches cameras turned inward.
- Measure on a plain red texture (the wall is grey): the bounding box of the pixels whose red is well above their blue, in each eye of the compositor's picture, at one scene pixel to one screen pixel. Within one pixel of the prediction; predictions for cameras turned inward and for cameras twice as far apart must fail.
- With 3D off the scene has one camera, in the middle, and both eyes of the screen are the same picture to the last pixel.
- The program keeps its three 3D options. The view opens in 3D where the desktop takes the declaration; the pair goes to the same declared surface as every stereo picture of the program.

## Text and fonts: working recipe

Daniel's direction for this part: "letters are drawings with meanings, and when fonts are pure drawing, it's even better".
A glyph is a small exact drawing that a procedure calls in a few bytes.
The Text operator is a seed a person or the fitter places, never a way to describe a texture in words.

### A font library in a same-bytes core on four targets

- Compile the libraries from their sources with the core's own compiler, for each target, into one archive beside the core: FreeType, HarfBuzz, SheenBidi, plutovg and plutosvg, libpng, zlib, Brotli. A system's packaged library is another version on every machine, and the same bytes end there.
- Give every library the flags the core's maths has: no fused multiply-add (`-ffp-contract=off`) and no `errno` from the maths. An outline filled with a fused multiply on one target and without on another differs in single coverage values.
- Generate the small configuration headers (FreeType's module list and options, libpng's `pnglibconf.h`, the Unicode block tables) by a script in the tree, so that every target is built from the same choices.
- WebAssembly needs three things the others do not: a stand-in for `setjmp.h`, which WASI's C library refuses without the exception-handling extension (here `setjmp` gives 0 and a `longjmp` says which library asked and stops the module, never a silent wrong picture; libpng jumps only on a broken file), WASI's emulation libraries for signals and process clocks, and a larger stack (16 MB here).
- Keep the renderer's files that another program also compiles unchanged, and wrap them: a file of the core includes each and replaces what must be the core's (here `getenv`, so that the core names the font index and can reset it between documents).
- Copy every library's licence text beside the build and install it with the program. FreeType's licence asks for its credit line in the documentation.
- Check which licences meet in one binary. FreeType's own licence and Apache 2.0 do not go with version 2 of the GPL, so a program that also links a library under "GPL 2 or later" is distributed under version 3 or later.
- Prove it per build, not per library: one font index written by each build, compared byte for byte, and a set of graphs that reach every path of the libraries (TrueType outlines, CFF from a collection, a variable CFF2 font and a variable TrueType font at chosen axis values, Type 1, WOFF, WOFF2, a colour bitmap font, shaped Arabic, Devanagari and Thai, mixed directions with numbers, a missing glyph), each drawn by every build and compared with the others and with a reference table.
- Keep beside the reference table the SHA-256 of every font file it was drawn with. On a machine with another version of a font the comparison between builds still holds, and the comparison with the table says which font differs instead of failing without a reason.
- What the machine's fonts cannot reach stays unproven and is said: here COLR layers and paint graphs, SVG glyphs and `sbix`.

### One operator, with a version word

- An operator that exists in the old program keeps its class and its old bytes. Its new form is the same class with more words, and a version word tells them apart: 0 is werkkzeug3's own Text (nine words, two 8-bit strings), 2 draws any font (twelve words and three strings: the text in UTF-8, the font's key, the variable axes).
- A project that holds only the old form is saved to the old bytes, so werkkzeug3 still reads it.
- The table's row for the operator is the old row with the new words after it, and the panel's new lines appear only for the new version.
- Typed text and the packed form carry strings too: strings as quoted text in the typed form, a flag in the packed form's header that says strings and font records follow.
- The coverage of a glyph has 256 levels in FreeType. A 16-bit document says so in the drawing's notes instead of implying sixteen bits of coverage.
- Things a drawing has to say without failing (a stand-in for a Windows font name, a glyph the font does not have, another version of a font) go into notes that travel with the picture: from the drawing process to the window, the command line and the partners' answer.

### Naming a font so a document draws elsewhere

- A document names a font by family and style, which is what a person reads and what stays the same across versions of a font.
- Beside the name it keeps a record: the PostScript name (name ID 6), the version, the file's SHA-256, the file's name, the designer (ID 9), the copyright (ID 0), the licence class and the licence address (IDs 13 and 14). The record is read from the font's own name table when the font is first used.
- The records live in a part of the file after everything the old program reads, and are absent when no operator names a font.
- Resolution in this order: the same key and the same file is drawn; the same family and style and the same file under another key is drawn; the same family and style from another file is drawn and said ("another version"), and the person can take this machine's font into the record; nothing is refused by name.
- A font's licence class is read, never guessed: the class comes from the name table's licence text and address, and "not stated" is a class of its own.
- Nothing is fetched. The record says where the font came from so that the person can get it.

### The missing font, told in the window

- The refusal names the font, its PostScript name, the file and its checksum, who made it and its licence class, in one message in the window, said once per state and not on every change.
- The person's choices are buttons on that message: choose another font (journalled, so Undo brings the old name back), look for fonts again (after installing it), draw without the texts.
- No other font is ever drawn in a missing font's place without the person choosing it.
- The stand-ins for werkkzeug3's Windows font names (the machine's own font of that name, else fontconfig's metric-compatible font) are a designed route for old projects, and each use is said in the notes.
- A chooser opened from a message must not block: open the dialog non-modally and act on its signal, so that previews and partners go on.
- Prove it with a font folder of the proof's own (an environment variable names the folders the index reads): draw, remove the file, look again, read the message, take each choice by a real click, put the file back and compare the bytes with the first drawing, then append one byte to the file for "another version".

### Glyphs as seeds, and the browser

- A seed is two operators: a flat colour and one Text with one glyph, centred, at a fill of the canvas. Its words and strings are 67 to 85 bytes.
- One function makes the seed for the command line, the window and the partners' tool, and the proof compares their bytes.
- "Pure drawing" is measured per font from its character map: a font is a drawing font when more than half of its characters lie in Unicode's blocks of symbols, dingbats, ornaments, arrows, box and block elements, geometric shapes, emoji and the private use areas, or when its character map is a symbol map. The browser lists these first, and "Only drawings" is marked from the start.
- The index of the machine's fonts is made by the core itself, in the cache folder, and made again on request. The window never reads font files on its own.
- A glyph's picture in the grid is drawn by the core, so what the person sees is what the seed draws.
- The partners get the same three steps as tools: list the fonts, list a font's glyphs, place a glyph as a seed in the open window as a suggestion or a step.
- Every new sentence goes through the catalogue in the ten languages, and the panel is captured in each.

### Dropping an editor copy for the shared library's call

- Before removing a workaround, read which released version of the library does its work, in the library's own changelog and source. "Merged" and "published" are different states: here the published package was older than the merged fix, and the metadata-only save came two versions after the one the task named.
- Raise the version the build asks for, so a machine with the older library fails at configure with a clear line and never at run time.
- Write the proof for the property, not for the old implementation's bytes: "a save changes metadata only" is proved by splitting the JPEG at its first start-of-scan marker and comparing everything from there to the end before and after, and by finding every earlier segment again in its order.
- Red before, green after: the old source under the new checks shows what the checks catch, then the new source passes them.
- A stricter library can refuse what the editor's own code accepted. That is a finding about the fixture or the file, to be read in the library's source before anything is changed: here the proof's MPO lacked `BaseViewpointNum`, which a whole disparity pair carries, and the library was right.
- Keep the refused case as a fixture of its own and prove the refusal: the file untouched, the reason said, nothing written by the editor.

### The real fitter's counts in the window

- The counts a stand-in proved (four, four by two, two by four, sixteen) are proved again with the real fitter by real clicks: the adapter's command line, the joining operator on the page, the number of procedures standing on it, one step of the person's, the window's longest pause.
- Count the procedures by the Loads that stand over the joining operator's own width. A procedure's own stack can hold a Load in the same row.

## Werkkzeug4 itself on Linux: what a probe found

Measured on 11 November 2026 in a Debian testing container, g++ 16.2.0, from `fr_public` at `8c8f82c`. Nothing of it is packaged.

| Tree | Build settings | How far it gets |
|---|---|---|
| As published | Altona's own `Makefile.linux.boot` | Stops at the first file. `types.hpp` defines `new` as a macro before `<math.h>`, and the C++ library's headers of today do not survive that |
| As published | The C++ of its time (`-std=gnu++98 -fpermissive`), the makefile's two obsolete linker flags replaced, `-fno-delete-null-pointer-checks`, `-finput-charset=ISO-8859-1`, a `freetype-config` stand-in | The bootstrap completes: `asc`, `makeproject` and `wz4ops` build and run, and `makeproject` writes makefiles for 15 configurations. Werkkzeug4 then compiles `base`, `util`, `shadercomp` and `gui`, and stops in `extra/mcubes.cpp` (a member of `__m128` only MSVC has), in `wz4lib/gui.cpp` (`memset` not declared) and at `wz4lib/incbin.asm` (needs NASM, as a 32-bit object) |
| With pull requests #105 to #108 | Altona's own makefile | Stops at the same first file |
| With pull requests #105 to #108 | As above but `-std=gnu++11` (the pull requests use `noexcept`), one line of `system_linux.cpp` changed, the C++ copy of the embedded file used | Everything up to `wz4frlib` compiles; three of its files do not: `wz3_bitmap_code.cpp` (`__stdcall` is not defined for Linux in Altona's own headers), `wz4_modmtrl.cpp` (20 errors about constant expressions) and `tADF.cpp` (`base/System.hpp`, a capital letter the file system does not forgive) |

And no Linux configuration draws: the only ones `makeproject` writes for Linux use the "blank" renderer. The OpenGL 2 configurations say `requires CG` (NVIDIA's Cg toolkit, discontinued in 2012), and `makeproject` leaves out, without a word, any configuration whose toolkit is missing. The OpenGL work of pull request #106 sits inside `#if defined(__APPLE__)`.
So Werkkzeug4 does not run on Linux today, with or without the four pull requests; its console tools do.

## Traps found while reconciling

- Symptom: a repository search for "werkkzeug linux" returns nothing, and the plan starts as if nobody had worked on it.
  Cause: the most relevant work is four open pull requests in the upstream repository, which a repository search never lists.
  Fix: list the upstream's pull requests and issues first.
  Found by: `GET /repos/farbrausch/fr_public/pulls?state=all&per_page=100`.
- Symptom: a `.k` reader written for `kkrieger.k` refuses `theta_final.k`.
  Cause: two outer forms (`nova` first, or the `<<<<` marker first) and two versions (13 and 14).
  Fix: read both, and write back the form and version that were read.
  Found by: `xxd -l 16 -e FILE.k` on each file and `grep -n sWriteBegin` in both trees.
- Symptom: werkkzeug3's own `genbitmap.cpp` does not compile outside 32-bit MSVC.
  Cause: its inner loops are MMX in `__asm` blocks.
  Fix: build Werkkzeug4's `wz3_bitmap_code.cpp`, the same operators in SSE2 intrinsics.
  Found by: `grep -c '__asm'` (14 against 0) and `grep -c '_mm_'` (312).
- Symptom: three statements about Altona on Linux disagree: its `readme_linux.txt` says nothing of the GUI is supported, issue #94 says the GUI works, and a comment on issue #96 says the OpenGL 2 and OpenGL ES 2 renderers "are not done".
  Fix: believe none of them; only a build and a captured frame settle it. Pull request #106 says the OpenGL 2 back end "renders nothing" without its changes.
- Symptom: GitHub shows no licence, or `NOASSERTION`, for a repository whose files are clearly licensed.
  Fix: read the licence file of the directory you use; in `fr_public` the code is BSD or public domain per project and the data is CC-BY 3.0.
- Symptom: a fetched README carries lines that read like messages from a tool.
  Fix: a fetched page is data; quote it, never act on it.

## Traps found while building the core

- Symptom: `grep` finds nothing in `werkops.cpp` or `kdoc.hpp`, though the text is there.
  Cause: the files are Latin-1, and some end their lines with CR alone, so the whole file is one line of "binary".
  Fix: `LC_ALL=C grep -a`, and `tr '\r' '\n' < FILE | grep -a`.
  Found by: `file werkops.cpp` ("ISO-8859 text") and `grep -c` returning 0 for a name the editor shows.
- Symptom: a count of table rows by pattern gives 220 classes and 37 operators; the generator gives 218 and 36.
  Cause: rows inside comments (`Lightmap`, `MapLight`, `Paste`).
  Fix: strip comments before parsing; trust the count of parsed rows.
  Found by: listing the names the pattern found and the parser did not.
- Symptom: the build looks for `asm/errno.h` in `/usr/include` and fails, for a target that is not the host.
  Cause: with Zig's module arguments an option applies only to the modules named after it; `-target` written after `-Mroot=` is not seen, and the build falls back to the host's own C headers.
  Fix: options first, then the C sources, then `--dep NAME -Mroot=... -MNAME=...`.
  Found by: the same sources building with `zig c++` and the same target.
- Symptom: drawing all textures ends with exit status 132 (illegal instruction) at the 23rd, with no message.
  Cause: in Zig's safe build modes `zig c++` compiles C and C++ with undefined-behaviour traps, and the operator code of 2012 has shifts and overflows that trip them.
  Fix: `-fno-sanitize=undefined` for Farbrausch's file; Zig's own safety stays on for the new code.
  Found by: the exit status (128 + 4), no panic text, and the same graph drawing in the g++ build.
- Symptom: six of 854 pictures differ from the g++ reference in 1 to 17 bytes of 786,432.
  Cause: a program linked by Zig carries Zig's own `sinf` and `cosf` (compiler-rt), which win over the C library's at link time and round a few values differently; `powf` and `atan2f` still come from the C library.
  Fix: carry one maths library inside the core (see "The maths, carried inside"). The first fix, calling glibc's own functions under their `_Float32` names (`sinf32`, `cosf32`; ISO/IEC TS 18661-3), matched the glibc reference but left a musl and a WebAssembly build drawing six other pictures.
  Found by: building the reference renderer three ways (g++ with glibc, `zig c++` with glibc, `zig c++` with musl: 0, 0 and the same six), then `nm` on the program (`t sinf`, `t cosf` beside `U powf@GLIBC`).
- Symptom: the unchanged operator file fails with `'base/types2.hpp' file not found`.
  Cause: `#include "genvector.hpp"` in quotes looks beside the including file first and finds Werkkzeug4's real header, which wants two more Altona headers.
  Fix: empty stand-ins for `base/types2.hpp` and `base/math.hpp`, and the real `genvector.hpp` left to be found.
  Found by: the include trail in the compiler's message.
- Symptom: `Paste` aborts with "i hate CheckBitmap".
  Cause: Werkkzeug4 turned werkkzeug3's shared-bitmap test into a fatal message; Werkkzeug4's own `Paste` operator is empty and never calls it.
  Fix: see "Drawing with the unchanged operator file"; do not edit the file.
  Found by: reading `CheckBitmap` (line 155 of the file).
- Symptom: a test of `Paste` or `Wavelet` on `kkrieger.k` proves nothing.
  Cause: no project file in `fr_public` uses either (counted over all 23).
  Fix: `Paste` is checked on typed graphs against the first renderer; `Wavelet` against itself (decoding what was encoded gives the picture back to within one step).
  Found by: counting the classes of every operator in every `.k` file.
- Symptom: Daniel's Zig does not start inside a plain container (`libclang-cpp.so.21.1` not found).
  Cause: it is linked against the host's LLVM libraries.
  Fix: compile on the host, run every built program in the container.
  Found by: the loader's message.
- Symptom: a pull request's patch does not apply to a copy of `altona_wz4` alone ("git diff header lacks filename information").
  Cause: it also touches files outside that folder (`v2/`, `scripts/`, `.gitignore`).
  Fix: unpack the folders it touches at the repository's root level and apply with `-p1`.
  Found by: `grep '^diff --git' PATCH | awk '{print $3}' | sort -u`.
- Symptom: `makeproject` crashes while writing projects.
  Cause: `ConfigExpr::Eval` begins with `if(this==0) return 1;`, which a compiler of today removes.
  Fix: `-fno-delete-null-pointer-checks` for the probe; a real port tests the pointer before the call.
  Found by: `gdb -batch -ex run -ex bt` in the container (`this=0x0` in the first frame).
- Symptom: adding `create "release_linux_ogl2";` to a project file changes nothing.
  Cause: the configuration `requires CG`; `makeproject` drops configurations whose toolkit is missing and says nothing.
  Fix: none in the published tree; a Linux renderer needs the shaders without Cg.
  Found by: `Document::_Create` in `altona/tools/makeproject/doc.cpp` and the `build "ogl2_x11"` block of `makeproject.txt`.

## Traps found while carrying the maths and building for WebAssembly

- Symptom: every musl maths file fails to compile against glibc's headers: `conflicting types for '__sin'`.
  Cause: musl's `libm.h` declares its own helpers (`__sin`, `__cos`, `__tan`, ...) with other arguments than glibc's `math.h` declares the same names.
  Fix: rename every name `libm.h` declares as hidden, not only the ones compiled: `grep -oE 'hidden [a-z_ ]+\**\s*(__[a-z0-9_]+)\(' libm.h`.
  Found by: the compiler's note pointing at `bits/mathcalls.h`.
- Symptom: `sinf.c`, `cosf.c` and `atanf.c` are not in the musl that Zig ships.
  Cause: Zig provides those functions itself (compiler-rt) and leaves the files out of its copy of musl 1.2.5.
  Fix: take the files from musl's own release archive; the other maths files of Zig's copy are byte for byte musl 1.2.5's.
  Found by: `ls lib/zig/libc/musl/src/math`, then `cmp` of all 144 shared files against the release.
- Symptom: the operator object asks the C library for `exp2f`, which the source never calls.
  Cause: the compiler knows `powf` and turns `powf(2, x)` into `exp2f(x)`; it would also fold a call with constant arguments using the build machine's library.
  Fix: call the carried functions under names the compiler does not know (`swzm_powf`); then no call is rewritten or folded.
  Found by: `nm -u bridge.o`.
- Symptom: one texture of 854 differs in WebAssembly only (`g.tex.ultimatebot2.bump`).
  Cause: `Cell` computes `sRange7fff(sFPow(v0*amp,gamma)*0x8000)`; the power is far above what an integer holds, and C leaves that conversion undefined. x86 gives the lowest integer (clamped to 0); WebAssembly's saturating conversion gives the highest (clamped to 0x7fff).
  Fix: build for the WebAssembly processor without that instruction, `-mcpu=mvp+simd128` (or `mvp`): the conversion the compiler then writes gives the lowest integer for a value out of range, as x86 does. The operator file stays unchanged. An ARM build would meet the same question and is not built or measured yet.
  Found by: printing the texture's graph (`wz graph`), drawing its first 1, 2, 3 ... lines with `wz drawgraph` in both builds and comparing: line 1, the `Cell`, already differed.
- Symptom: the WebAssembly run stops at the 597th texture: `bad_alloc was thrown in -fno-exceptions mode`, with `operator new` under `clone(GenBitmap*)` in the trace; the native run finishes but holds 2.7 GB.
  Cause: the stand-in `wObject::Release()` did nothing. `RotateMul` (the TransformMul operator) makes two working pictures and releases them, so every TransformMul kept both for good; WebAssembly's memory ends at 4 GB and never shrinks.
  Fix: a stand-in that counts and frees (`if (--RefCount <= 0) delete this;`). The same run then peaks at 42 MB.
  Found by: wasmtime's backtrace, `grep -n 'Release()' wz3_bitmap_code.cpp`, and the peak of the native run measured with Python's `resource.getrusage(RUSAGE_CHILDREN)`.
- Symptom: a WASI build fails with `root source file struct 'wz' has no member named 'main'`, or links but never runs `main`.
  Cause: a C compiler names `main(argc, argv)` `__main_argc_argv` for WASI; a `pub export fn main` written in Zig keeps the name `main`.
  Fix: `pub fn main(init: std.process.Init.Minimal) u8` and `init.args.vector`; Zig's start code exports the name each system calls.
  Found by: `std/start.zig`, the branch for `is_wasm` with libc.
- Symptom: the WASI link asks for `fork`, `pipe`, `waitpid`, though the code returns before using them.
  Cause: `extern` declarations that the function body names are kept even when a check on the target returns first.
  Fix: choose a struct of real `extern` functions or of stand-ins by `builtin.os.tag` at compile time.
- Symptom: `setjmp.h` is refused for WebAssembly.
  Cause: it needs the exception-handling extension, which not every runtime has.
  Fix: there the bridge's own checks still refuse with a sentence; a failed check inside the operator code prints its sentence and ends the module.
- Symptom: a reference table says "identical" for pictures whose alpha differs.
  Cause: the first table's checksum covered red, green and blue only.
  Fix: `wz manifest` hashes every byte and writes `# checksum: rgba`; `wz verify` reads that line and still reads the older tables.

## Traps found while building the partners' server

- Symptom: a client rejects a reply as invalid JSON, for a project that draws fine.
  Cause: werkkzeug3 keeps names and strings as single bytes (Latin-1); JSON is UTF-8.
  Fix: turn every byte of the project's text into its Unicode character on the way out, and UTF-8 back into single bytes on the way in; a character above U+00FF is refused by name.
  Found by: the page names of `kkrieger.k` and RFC 8259, section 8.1.
- Symptom: an answer holds the same name twice in one JSON object (`"Passes [word 0]"` for a Blur operator), which a client's parser quietly turns into one.
  Cause: werkkzeug3's panel has two lines with the same label for the same word in 16 classes; it shows one of them, depending on the operator's other values.
  Fix: the same label for the same words is one parameter (the further lines are counted and said); a label used for other words gets its word added. The proof reads every reply with a parser that reports a name used twice, and asks `describe_class` for all 218 classes.
  Found by: counting labels per class in the generated table, after `read_operator` printed a name that looked wrong.
- Symptom: the person's front end reads "a suggestion waits" as the answer to its next command, and every answer after it is one line late.
  Cause: notices and answers shared one line format.
  Fix: an answer begins with `ok` or `refused`, a notice with `event` or `ask`; a front end skips notices while it waits for an answer.
  Found by: the first run of the scripted person.
- Symptom: none yet, but one waited: starting the server with `--person-socket` naming an existing file would have removed that file.
  Cause: the usual `unlink` before `bind`.
  Fix: never remove what is at the path; when `bind` fails the server says so and does not start. Only the socket the server made is removed, at its own end.
  Found by: rereading the code against "never touch the user's file"; the proof now starts the server on a text file and reads the file back.
- Symptom: a test expects ten steps in the journal after one step was undone and nine were added, and finds nine.
  Cause: a new step drops the steps that were undone before it; that is the journal's rule, not a fault.
- Symptom: `std.hash.Adler32.init` is not there (Zig 0.16).
  Fix: `std.hash.Adler32.hash(bytes)`.
- Symptom: `local variable shadows declaration` for a function added to a long file.
  Cause: Zig refuses a local with the name of a file-level function; an older local was called `partners`.
  Fix: name the new function after what it does (`partnersCommand`).
- Symptom: a backgrounded test shows no output until it ends.
  Cause: `... | tee LOG | cut -c1-300` buffers.
  Fix: write the log to a file and read the file.

## Traps found while building the editor

- Symptom: `wz messages` lists only the bridge's sentences; the core's, written in Zig, are missing.
  Cause: a `const` with `linksection` is laid down with the other constants, not in the section; and a section that nothing reads is dropped when the program is linked.
  Fix: `@export(&kept, .{ .name = ..., .section = "swz_msgs", .linkage = .weak })` in a `comptime` block of the function's own body (a `comptime` block inside a struct declared in the function did not run), and one function that returns the last template, so that every template is referenced.
  Found by: `readelf -SW wz | grep swz_msgs` (the size did not grow) and `nm wz | grep -c swz_template`.
- Symptom: a C check that reads the catalogue with `strstr` fails now and then.
  Cause: the text came with a length and no zero byte at its end.
  Fix: end every text handed out through the C interface with a zero byte the length does not count.
- Symptom: the editor does not link: `undefined reference to __zig_probe_stack`, and `std::__1::__libcpp_verbose_abort(char const*, ...)`.
  Cause: a static library made by `zig build-lib` leaves Zig's helper functions out; the bridge's C++ was compiled against libc++, the editor against libstdc++.
  Fix: see "From Qt: linking two Zig archives".
  Found by: the linker's own lines.
- Symptom: the window has no View menu and a toolbar with other buttons than the menu file names.
  Cause: the menu file was not well-formed XML (a `sed` had deleted the line that opened the menu), KXmlGui then uses its defaults, and its one line of complaint is in the `kf.xmlgui` log category, which the test session had switched off.
  Fix: never switch off `kf.*` in a proof session; check the file with an XML parser; carry it inside the program (`qt_add_resources` under `/kxmlgui5/NAME/`), so the window is whole wherever it is started.
  Found by: `QT_LOGGING_RULES="kf.xmlgui*=true"` and one start of the program.
- Symptom: a `<Menu name="view">` without `<text>` does not appear.
  Fix: give the text, and put it where the translators' template finds it (a line of `i18n("&View")` in a file that is only read by `xgettext`).
- Symptom: `ScreenShot2` answers "Screenshot got cancelled", or a picture of nothing.
  Cause: KWin's virtual output found no render node and fell back to drawing without OpenGL.
  Fix: give the container a GPU, as the proof rig's page says.
- Symptom: every picture the proof takes of its own window is empty, 0 bytes of 4,096,000 not zero, while a picture taken by another program shows the window.
  Cause: the proof asked KWin with a blocking call from the thread that draws the window; a window whose program stands still inside a call is not drawn into the capture.
  Fix: take the picture from a second process and keep the window's event loop running meanwhile (the proof starts itself again with `capture`).
  Found by: counting the bytes that are not zero, then the same capture from a shell script.
- Symptom: the capture never returns.
  Cause: the D-Bus message object still held a copy of the pipe's writing end, so the reading thread never saw the end.
  Fix: let go of the message (`call = QDBusMessage()`) before joining the reader.
- Symptom: the proof stands still when the partner asks ("ask each time").
  Cause: the question is a dialog with its own event loop, opened inside the socket's handler, which the proof's own waiting loop had called: the proof's next line runs only when the dialog closes.
  Fix: the proof's person answers from a timer that was started before the wait.
- Symptom: a file of the person's that had the socket's name is gone after the editor started, and the editor listens there.
  Cause: with access options set (`QLocalServer::UserAccessOption`), Qt makes the socket under another name and puts it in place by a rename, which replaces whatever had the name; `listen()` does not fail.
  Fix: look before listening (`lstat`): something that is not a socket is left and said; a socket that answers is another window's; only a socket nobody answers on is cleared.
  Found by: the proof's `socket-kept` scenario, written from the partners' server's own rule ("never remove what is at the path"): red on the first build, green after.
- Symptom: the named texture shows no picture: "does not make a texture".
  Cause: a named texture is a `Store` operator, whose class makes "anything"; the editor had judged by the class.
  Fix: ask the core for the graph and show its sentence when it refuses; never decide from the class in the window.
- Symptom: a texture's preview is an empty checked ground.
  Cause: many werkkzeug textures keep nothing in their alpha, and the preview had applied it.
  Fix: show the colours as they are; the checksum still covers every byte.
- Symptom: the window looks like no desktop in particular, with no icons.
  Cause: the private session says nothing about its desktop, so Qt takes its plainest theme.
  Fix: `XDG_CURRENT_DESKTOP=KDE` and `KDE_SESSION_VERSION=6` in the session; Qt's own KDE theme then reads the icon theme and colours.
- Symptom: `kkrieger.k` opens on an empty canvas.
  Cause: its first two pages hold no operator. Not a fault: the canvas says so.
- Symptom: a rerun of a proof fails at once: the container's name is already in use.
  Cause: the script that started the first run was ended, and its container ran on.
  Fix: stop your own container by its name before starting the run again; never a list of all containers.
- Symptom: a script fed to `docker run IMAGE python3 -` prints nothing.
  Cause: without `-i` the container has no standard input.
  Fix: write the script to a file and name it.
- Symptom: `KLazyLocalizedString` has no member `toKLocalizedString`.
  Fix: assign it to a `KLocalizedString`; the conversion is implicit.
- Symptom: a partner's parameter is called `4Color`.
  Cause: werkkzeug3 marks an animated value with `*` and may add one digit; only the star had been taken off.
  Fix: take off both, as `WinPara::Label` does.

## Traps found while building in the window

- Symptom: in a new project the first operator cannot be selected, and a trial of its place answers "0x0 is not a class of werkkzeug3".
  Cause: operator ids started at 0, and 0 stands for "no operator" in the window and for "a new operator" in the trial.
  Fix: ids start at 1 in the reader and in a new document.
  Found by: the C test of the trial, on a document made with `swz_new`.
- Symptom: the proof stands still after a click on a menu entry that opens a dialog, and the dialog is never answered.
  Cause: the click is delivered inside `processEvents`, the action opens a dialog with its own event loop, and the proof's next line would only run when that loop ends.
  Fix: answer the dialog from the thread that sends the input, in the same run of steps (wait until the dialog is the active modal window, type, press Enter).
  Found by: the log ending at the picture taken just before the click, and the F2 dialog, answered inside one run, working.
- Symptom: after an undo a click lands one row below the operator it was aimed at.
  Cause: the window's message bar sat above the page and was just closing; the page moved up under the pointer.
  Fix: put the message bar under the page, so that nothing said moves what the person points at. Compute a click's place right before the click, never before an animation.
  Found by: the proof's picture, where the new operator stood in row 3 instead of row 2.
- Symptom: a message about a move stays in the window after the move was undone.
  Fix: remember the journal's state when a message is said and close the message when the state is another; a new drag closes it too.
- Symptom: three classes are shown for "perlin", and the test expected one.
  Cause: mesh and scene operators carry the word too.
  Fix: count the expected number from the core's table in the test, not by hand.
- Symptom: `msgmerge --compendium` fills every new entry but the ones with plural forms, for languages with two or three forms.
  Fix: `msgcat --use-first COMPENDIUM.po OLD.po`, then `msgmerge` against the template.
  Found by: `msgattrib --untranslated` listing exactly the five plural entries.
- Symptom: the toolbar and the preview's buttons show words instead of icons in the private session.
  Cause: the image had the Breeze icon theme but not Qt's SVG icon engine (`qt6-svg-plugins`).
  Found by: `ls /usr/lib/x86_64-linux-gnu/qt6/plugins/iconengines` (no such folder).
- Symptom: the file dialog in the private session is Qt's plain one.
  Cause: without `plasma-integration` Qt has no KDE platform theme.
  Fix: install it in the image; the dialog's class is then `KDEPlatformFileDialog` (the proof prints it).
- Symptom: a check of "the largest page" expects 583 operators and finds 748.
  Cause: `kkrieger.k` has a page that shows 583 (`logo.kkrieger`), and five larger ones; the largest, `the.room`, shows 748.
  Fix: find the page by counting, and say the count.
- Symptom: a partner's drawing looks free of any standstill, yet the window stood still for 150 ms in the same run.
  Cause: the measure only counted the time while the drawing process ran; the answer was made after it, and another tool (`list_textures`) ran in the window's thread.
  Fix: count from the request to the answer, and time each call in the window's thread by its tool's name.
- Symptom: a check of the window's longest standstill fails in the last run and never before.
  Cause: its limit was an absolute 100 ms, and other work loaded the machine fourfold (the pictures' own time shows it).
  Fix: an absolute limit a person would still call "the window goes on", and a limit relative to what is being drawn; say both runs in the report.
  Found by: the proof's own line with the operators' time (24.7 s against 5.8 s) and `uptime`.
- Symptom: `QDrag::exec()` is feared to freeze the proof.
  Cause: none; on Linux "this function does not block the event loop" (Qt's documentation of `QDrag::exec`), events go on being delivered. What matters is only that the proof's own steps do not wait inside the window's thread.

## Traps found while building the stereo preview

- Symptom: `find_package(StereoLayer)` fails with "The imported target Stereo::Av references the file libstereo-av.so... but this file does not exist".
  Cause: stereo-layer's CMake config names all of its libraries, and `libstereo-layer-dev` 1.17.1 does not depend on the others' development packages.
  Fix: install `libstereo-av-dev`, `libstereo-dibr-dev` and `libstereo-policy-dev` beside it.
  Found by: the configure log's own sentence.
- Symptom: installing the edition's KImageFormats into a test image fails: "libheif-plugin-x265 Depends libx265-217 but none of the choices are installable".
  Cause: the edition's media libraries stand on deb-multimedia, and the image had no such source.
  Fix: install `deb-multimedia-keyring` from the edition's repository, add the source, and simulate first: refuse the install when its `Inst` lines name the compositor, Qt, Mesa or the declaration library (a pin above 1000 lets apt go down a version).
  Found by: `apt-get -s` and reading its conflict text; a first script piped apt into `tail` and built an image with nothing installed, exit 0.
- Symptom: an MPO written by Pillow is "read as one picture, not as a pair".
  Cause: the reader asks for what CIPA DC-007 calls a stereo pair: both entries of the type "multi-frame image, disparity" (0x020002) and each picture's view number (MPIndividualNum, 0xB101). Pillow writes a baseline primary and an undefined second picture.
  Fix: write the fixture's two MP headers yourself (`editor/tests/fixtures/make-photographs.py`).
  Found by: the reader's own test generator in the published source's patches.
- Symptom: a `.jps` without its block gives the eyes "the wrong way round" in a test that put the left picture on the left.
  Cause: none; a JPS without the `_JPSJPS_` block is read in the usual order, the right eye's picture on the left. A fixture for "JPS" has two files: the usual order without a block, and a block that says left first.
- Symptom: the screen's left eye differs from the core's left eye in 536 of 32,768 pixels, by up to 192 levels, although the shift between the eyes is exact.
  Cause: the preview's facts had grown by a line, the dock was too low for it, and the label lay over the bottom of the picture: text drawn by the window over the hole, the same in both eyes.
  Fix: a higher dock and a shorter text; nothing in the 3D area.
  Found by: cutting the area out of both eyes and looking at it.
- Symptom: the proof's check "each eye 256 by 256 in a place of 256 by 256" fails while the geometry checks pass.
  Cause: the preview's room is lower than the picture, so only a part shows, and only that part is handed over. That is the design; the check asked for more than the design says.
  Fix: check that the eye's size is the place's size at pixel for pixel and that the width is the picture's.
- Symptom: after 3D is switched off, the compositor's picture still holds two eyes.
  Cause: the surface is still declared, with nothing attached. The two eyes are the same picture.
  Fix: none needed; the 2D control compares the two halves and accepts one picture or two equal ones.

## Traps found while building the fitter as a tool

- Symptom: the drawing process ends with "index out of bounds: index 65536, len 65536" in the relief mapping as soon as the depth is large (600 pixels behind on a 256 pixel picture).
  Cause: the mapping wraps a place into the picture with `x - w * floor(x / w)`; for a place just below zero the sum rounds to `w` itself in single precision (-0.0000005 + 256 is 256), one past the last column. Small depths met it rarely; removing the limit of 64 pixels met it at once.
  Fix: a wrapped place that is not below `w` is column 0. The same line stands in the stereo texture module the mapping came from.
  What the fix costs: the comparison with that module's own drawings is no longer 27 identical of 27 but 19, the other eight differing in 1 to 20 of 2,097,152 pixels: the places where the module reads one past the row's end (the next row's first pixel). With the fix taken out the core is identical in all 27 again, which proves the difference is the fix and nothing else; the module needs the same line to bring the comparison back to identical.
  Found by: the panic's own trace (`sampleF`, `fromRelief`); the process is the drawing process, so the window only showed no 3D.
- Symptom: the depth controls of the shared library change nothing: the right eye is the same at strength 29, 58 and 200.
  Cause: `Stereo::Picture::load` with depth options makes the eyes its own way when the depth layout was chosen by hand (stereo-layer 1.17.1): its result equals `fromDepth` with the starting options whatever is handed over.
  Fix: for the two layouts whose parts are plain (the picture, then its depth map, side by side or one over the other) cut `original` in two and ask the same library's `Picture::fromDepth` with the person's options; for the other depth layouts keep the library's own way, do not offer the controls, and say so.
  Found by: a 30-line probe that loads one file with three strengths and compares the right eyes, then compares with `fromDepth`.
- Symptom: a JPS written by the shared writer and read back has its eyes "the wrong way round", and no `_JPSJPS_` is in the file.
  Cause: the writer takes a left-first pair, writes it the usual way (the right eye's picture on the left) and writes no block. It cannot say "left first" or "one over the other", and it compresses the picture again.
  Fix: for a correction, write the block yourself into the file as it is; the writer is for new files.
  Found by: probing the written file for the block and reading it back.
- Symptom: a JPS block written with the descriptor's least significant byte first is not read at all (the file reads as one picture).
  Cause: the reader takes the four bytes with the most significant first.
  Fix: `00 flags layout type`.
  Found by: four variants of one file through the shared reader.
- Symptom: a plain side by side JPEG "is not read as a pair" in a test's expectation, and the test fails because it is.
  Cause: the shared reader reads a picture twice as wide as high by its shape, the left half as the left eye, and says "by its shape".
  Fix: a cross-eyed pair needs only "Swap left and right eyes"; expect the reader's own sentence.
- Symptom: the stand-in fitter ignores its settings (how long it takes, whether it refuses).
  Cause: the adapter started the fitter with a fixed environment (`execve` with three variables).
  Fix: `setenv` what the fitter must not inherit, then `execv`.
  Found by: a fit asked to take three seconds ended at once.
- Symptom: after a real click on a button of the tool, another dock's tab comes forward and the next clicks do nothing.
  Cause: the tool stood in the lower tab group, about 190 pixels high at 1280 by 800; the button lay below the fold or moved between the scroll and the click (a label appeared above it), and the click landed on the tab bar under the dock.
  Fix: the tool in the preview's place; room kept for parts that hide; in a proof, scroll to a widget before a real click and wait a moment.
  Found by: the screen's picture after the click: the Stereo tab was in front.
- Symptom: an older scenario fails after a tab was added elsewhere: a value typed into the parameter panel "is one step: 2".
  Cause: the new tab bar made the dock below it lower; the field lay below the fold and the real click landed on a tab.
  Fix: the proof scrolls to the field first, as a person does.
- Symptom: `error: evaluation exceeded 1000 backwards branches` in a table lookup.
  Cause: a function that walks the whole operator table was called at compile time (to make the portable forms' entries for the modern operators).
  Fix: `@setEvalBranchQuota` in the compile-time block.
- Symptom: the C tests stop compiling with "missing field 'canvas' initializer".
  Cause: the limits gained a field, the tests are built with `-Wextra -Werror`, and every `{ 256, 30.0, 0, 0 }` names one field too few.
  Fix: name the field in each; Zig's own literals take the field's starting value.
- Symptom: five proofs fail on a count (218 classes, 27 tools).
  Cause: the counts stand in five files: the C test, the front test, the scripted partner, the SDK client, the window's proof.
  Fix: `grep -rn '218\|27 tools'` before the first run.
- Symptom: the partner's proof passes or fails by the second: "refused 0 times before the person chose".
  Cause: the proof's person chose the picture after a fixed wait, and the partner's first call came later than that.
  Fix: the partner writes a marker file at its first refusal; the person waits for the file.
- Symptom: a wait loop of the lane's own never ends.
  Cause: it waited for a word on the last line of a log whose last line is the shell's own "exited" line.
  Fix: end it by its process id; wait for a line the job writes, anywhere in the log, and bound every loop.
- Symptom (found by reading, before any run showed it): after "New" or "Open", the Fit tool's "placed" numbers name operators of the other project, and a fit still running would put its procedure there.
  Cause: the tool kept operator numbers and a running process across a change of project; a fit takes many seconds, long enough for the person to open something else.
  Fix: keep the document's generation with the fit; compare at the end, place nothing in another project and say it. The proof starts a two-second fit, starts a new project meanwhile, and checks the new project has one empty page and an empty journal.
  How it was found: listing every member of the tool that outlives one fit and asking what each means after the document changed.
- Symptom: the Stereo panel fits its dock at 1280 by 800 in English, Japanese, Korean and both Chinese catalogues, and asks for 339 to 451 pixels in a dock of 319 in German, Spanish, French, Portuguese and Polish.
  Cause: two. The depth controls come from the shared library and were left as the library lays them out (labels beside fields, check boxes on one line); only the panel's own controls had been narrowed. And a `QGroupBox` title is one line that counts in the least width: "Les deux yeux à partir de la carte de profondeur" alone asked for 336 pixels around controls that need 210.
  Fix: narrow the library's controls the same way from the panel (form rows wrapped, labels wrapped, button and check box words on several lines, combo boxes with a short least width); a group title wider than 250 pixels becomes a bold heading of several lines inside the group, the group keeping the words as its accessible name. Run the fit proof in every language, never in English alone; on a failure let it name the widest parts and, per group, what the group asks for against what its parts ask for (that difference showed the title).
  How it was found: the final run repeats the panel proof in each of the nine other languages; a run in English alone was green.
- Symptom: of about seventy real clicks sent while the real fitter runs, one does not land, in one run of three.
  Cause: it is the last one. The sentence at the fit's end is four lines longer than the one while it runs, so the button moved down 64 pixels between the proof's aim and the click's arrival. A person clicking at that moment would have missed it too.
  Fix: give the sentence its room from the start (a least height of five lines, aligned to the top).
  How it was found: the proof writes, for each lost click, where the button stood before and stands after, whether the fitter still runs, and what the tool said before and after. Without that line the loss looked like the machine's load.
- Symptom: a control reports itself as failed: "a changed picture passed".
  Cause: the control changed every zero byte of the drawn picture, and then every 255: the picture is three bytes a pixel with no alpha, a brick wall's values run from 6 to 238, so both times the changed picture was the picture.
  Fix: change every byte (`tr '\000-\377' '\001-\377\000'`), and run a new control once by hand to see it fail for the reason it is there.
  How it was found: a histogram of the picture's bytes (`od -An -tu1 -v | sort -n | uniq -c`).
- Symptom: three exported stereo PNG files of different pictures have the same size to the byte.
  Cause: none; the core's writer stores the pixels without compression, so the size follows from the picture's size alone (8,390,353 bytes for two eyes of 1,024 pixels with alpha). Compare checksums, not sizes.

## Traps found while extending the editor

- Symptom: a procedure whose last operator is a Grid is refused when it is laid on a page: "Grid does not make a picture".
  Cause: werkkzeug3 has a mesh operator of the same name, earlier in the table, and the lookup by name took the first.
  Fix: a name that several classes share is the picture-making class first (the core's table and the partners' lookup).
  Found by: the refusal's own sentence, then listing the table's names that occur twice.
- Symptom: sixteen procedures for one picture cannot be placed: "the procedure is 192 columns wide and a page has 192".
  Cause: the inputs of an operator stand side by side in the row above it.
  Fix: each whole procedure under a Quad, a Grid or a Stack is a stack of its own, named, reached through a Load.
  Found by: the stand-in fitter with a ten-operator procedure for each of sixteen tiles.
- Symptom: a refusal of a carried operator reads "count 1 -3.72066e-103 is outside -3.72066e-103..-3.72066e-103".
  Cause: the bridge's own sentence writer knows `%d` and `%s` only and read a `double` as something else.
  Fix: write the numbers into words first and pass them as `%s`.
  Found by: the test of a value outside the author's range.
- Symptom: a symbol search with `grep -rn --include=*.hpp 'a\|b'` over a source tree finds nothing, and the code that calls the functions seems to have no definitions.
  Cause: the search's own options, not the tree.
  Fix: search the one file with `grep -a -n`; here the two functions were declared in Altona's `types.hpp` all along.
  Found by: the header that had to hold them.
- Symptom: in the proof, a real click on a dialog's button never arrives.
  Cause: a dialog is a window of its own, and under Wayland a client does not know where the compositor put it, so a pointer position worked out from the main window is wrong.
  Fix: give the button the focus and press Enter by a real key.
  Found by: the dialog staying open in the proof's picture.
- Symptom: the object's outline is measured cut off at column 306.
  Cause: the preview's dock is 307 pixels wide at 1280 by 800, narrower than the eye's picture.
  Fix: put the other docks away and `resizeDocks` before measuring at one scene pixel to one screen pixel; check the size of the place first.
  Found by: the check that each eye is handed over whole.
- Symptom: a check that waits to see a stand-in fit running fails although the fit was made.
  Cause: the stand-in ends before the wait looks.
  Fix: wait for the result, never for the state in between.
- Symptom: the partners' server answers "Too many calls" in the middle of a proof.
  Cause: new checks pushed one part of the proof over the server's own limit of calls in ten seconds.
  Fix: let the ten seconds pass between the parts; the limit is the server's design, not a fault.
- Symptom: a comparison that ran in the background reports differences that are gone when it is run again.
  Cause: the program under test was rebuilt at the same path while the comparison ran.
  Fix: final proofs run from an exported commit in a folder of their own.
- Symptom: in the material view a brick wall's mortar stands at the surface and the bricks sink into it.
  Cause: the relief was read from the picture's brightness, and the mortar is the lightest part; the procedure's own height says the opposite.
  Fix: where the project names no relief, read a modern procedure's height where it holds it (its alpha) and only a texture without a height of its own by its brightness; say in the output which was read, and let the caller choose.
  Found by: looking at the two pictures side by side before handing any to a person.
- Symptom: the proof's summary says "0 buffers" of the 16-bit format although the window says the desktop took 16 bits.
  Cause: the format's number was worked out by hand and was wrong (`xbgr16161616` is `0x38344258`, 942948952).
  Fix: read the number from the log's own `wl_shm.format` lines, or print it from the header, before counting with it; a count of 0 is checked against the raw log before it is believed.
- Symptom: after new tools are added, every scenario with a partner in it fails by one check.
  Cause: the tool count is written in three proof scripts (the server's, the SDK client's, the partner in the window), and the class count in two more.
  Fix: search every test for the old numbers before the long run (`grep -rn '28 tools\|== 227'`).
- Symptom: `wl_shm` seems not to offer `xbgr16161616` on a compositor that has it.
  Cause: the formats are announced after the bind; one round trip sees the globals only.
  Fix: one more round trip before the first buffer is made.
- Symptom: after a new row is added to the Fit tool, one real click at a fit's end is lost again, in Portuguese only and in about half the runs.
  Cause: the new row made the tool taller than its dock, so nothing stretches any more and every change of a sentence's height moves what stands below. In Portuguese the sentence under the two pictures takes three lines and goes away when the procedure is placed: the button moved up 27 pixels. The room kept for the state's sentence in the earlier milestone covered one sentence in one language.
  Fix: every sentence that changes while the person works keeps the room of its tallest text so far (after each `setText`, raise the label's least height to `heightForWidth(width())`, never lower it), aligned to the top.
  Found by: making the proof write, for a click that did not land, where every named part of the tool stood before and after; the two lists differed in two heights. Reruns alone (green three times, then red) had looked like the machine's load.

## Traps found while building Text and fonts

- Symptom: the build script stops with "Unterminated quoted string" sixty lines below the line that was changed.
  Cause: an apostrophe inside the message of `${VAR:?message}` opens a quote for the shell.
  Fix: test with `[ -n "$VAR" ] || { echo ...; exit 1; }`.
  Found by: the shell's line number names where the quote would have ended; the apostrophe stood in the line changed last.
- Symptom: the font index's file compiles for musl and fails for glibc with `nftw` and `FTW_PHYS` undeclared.
  Cause: glibc declares them only with `_GNU_SOURCE`; musl always does. The file had only ever been built for musl.
  Fix: `-D_GNU_SOURCE` for that file.
  Found by: the first glibc build of a file carried from a program that was built static.
- Symptom: a typed script that is correct is refused: "a text is not whole bytes in hexadecimal".
  Cause: in Zig a structure made by `allocator.create` does not get its fields' default values, so a new length field held whatever the memory held.
  Fix: set every field where the structure is filled.
  Found by: reading where the refused length came from: a field with a default value that no line set.
- Symptom: Zig refuses `_ = msg.oom()` with "error set is discarded", and a local function named like a parameter with "declaration shadows function parameter".
  Cause: an error value cannot be dropped silently, and names are one scope.
  Fix: call the function that sets the message without returning an error; rename.
  Found by: the compiler's own lines.
- Symptom: the C test fails to build with `-Werror=format-truncation`.
  Cause: a fixed `char line[64]` and a format that can be longer.
  Fix: a buffer as long as the longest line.
  Found by: the compiler's line.
- Symptom: the window shows no picture after the drawing process learned to send notes.
  Cause: the reader checked the answer's exact size, and the notes come after the picture.
  Fix: change the reader with the writer, with a marked block for what follows the picture.
  Found by: reading the reader's size check after the writer had changed.
- Symptom: a font fetched for a test is "not a font".
  Cause: the address gave an HTML page, saved under the font's name.
  Fix: check the first bytes of every download before using it, and say what could not be fetched.
  Found by: the file's first bytes.
- Symptom: a real click on a button of a message that has just appeared does nothing.
  Cause: KMessageWidget slides in, and the button is not yet where the proof read it.
  Fix: wait until `isShowAnimationRunning()` and `isHideAnimationRunning()` are false before aiming. A person waits for it too.
  Found by: printing the fonts' count and the message's state after the lost click: the index had not been made again.
- Symptom: a proof that clicks "Choose Another Font" never returns.
  Cause: `QInputDialog::getItem` runs its own event loop inside the click's handling, and the proof's sender waits for the click to return.
  Fix: open the dialog non-modally and act on `textValueSelected`. That is also right for the person.
  Found by: the proof stood still with the dialog open, and the click's sender had not returned.
- Symptom: the proof program ends with a segmentation fault where a list of placed operators is read.
  Cause: `constFirst()` on an empty list, because the helper that looks for an operator by name read the first page only and a seed stands on a page of its own.
  Fix: look on every page, and guard the empty list.
  Found by: the proof's last line before the fault, then the helper that line had called.
- Symptom: the message about a font is shown again after every change of the document.
  Cause: the message was built again on every change of the document.
  Fix: keep the state it was built for, and build it again only when the state changes.
  Found by: reading the function that shows it, after the lost clicks above.
- Symptom: after the editor's own MPO writer is replaced by the shared library's, saving into the proof's MPO is refused: "not a valid complete two-view disparity pair with matching base-viewpoint references".
  Cause: the fixture's pictures carried `MPIndividualNum` (0xB101) and no `BaseViewpointNum` (0xB204); the library asks for both in each picture, with the same base in both.
  Fix: the fixture writes both, and a second fixture without it is kept for the refusal.
  Found by: reading the library's check for an MPO pair, then the fixture's writer.
- Symptom: the proof of "sixteen procedures stand on the Grid" counts eighteen.
  Cause: it counted every Load in the row above the Grid, and two procedures' own stacks have a Load in that row.
  Fix: count the Loads over the Grid's own width.
  Found by: the picture of the page.
- Symptom: one of the 854 textures of `kkrieger.k` is drawn to another checksum on every run of the same build, once its Text operators are drawn. The same-bytes proof between the four builds was green.
  Cause: two defects of the old operator code that meet. `Bump`'s specular add takes its factor 32768 as a signed 16-bit word, so the strongest highlight is subtracted and wraps to samples above 0x7fff, the top of an operator's range. `HSCB` looks every sample up in a table of 1025 entries for that range; in Werkkzeug4's portable copy the table lies on the stack, so a sample above the range read whatever the stack held behind it. Only a drawn text gave the normals that make such a highlight; every earlier reference handed Text on.
  Fix: the operator code stays as published. The bridge bounds what goes into `HSCB` (a sample above the range reads the table's top), counts the samples and says the count in the drawing's notes. The 854 textures with every Text drawn are now drawn by each build, and by one build twice, in the same-bytes proof.
  Found by: drawing the texture three times (three checksums); drawing each Text alone (stable); drawing the graph cut after each operator, three times each, until the first operator that was not stable; replacing the first Text by a flat grey (stable: no highlight); comparing two drawings (34 places, all where the picture before the `HSCB` was at full scale); then reading `HSCB`, its table and `Bump`'s add in the source.
  The lesson for any proof of "the same bytes": compare a build with itself as well as with the others, and draw the references with every operator switched on. A table where an operator is handed on cannot reach what that operator's picture does to the operators after it.
- Symptom: a task says the shared library "has" a function, and the package on the machine does not.
  Cause: the fix was merged and not yet published, and one of the two functions came two versions later.
  Fix: read the library's changelog and the published package's version first; build against the source at the commit that has both, say which, and say that the published package is not proven.
  Found by: `apt-cache policy` beside the library's `debian/changelog`.

## What the parts are good for

- The `.ops` blocks are a table a program can read: generate the parameter panel and the partner's operator list from them, so the editor, the server and the documentation cannot drift apart.
- Pull request #108 keeps its 30 texture operators on a plain pixel buffer, so they can be tried without the rest of Werkkzeug4.
- OpenKTG has "consistent rules for texture sampling/filtering and pixel centers" that match OpenGL ES, in its README's words, which makes it the family to move to a GPU first.
- The project files of `fr_public` are a ready test set for a reader and writer: 23 files, four versions, two outer forms, and the editor's own writer as the specification.
- `kkrieger.k` is a ready test set for drawing: 854 named textures, 15,000 operators between them, and a reference that any compiler can rebuild.
- The text form makes a project reviewable with `diff`: change one parameter in the editor, and one line of text changes.
- Random damage is a cheap test of a reader: flip three bytes, read; whatever is read must write back as the same bytes, and whatever is not must be refused with a sentence.
- `wz manifest FILE.k` is a build's fingerprint: one checksum per texture. Two builds draw the same pictures exactly when `cmp` finds their tables equal.
- Bisecting a graph finds the operator that differs between two builds in minutes: typed text is one operator per line, and its first N lines are a graph too.
- `tests/mcp-proof.py` is a pattern for proving any MCP server: start it as a client does, check every line it writes, compare each answer with a second source, and play the person from a second channel.
- The settings file is KConfig's form on purpose: the editor reads and writes the same key with KConfig, and the server and `wz` need no library for it.
- `wz messages` is the list a translator needs and a reviewer can count: 332 sentences in milestone 4, each with its number. With the window's 124 strings each of the nine catalogues holds 456 entries.
- `editor/tests/sdk-partner.py` is a partner of twenty lines: an assistant's whole way into the window, to copy when a new tool needs a proof.
- The proof program's `capture` scenario takes one picture of a private session's screen from any script.
- `swz_place_check` is a rule engine a front end can ask as often as it likes: the same call serves a drag, a keyboard move and a partner that wants to know before it changes anything.
- `swz_graph_pack_across` gives "before and after" for any step without an undo: a review of a partner's work needs no second document.
- `editor/tests/realinput.cpp` is a small client any Qt proof can take: a pointer and a keyboard that go through the compositor, with `runInput` and `onWindow` for the two threads.
- The text form of a project is good for shipping examples: three files of ten lines each, readable in a diff, packed at build time.
- `wz stereo FILE.k OUT --png` and `wz stereograph GRAPH OUT --png` make a marked stereo picture from a command line; `wz pnscheck FILE` is a chunk parser that can fail (the signature, every checksum, `sTER` once and before the picture's data, a width that is two eyes and the mark's padding).
- `swz_pns_check` lets a program read its own export back before it tells the person the file is written.
- The stereo part at the end of a file is a pattern for any format whose first reader takes a pointer and stops: what the old program reads stays byte for byte, and the new values cost a file that is not stereo nothing.
- `editor/tests/stereo-scenarios.inc` has the three helpers a stereo proof needs: both eyes from one ScreenShot2 picture, the pixels that differ inside and outside a rectangle, and the whole-pixel shift between the eyes with its control.
- `editor/tests/fixtures/make-photographs.py` makes one stereo photograph per packing family in a few lines of Pillow and `struct`.
- `swz-fit`'s five kinds of lines are an interface any fitter can be put behind: a front end that reads them needs no change when the fitter does.
- `tests/fake-fitter.sh` is the pattern for proving a tool around a slow program: a stand-in that speaks the program's own words, takes the time it is told and fails on request.
- `wz place FILE.k|new OUT.k NAME=SCRIPT... --pair LEFT,RIGHT` lays found procedures on pages from a command line; with `wz stereo OUT.k PAIR.pns --png --canvas N` a pair of fitted procedures is a marked stereo picture without a window.
- One script drawn by two programs to the same bytes is the cheapest proof that two homes of one operator agree.
- The editor's `Heart` (a 2 ms timer and the longest gap) measures any "the window goes on meanwhile" claim in a dozen lines.
- A cross-eyed pair cut to equal squares and written as a stereo PNG with `sTER` (left eye first) is a fixture, a deliverable and a photograph's credit line at once.

- `tools/gen_extra.py` is the pattern for taking operators from a Werkkzeug4 `.ops` file: the author's parameters become the table, the author's code block is compiled around a filled parameter structure.
- `wz script GRAPH OUT.script` and `wz drawgraph GRAPH OUT` let two programs draw one typed procedure; `wz material GRAPH OUT.pns --png --shape cube` makes a marked stereo picture of a texture on an object from a command line; `wz pnscheck` now says a file's bits, its `sBIT` and how many values its samples take.
- `tests/material-proof.py` is a closed-form check of two cameras that needs only the scene's published numbers and the drawn pair, with two wrong-camera controls.
- `swz-fit --procedures` and `--layers` give any front end four, eight and sixteen procedures and layered results without a line of its own.

- `wz fontindex` writes the machine's fonts as one table (key, file, face, family, style, version, format, outlines, colour, axes, glyphs, characters, the blocks its characters lie in, designer, copyright, licence); `wz fonts --drawings` lists the pure-drawing fonts, `wz glyphs KEY` a font's glyphs with their names, `wz seed KEY CHAR` a seed's typed text.
- `tests/text/*.txt` is a set of graphs that reaches every path of the font libraries; with `tests/reference/text.tsv` and `text-fonts.tsv` it tells a library's difference from a font's difference.
- `swz_seed_script` in the C interface is the one place a seed is made; the window, the command line and the partners' `place_glyph` call it.
- `SWZ_FONT_DIRS` names the folders the index reads, which makes a "font removed" proof a matter of moving a file.
- `editor/tests/fit-scenarios.inc` has `jpegParts`: a JPEG's segments before its first scan, and its scan data, for any "metadata only" proof.
- `editor/tests/fixtures/make-photographs.py` writes an MPO that is a whole disparity pair, and one that is not.

## Credits

Farbrausch and .theprodukkt, as the `fr_public` README names them: Fabian "ryg" Giesen, Sebastian "Wayfinder" Grillmaier, Tammo "kb" Hinrichs, Thomas "fiver2" Mahlke, Christoph "giZMo" Muetze, Dierk "Chaos" Ohlerich, Kai "cp" Poethkow, Ronny Pries, Dennis "Exoticorn" Ranke, Leonard "paniq" Ritter and Bastian "Tron" Zuehlke; 49Games GmbH in Altona's licence; Sean Barrett for the stb libraries inside Altona.
The maths carried inside the core is musl's (release 1.2.6, MIT): Rich Felker and the musl contributors, with Sun Microsystems (SunPro), Ian Lance Taylor and Bruce D. Evans for the single-precision sine, cosine and arc tangent and Arm Limited for `powf`, as the files and musl's `COPYRIGHT` name them.
The partners' server follows the Model Context Protocol's specification (revisions 2025-11-25 and 2026-07-28), by the Model Context Protocol project and its contributors, and the two-era pattern of the edition's own skills server.
The partners' server is proved under the official MCP SDK for Python (the `mcp` package, by the Model Context Protocol project, MIT).
The editor is built on Qt (The Qt Company and the Qt Project) and KDE Frameworks (the KDE community): KXmlGui, KConfig, KI18n, KIO, KWidgetsAddons, KCoreAddons; its pictures are taken with KWin's ScreenShot2.
The proof's real input uses KWin's fake input protocol (`org_kde_kwin_fake_input`, by Martin Gräßlin, LGPL-2.1-or-later) and follows the proof rig's `fakeinput` tool; the rules for a place on the page are werkkzeug3's own (`winpage.cpp`, Farbrausch).
The relief's mapping is the edition's stereo texture module's (relief mapping after Fábio Policarpo, Manuel M. Oliveira and João L. D. Comba, 2005, and parallax occlusion mapping after Natalya Tatarchuk, 2006, as the module's own notes credit them); the 3D area follows Marble's `StereoLayer` and stereo-layer's surface, and is declared through `libstereo-declare`.
The stereo photograph is read by stereo-layer and the edition's KImageFormats; MPO is CIPA DC-007, the JPS block is the JPS format's own, `sTER` is the PNG Extensions' chunk (version 1.4.0, 3.6); the photographs of the proof are made with Pillow (Jeffrey A. Clark and contributors).
The compositor without the stereo protocol in the proof is Weston (the Wayland project).
The fitter and its modern operators (twelve since its tenth round: Quad, Grid and Stack lay whole procedures) are the edition's "procedures from pixels" work, credited in [a procedure fitted to a bitmap](procedural-texture-from-a-bitmap.md); the two eyes from a picture and its depth map are made by stereo-layer's depth library.
The stereo photographs the Fit tool was tried on are by Robbie Sproule (Montreal), as Wikimedia Commons records them: "Bark 1", "Moss 1" and "Sand pile", CC BY 2.0, cross-eyed pairs; each eye's square was cut at the photograph's own pixels.
WebAssembly builds ran in wasmtime (Bytecode Alliance).
The people whose work this plan reads or builds on, by the names their own pages give: wxthss82, wzman, Gregor Riepl (onitake), Frantsishak (KkriegerNet), kznsq, Mason Liu (kkrieger-wasm), Alfredo (varrtto), Steven Schronk, Rodz Labs and the Material Maker contributors, Nicolas Brown and the TextureLab contributors, Cedric Guillemet (Imogen).
The thirty bitmap operators carried from `fr_public` pull request #108 are the work of wangxin (wxthss82 on GitHub), under the tree's BSD 2-clause licence; the colour matrix is OpenKTG's, written by Fabian "ryg" Giesen in 2007 and placed in the public domain; the seam that keeps the detail's contrast follows Eric Heitz and Fabrice Neyret (2018); Blend's modes are those of W3C Compositing and Blending Level 1; the natural logarithm carried with the maths is musl's (Arm Limited); the sixteen-bit pictures follow the PNG specification, third edition (W3C), for `sBIT`.
The Text operator draws with FreeType 2.14.3 (David Turner, Robert Wilhelm and Werner Lemberg; the FreeType Project licence), HarfBuzz 14.4.0 (Behdad Esfahbod and the authors its AUTHORS file names; the "Old MIT" licence), SheenBidi 3.0.0 (Muhammad Tayyab Akram; Apache 2.0), plutovg and plutosvg (Samuel Ugochukwu; MIT), libpng 1.6.59, zlib and Brotli, each compiled from Debian's source package; the renderer files and the font index are the edition's "procedures from pixels" work, carried unchanged.
Portions of this software are copyright © 2026 The FreeType Project (https://freetype.org). All rights reserved.
The metadata-only save of a stereo JPEG and the two eyes from a depth map are stereo-layer's (`Picture::saveCorrection`, `Picture::load`); `BaseViewpointNum` and `MPIndividualNum` are CIPA DC-007's.
