#!/bin/bash
# stage.sh STAGE SOURCE_DIR...: each SOURCE_DIR (one source's build output) copied into STAGE/NAME as a source closure:
# the .dsc and every file it names, the build record (.sparky-build.json), buildinfo and changes where the build made
# them, and the .deb files; then STAGE/SHA256SUMS over everything and its check. Refuses a .dsc whose named files are
# missing or whose sums differ, and a source without a build record.
set -euo pipefail
STAGE=$(mkdir -p "$1" && cd "$1" && pwd); shift
for src in "$@"; do
	src=$(cd "$src" && pwd)
	dsc=$(ls "$src"/*+lc1.dsc 2>/dev/null | head -1); [ -n "$dsc" ] || dsc=$(ls "$src"/*.dsc | head -1)
	name=$(sed -n 's/^Source: //p' "$dsc")
	dest=$STAGE/$name; mkdir -p "$dest"
	cp "$dsc" "$dest/"
	awk '/^Checksums-Sha256:/{f=1; next} /^[^ ]/{f=0} f && NF == 3 {print $1 "  " $3}' "$dsc" | while read -r sum file; do
		[ -f "$src/$file" ] || { echo "$name: $file named by $(basename "$dsc") is missing" >&2; exit 1; }
		echo "$sum  $src/$file" | sha256sum -c --quiet - || { echo "$name: $file differs from its .dsc" >&2; exit 1; }
		cp "$src/$file" "$dest/"
	done
	ls "$src"/*.sparky-build.json > /dev/null 2>&1 || { echo "$name: no build record in $src" >&2; exit 1; }
	cp "$src"/*.sparky-build.json "$src"/*.deb "$dest/"
	cp "$src"/*.buildinfo "$src"/*.changes "$dest/" 2>/dev/null || echo "$name: no buildinfo or changes (a standalone script package)"
done
(cd "$STAGE" && find . -type f ! -name SHA256SUMS ! -name .keep | sed 's|^\./||' | sort | xargs sha256sum > SHA256SUMS && sha256sum -c --quiet SHA256SUMS && echo "$(wc -l < SHA256SUMS) files, sums verified")
