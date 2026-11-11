# werkkzeug, modernized: the plan

Written on 2026-11-10 (ORDER 514, milestone 1), by Claude Fable 5.2 with Daniel Campos Ramos.
It holds what Farbrausch's open tools are, what builds where, who already works on them, the plan for an editor on KDE Plasma where people and AI partners build procedural textures together, and, since milestone 2 (11 November 2026), the recipe and the traps of the editor's core: Stereo Werkkzeug, the part without a window.
The window, the partners' server and the stereo preview are not built yet.
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

1. Build: `./build.sh OUT` (Zig 0.16). It makes the operator table from Farbrausch's sources, then `OUT/wz` (the command), `OUT/libstereo_werkkzeug.a` with `stereo_werkkzeug.h`, and `OUT/capi_test`.
2. Prove: `tests/run-all.sh OUT`. One line per step; expect "55 steps passed, 0 failed". The steps that are controls pass when the check under them fails (a change made behind the journal's back, one flipped bit in one picture).
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
  Fix: on glibc, call the library's functions under their `_Float32` names, `sinf32` and `cosf32` (ISO/IEC TS 18661-3; the same code). A static musl build and a WebAssembly build keep the six differences: say so wherever "the same pixels" is claimed.
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

## What the parts are good for

- The `.ops` blocks are a table a program can read: generate the parameter panel and the partner's operator list from them, so the editor, the server and the documentation cannot drift apart.
- Pull request #108 keeps its 30 texture operators on a plain pixel buffer, so they can be tried without the rest of Werkkzeug4.
- OpenKTG has "consistent rules for texture sampling/filtering and pixel centers" that match OpenGL ES, in its README's words, which makes it the family to move to a GPU first.
- The project files of `fr_public` are a ready test set for a reader and writer: 23 files, four versions, two outer forms, and the editor's own writer as the specification.
- `kkrieger.k` is a ready test set for drawing: 854 named textures, 15,000 operators between them, and a reference that any compiler can rebuild.
- The text form makes a project reviewable with `diff`: change one parameter in the editor, and one line of text changes.
- Random damage is a cheap test of a reader: flip three bytes, read; whatever is read must write back as the same bytes, and whatever is not must be refused with a sentence.

## Credits

Farbrausch and .theprodukkt, as the `fr_public` README names them: Fabian "ryg" Giesen, Sebastian "Wayfinder" Grillmaier, Tammo "kb" Hinrichs, Thomas "fiver2" Mahlke, Christoph "giZMo" Muetze, Dierk "Chaos" Ohlerich, Kai "cp" Poethkow, Ronny Pries, Dennis "Exoticorn" Ranke, Leonard "paniq" Ritter and Bastian "Tron" Zuehlke; 49Games GmbH in Altona's licence; Sean Barrett for the stb libraries inside Altona.
The people whose work this plan reads or builds on, by the names their own pages give: wxthss82, wzman, Gregor Riepl (onitake), Frantsishak (KkriegerNet), kznsq, Mason Liu (kkrieger-wasm), Alfredo (varrtto), Steven Schronk, Rodz Labs and the Material Maker contributors, Nicolas Brown and the TextureLab contributors, Cedric Guillemet (Imogen).
