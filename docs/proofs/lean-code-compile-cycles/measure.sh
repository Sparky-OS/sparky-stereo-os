#!/bin/bash
# Count the instructions and cycles GCC spends on four copies of the libstdc++ headers.
# Run from a folder holding deb-tree/, station/, lean/ and blank/ (each with c++/16 and
# x86_64-linux-gnu/c++/16), prog.cc and all.cc. perf needs CAP_PERFMON or root.
set -e
I="-nostdinc++ -isystem $PWD/inc/c++/16 -isystem $PWD/inc/x86_64-linux-gnu/c++/16"
for t in deb-tree station lean blank; do
  ln -sfn $t inc
  g++ -std=c++23 $I -O2 -c prog.cc -o prog-$t.o; g++ -std=c++23 $I -O2 -c all.cc -o all-$t.o
  g++ -std=c++23 $I -E all.cc | grep -v '^# ' | tr -s ' \n' > pp-$t.txt
done
for t in station lean blank; do
  cmp prog-deb-tree.o prog-$t.o && cmp all-deb-tree.o all-$t.o && cmp pp-deb-tree.txt pp-$t.txt && echo "$t: objects and preprocessed output identical to Debian's"
done
: > perf.csv
run() { w=$1; shift; for round in 1 2; do for t in deb-tree station lean blank; do ln -sfn $t inc
  perf stat -x, -e cycles:u,instructions:u,task-clock -r 8 -- "$@" 2>&1 >/dev/null | sed "s/^/$w,$t,$round,/" >> perf.csv; done; done; }
run pp-prog g++ -std=c++23 $I -E prog.cc -o /dev/null
run pp-all g++ -std=c++23 $I -E all.cc -o /dev/null
run cc-prog g++ -std=c++23 $I -O2 -c prog.cc -o /dev/null
run syn-all g++ -std=c++23 $I -fsyntax-only all.cc
