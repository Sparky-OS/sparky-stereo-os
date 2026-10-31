#!/bin/bash
# Count what an interactive bash start costs with Debian's bash_completion and with its comments blanked.
# Run in a folder holding bash_completion.orig (from Debian's bash-completion .deb) and bash_completion.blank
# (from blank-shell.py). perf needs CAP_PERFMON or root.
set -e
for f in orig blank; do
  bash --norc --noprofile -i -c "source ./bash_completion.$f >/dev/null 2>&1; declare -f; complete -p" 2>/dev/null \
    | sed "s|bash_completion\.$f|bash_completion.X|g" > defs-$f.txt
done
cmp defs-orig.txt defs-blank.txt && echo "functions and completions identical"
: > perf-bash.csv
for round in 1 2 3; do for f in orig blank; do
  perf stat -x, -e instructions:u,cycles:u,task-clock -r 40 -- bash --norc --noprofile -i -c "source ./bash_completion.$f >/dev/null 2>&1" \
    2>&1 >/dev/null </dev/null | sed "s/^/$f,$round,/" >> perf-bash.csv
done; done
