#!/bin/bash
# mutate-signal.sh: each mutation of the test signal must turn its unit test red; then the unmutated green run
set -u
SRC=${PLASMA_PA_SRC:?the plasma-pa clone}
M=${MUT_DIR:?a scratch folder}
declare -A MUT
MUT[white-noise-not-pink]='s/x\[i\] = b0 + b1 + b2 + w \* 0.1848;/x[i] = w;/'
MUT[level-minus-ten]='s/static constexpr double defaultLevelDb = -20.0;/static constexpr double defaultLevelDb = -10.0;/'
MUT[level-not-normalised]='s/const double scale = rms > 0 ? qPow(10.0, levelDb \/ 20.0) \/ rms : 0;/const double scale = 0.05;/'
MUT[noise-on-every-channel]='s/samples\[(first + i) \* channels + ch\] = noise.at(i);/for (int k = 0; k < channels; ++k) samples[(first + i) * channels + k] = noise.at(i);/'
MUT[no-gap]='s/const int gap = qRound(gapSeconds \* rate);/const int gap = 0;/'
MUT[burst-one-frame-early]='s/return {indexInWhich \* (len + gap), len};/return {indexInWhich * (len + gap) + 1, len};/'
MUT[unknown-speaker-not-ignored]='s/if (positions.contains(p)) {/if (true) {/'
for k in "${!MUT[@]}"; do
  rm -rf "$M"; mkdir -p "$M"; cp -r "$SRC/src" "$SRC/autotests" "$M/"
  for f in speakertestsignal.cpp speakertestsignal.h; do sed -i "${MUT[$k]}" "$M/src/$f"; done
  if diff -q -r "$M/src" "$SRC/src" >/dev/null; then echo "NOCHANGE $k"; continue; fi
  out=$("$(dirname "$0")/run-unit.sh" "$M" speakertestsignaltest speakertestsignal 2>&1); rc=$?
  echo "$k: rc=$rc failures=$(echo "$out" | grep -c '^FAIL!') $(echo "$out" | grep '^Totals')"
done
rm -rf "$M"
echo "--- green, nothing mutated"
"$(dirname "$0")/run-unit.sh" "$SRC" speakertestsignaltest speakertestsignal 2>&1 | grep '^Totals'
