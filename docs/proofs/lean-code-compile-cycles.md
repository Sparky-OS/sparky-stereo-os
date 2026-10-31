# Lean Code and the compiler, and the shell: instructions counted

Measured on 30 and 31 October 2026 on the Sparky Stereo OS development station (x86_64, GCC 16.2.0-3, GNU bash 5.3.15, perf 7.2.11), for Daniel's reply in [Evidence over authority](../evidence-over-authority.md#daniels-reply).
The question: when a program reads a file again, at every build or at every start, how much of that work do the comments cost?
The scripts and the raw counts are in [lean-code-compile-cycles/](lean-code-compile-cycles/).

## At every build: the C++ standard library headers

**Input:** Debian's `libstdc++-16-dev` 16.2.0-3 (.deb sha256 `9bbc2704dd8d47fb593f7051cb01c8bdba22e13d817774f771cad854b53c4e49`), unpacked.
The station's own `/usr/include` is not the baseline: dpkg-stereo had already projected part of it at install time.

**Four copies of the header trees, served at one path** (a symbolic link switched between them, so `__FILE__` is the same in every case):
1. Debian's original.
2. The station's installed headers.
3. The edition's C and C++ renderer (`lean/project.py`'s `render_text` with its GCC check; Doxygen comments are removed too, since the compiler is the only reader measured here; notices stay; a `#line` directive follows every removed run so line numbers are kept): `render-tree.py`.
4. The same lexer's comment spans, each replaced by one space or by the line breaks it held, so line numbers are kept with no directive: `blank-tree.py`.

**Programs:** `prog.cc`, 12 lines using `<algorithm>`, `<iostream>`, `<map>`, `<string>` and `<vector>`; and `all.cc`, which includes `<bits/stdc++.h>`.

**Controls:** for every copy, the `-O2` objects of both programs and the preprocessed output of `all.cc` are byte for byte the same as with Debian's headers.

**Count:** `perf stat -e cycles:u,instructions:u,task-clock -r 8`, two rounds interleaved across the four copies (`measure.sh`, raw counts in `perf-compile.csv`).

| Millions of instructions | Debian's headers | Station's installed headers | Our renderer today, with `#line` | Comments removed, line breaks kept |
|---|---|---|---|---|
| Preprocess `prog.cc` | 770.2 | 779.6 (1.2% more) | 961.0 (24.8% more) | 757.6 (1.6% fewer) |
| Preprocess `all.cc` | 1,912.8 | 1,932.3 (1.0% more) | 2,355.9 (23.2% more) | 1,887.6 (1.3% fewer) |
| Compile `prog.cc`, `-O2` | 7,506.0 | 7,507.4 (0.02% more) | 7,594.3 (1.2% more) | 7,492.6 (0.18% fewer) |
| `-fsyntax-only` on `all.cc` | 7,648.1 | 7,651.1 (0.04% more) | 7,890.2 (3.2% more) | 7,618.7 (0.38% fewer) |

**Bytes read:** `prog.cc` reads 156 headers: 3,750,259 bytes from Debian's copy, 2,876,279 with `#line`, 2,823,268 with the line breaks kept.
`all.cc` reads 320 headers: 8,012,959, 6,189,483 and 6,114,306 bytes.

## At every start: bash_completion

**Input:** Debian's `bash-completion` 1:2.16.0-8 (.deb sha256 `a1803f343c275584e86e4d6bda1cb5bae17dc84c69e98fc3caf8046fdfa2aaaa`); every interactive bash on Debian reads `/usr/share/bash-completion/bash_completion`.
The edition's shell projector leaves this file ("uses line numbers (LINENO, caller)"), rightly: its line numbers must not move.
So its 1,103 comments were blanked with the same lexer, each kept as the line breaks it held (`blank-shell.py`): 126,996 bytes became 78,534, and 3,475 lines stayed 3,475.

**Control:** after sourcing each file, `declare -f; complete -p` prints the same 3,285 lines, byte for byte.

**Count:** `bash --norc --noprofile -i -c 'source FILE'`, `perf stat -r 40`, three rounds interleaved (`measure-bash.sh`, raw counts in `perf-bash.csv`).

| Per interactive bash start | Debian's file | Comments removed, line breaks kept |
|---|---|---|
| Instructions | 105.79 million | 101.10 million (4.69 million, 4.43% fewer) |
| Cycles | 42.6 million | 39.8 million (6.5% fewer) |
| Task clock | 13.0 ms | 12.2 ms |

## Reading the numbers

- Instruction counts repeated within 0.04% from round to round in every case; they are the exact measure of the work.
- Cycles and times varied by several percent between rounds, because the station was building a kernel at the same time; the cost of `#line` (16% to 22% more cycles to preprocess) stands out of that noise, the smaller savings do not yet. A count on a quiet machine follows.
- Today's C and C++ renderer misses the design: the `#line` directives it writes to keep line numbers cost GCC more than the comments did, and the station's headers, projected the same way at install time, cost 1.2% more to preprocess. Keeping line breaks instead keeps the same line numbers with no directive and fewer bytes; that is the renderer's next change.
- These are two readers and two sets of files. A system holds many more: the installed system of the 31 October developer ISO lists 66,302 comment-bearing text files (723 MB), of which Lean Code projected 15,763, removing 25.3 MB of comments.

## Reproduce

```
# headers: unpack Debian's libstdc++-16-dev into deb/x, then
mkdir -p deb-tree/c++ deb-tree/x86_64-linux-gnu/c++
cp -a deb/x/usr/include/c++/16 deb-tree/c++/16
cp -a deb/x/usr/include/x86_64-linux-gnu/c++/16 deb-tree/x86_64-linux-gnu/c++/16
export SPARKY_LEAN=<Sparky-OS/sparky-stereo-os-build checkout>/sparky-os
for t in c++/16 x86_64-linux-gnu/c++/16; do
  python3 render-tree.py deb-tree/$t lean/$t; python3 blank-tree.py deb-tree/$t blank/$t
done
# a copy of the headers installed on the machine under test goes in station/ the same way
bash measure.sh

# bash_completion: from Debian's bash-completion package
cp <unpacked>/usr/share/bash-completion/bash_completion bash_completion.orig
python3 blank-shell.py bash_completion.orig bash_completion.blank
bash measure-bash.sh
```
