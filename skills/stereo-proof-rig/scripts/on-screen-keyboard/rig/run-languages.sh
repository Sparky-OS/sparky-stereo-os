#!/bin/bash
# run-languages.sh IMAGE OUTDIR [VAR=VALUE ...]: the typing case in each of the ten required languages, one fresh container
# each (run-case.sh), OUTDIR/LANG/result.json per language. Environment as run-case.sh; LANGS (code:locale ...) for a part.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
IMG=$1; OUT=$2; shift 2
mkdir -p "$OUT"
for l in ${LANGS:-en:en_US pt_BR:pt_BR es:es_ES fr:fr_FR de:de_DE pl:pl_PL ja:ja_JP ko:ko_KR zh_CN:zh_CN zh_TW:zh_TW}; do
	code=${l%%:*}; loc=${l#*:}
	bash "$HERE/run-case.sh" "$IMG" "$OUT/$code" LOGIN_LANG="$loc.UTF-8" LANG_CASE="$code" "$@"
done
