#!/bin/bash
# mutate.sh: each mutation of the input checks must turn the unit test red (the red run, then the unmutated green run)
set -u
SRC=${PLASMA_PA_SRC:?the plasma-pa clone}
M=${MUT_DIR:?a scratch folder}
declare -A MUT
MUT[label-ends-with-dollar]='s/\\\\x{FF09}-\]{0,79}\\\\z/\\\\x{FF09}-]{0,79}$/'
MUT[label-class-any]='s/\^\[\\\\p{L}\\\\p{N}\]\[\\\\p{L}\\\\p{N}\\\\p{M}\\\\p{Zs}._+:()\/\\\\x{FF1A}\\\\x{FF08}\\\\x{FF09}-\]{0,79}\\\\z/^.{0,80}\\\\z/'
MUT[label-no-limit]='s/\\\\x{FF09}-\]{0,79}\\\\z/\\\\x{FF09}-]*\\\\z/'
MUT[label-allows-line-separator]='s/\\\\p{Zs}/\\\\p{Z}/'
MUT[label-allows-any-punctuation]='s/\\\\p{M}\\\\p{Zs}/\\\\p{M}\\\\p{Zs}\\\\p{P}/'
MUT[label-allows-format-chars]='s/\\\\p{M}\\\\p{Zs}/\\\\p{M}\\\\p{Zs}\\\\p{Cf}/'
MUT[filter-without-linger]='s/ node.linger = true//'
MUT[filter-without-dont-fallback]='s/ node.dont-fallback = true//'
MUT[level-allowed-in-the-file]='s/static const QSet<QString> deviceKeys = {u"positions"_s, u"label"_s,/static const QSet<QString> deviceKeys = {u"positions"_s, u"levels"_s, u"label"_s,/'
MUT[node-name-ends-with-dollar]='s/\[A-Za-z0-9_.:+-\]{1,200}\\\\z/[A-Za-z0-9_.:+-]{1,200}$/'
MUT[node-name-class-any]='s/\[A-Za-z0-9_.:+-\]{1,200}\\\\z/.{1,200}\\\\z/'
MUT[node-name-no-limit]='s/\[A-Za-z0-9_.:+-\]{1,200}\\\\z/[A-Za-z0-9_.:+-]+\\\\z/'
MUT[position-any]='s/return knownPositions().contains(position);/return !position.isEmpty();/'
MUT[level-nan-allowed]='s/return qIsFinite(v.toDouble());/return true;/'
MUT[level-text-allowed]='s/    case QMetaType::Int:/    case QMetaType::QString:\n    case QMetaType::Int:/'
MUT[distance-range-open]='s/v.toDouble() < minDistance || v.toDouble() > maxDistance/false/'
MUT[distances-may-miss-one]='s/if (distances.size() != positions.size()) {/if (false) {/'
MUT[crossover-range-open]='s/v.toDouble() < minCrossover || v.toDouble() > maxCrossover/false/'
MUT[small-lfe-allowed]='s/if (!positions.contains(p) || p == u"LFE"_s) {/if (!positions.contains(p)) {/'
MUT[small-without-sub-allowed]='s/|| !positions.contains(u"LFE"_s) ||/||/'
MUT[empty-device-allowed]='s/if (!hasEffect(dev)) {/if (false) {/'
MUT[unknown-device-key-allowed]='s/if (!deviceKeys.contains(k.key())) {/if (false) {/'
MUT[foreign-file-overwritten]='s/if (QFileInfo::exists(path) \&\& !isOurs(path)) {/if (false) {/'
for k in "${!MUT[@]}"; do
  rm -rf "$M"; mkdir -p "$M"; cp -r "$SRC/src" "$SRC/autotests" "$M/"
  sed -i "${MUT[$k]}" "$M/src/speakersetupconf.cpp"
  if cmp -s "$M/src/speakersetupconf.cpp" "$SRC/src/speakersetupconf.cpp"; then echo "NOCHANGE $k"; continue; fi
  out=$("$(dirname "$0")/run-unit.sh" "$M" 2>&1); rc=$?
  failed=$(echo "$out" | grep -c '^FAIL!')
  tot=$(echo "$out" | grep '^Totals')
  echo "$k: rc=$rc failures=$failed $tot"
done
rm -rf "$M"
echo "--- green, nothing mutated"
"$(dirname "$0")/run-unit.sh" "$SRC" 2>&1 | grep '^Totals'
