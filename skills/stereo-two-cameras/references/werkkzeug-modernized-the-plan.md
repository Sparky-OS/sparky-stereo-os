# werkkzeug, modernized: the plan

Written on 2026-11-10 (ORDER 514, milestone 1), by Claude Fable 5.2 with Daniel Campos Ramos.
It holds what Farbrausch's open tools are, what builds where, who already works on them, the plan for an editor on KDE Plasma where people and AI partners build procedural textures together, and, since milestone 2 (11 November 2026), the recipe and the traps of the editor's core: Stereo Werkkzeug, the part without a window.
Since milestone 3 (the same day) it also holds the maths the core carries inside, so that one procedure draws the same bytes with every C library and in WebAssembly, and the partners' server, which an AI partner reaches the open project through.
Since milestone 4 (the same day) it holds the editor's first light: a KDE program over the C interface, its parameter panel made from Farbrausch's table, a live picture drawn in a process of its own, the core's sentences in ten languages, and AI partners working in the open window.
Since milestone 5 (the same day) it holds building in the window: operators dragged onto the page with the core's connection rules shown while they are dragged, a preview that can be pinned and tiled, the two sides of a step side by side, a partner's change marked on the page, and a proof that sends real pointer and key events through the compositor.
The stereo preview, new operators and the Text operator are not built yet.
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

## Credits

Farbrausch and .theprodukkt, as the `fr_public` README names them: Fabian "ryg" Giesen, Sebastian "Wayfinder" Grillmaier, Tammo "kb" Hinrichs, Thomas "fiver2" Mahlke, Christoph "giZMo" Muetze, Dierk "Chaos" Ohlerich, Kai "cp" Poethkow, Ronny Pries, Dennis "Exoticorn" Ranke, Leonard "paniq" Ritter and Bastian "Tron" Zuehlke; 49Games GmbH in Altona's licence; Sean Barrett for the stb libraries inside Altona.
The maths carried inside the core is musl's (release 1.2.6, MIT): Rich Felker and the musl contributors, with Sun Microsystems (SunPro), Ian Lance Taylor and Bruce D. Evans for the single-precision sine, cosine and arc tangent and Arm Limited for `powf`, as the files and musl's `COPYRIGHT` name them.
The partners' server follows the Model Context Protocol's specification (revisions 2025-11-25 and 2026-07-28), by the Model Context Protocol project and its contributors, and the two-era pattern of the edition's own skills server.
The partners' server is proved under the official MCP SDK for Python (the `mcp` package, by the Model Context Protocol project, MIT).
The editor is built on Qt (The Qt Company and the Qt Project) and KDE Frameworks (the KDE community): KXmlGui, KConfig, KI18n, KIO, KWidgetsAddons, KCoreAddons; its pictures are taken with KWin's ScreenShot2.
The proof's real input uses KWin's fake input protocol (`org_kde_kwin_fake_input`, by Martin Gräßlin, LGPL-2.1-or-later) and follows the proof rig's `fakeinput` tool; the rules for a place on the page are werkkzeug3's own (`winpage.cpp`, Farbrausch).
WebAssembly builds ran in wasmtime (Bytecode Alliance).
The people whose work this plan reads or builds on, by the names their own pages give: wxthss82, wzman, Gregor Riepl (onitake), Frantsishak (KkriegerNet), kznsq, Mason Liu (kkrieger-wasm), Alfredo (varrtto), Steven Schronk, Rodz Labs and the Material Maker contributors, Nicolas Brown and the TextureLab contributors, Cedric Guillemet (Imogen).
