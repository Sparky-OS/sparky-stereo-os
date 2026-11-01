#!/bin/bash
# measure.sh for toolkit 0.1.20: four copies of Debian's libstdc++-16-dev headers, served at one path (a symbolic
# link switched between them): deb-tree (Debian's), l0115 (toolkit 0.1.15, #line), l0119 (0.1.19, every line kept) and
# l0120 (0.1.20, comment-only lines removed), each rendered by render-tree.py with that toolkit. Run from a folder
# holding the four trees, prog.cc and all.cc; perf needs CAP_PERFMON or root. Besides measure.sh's counts: the objects
# with and without -g (and with the debug sections stripped) and with -D_GLIBCXX_ASSERTIONS, compared with Debian's;
# the preprocessed outputs; the line markers GCC writes and the bytes of the headers read.
set -e
I="-nostdinc++ -isystem $PWD/inc/c++/16 -isystem $PWD/inc/x86_64-linux-gnu/c++/16"
T="deb-tree l0115 l0119 l0120"
for t in $T; do
  ln -sfn $t inc
  for p in prog all; do
    g++ -std=c++23 $I -O2 -c $p.cc -o $p-$t.o
    g++ -std=c++23 $I -O2 -g -c $p.cc -o $p-g-$t.o
    objcopy --strip-debug $p-g-$t.o $p-g-$t.nodebug.o
    g++ -std=c++23 $I -E $p.cc -o $p-$t.i
    g++ -std=c++23 $I -D_GLIBCXX_ASSERTIONS -E $p.cc -o $p-assert-$t.i
    g++ -std=c++23 $I -D_GLIBCXX_ASSERTIONS -O2 -c $p.cc -o $p-assert-$t.o
    g++ -std=c++23 $I -H -fsyntax-only $p.cc 2> $p-$t.headers
  done
  printf '%s markers %s %s bytes %s\n' $t "$(grep -c '^# [0-9]' prog-$t.i)" "$(grep -c '^# [0-9]' all-$t.i)" \
    "$(sed 's/^\.* //' all-$t.headers | sort -u | xargs cat 2>/dev/null | wc -c)"
done > lines-markers-bytes.txt
for t in l0115 l0119 l0120; do
  for p in prog all; do
    for f in "$p-%s.o" "$p-g-%s.nodebug.o" "$p-g-%s.o" "$p-assert-%s.o"; do
      a=$(printf "$f" deb-tree) b=$(printf "$f" $t)
      cmp -s "$a" "$b" && echo "$t $(printf "$f" FORM) identical" || echo "$t $(printf "$f" FORM) differ"
    done
  done
done > objects.txt
: > perf.csv
run() { w=$1; shift; for round in 1 2; do for t in $T; do ln -sfn $t inc
  perf stat -x, -e cycles:u,instructions:u,task-clock -r 8 -- "$@" 2>&1 >/dev/null | sed "s/^/$w,$t,$round,/" >> perf.csv; done; done; }
run pp-prog g++ -std=c++23 $I -E prog.cc -o /dev/null
run pp-all g++ -std=c++23 $I -E all.cc -o /dev/null
run cc-prog g++ -std=c++23 $I -O2 -c prog.cc -o /dev/null
run syn-all g++ -std=c++23 $I -fsyntax-only all.cc
cat lines-markers-bytes.txt objects.txt
