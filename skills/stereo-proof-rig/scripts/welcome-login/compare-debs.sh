#!/bin/bash
# compare-debs.sh OLD.deb NEW.deb: the file lists of a package and its successor, path by path (dpkg-deb -c, the paths
# only, sorted): lines only in the old one start with "-", only in the new one with "+"; then the files present in both
# whose sizes differ ("~"). Prints "same paths" when no path left or came.
set -euo pipefail
list() { dpkg-deb -c "$1" | awk '{size=$3; $1=$2=$3=$4=$5=""; sub(/^ +/, ""); sub(/ -> .*/, ""); print $0 "\t" size}' | sort; }
a=$(mktemp); b=$(mktemp); trap 'rm -f "$a" "$b"' EXIT
list "$1" > "$a"; list "$2" > "$b"
echo "old $(basename "$1") $(wc -l < "$a") paths; new $(basename "$2") $(wc -l < "$b") paths"
changed=$(diff <(cut -f1 "$a") <(cut -f1 "$b") | grep '^[<>]' | sed 's/^</-/; s/^>/+/' || true)
[ -n "$changed" ] && echo "$changed" || echo "same paths"
join -t "$(printf '\t')" "$a" "$b" | awk -F'\t' '$2 != $3 && $2 != 0 {print "~ " $1 " " $2 " -> " $3}'
