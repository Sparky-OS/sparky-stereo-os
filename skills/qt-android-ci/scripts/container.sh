#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
mode=${1:?Use build or run}
[[ "$mode" == build || "$mode" == run ]]
: "${QACI_WORK:?Absolute build-storage directory}"
: "${QACI_IMAGE:?Existing image with the documented build tools}"
: "${QACI_JDK:?Absolute path to JDK 21}"
: "${QACI_SOURCE:?Absolute path to the test source directory}"
export QACI_BUILD=${QACI_BUILD:-$QACI_WORK/build/frame-test}
export QACI_LOGS=${QACI_LOGS:-$QACI_WORK/evidence/frame-test}
export QACI_HOME=${QACI_HOME:-$QACI_WORK/home}
export QACI_AVD=${QACI_AVD:-qt_api28_x86_64}
[[ "$QACI_WORK" == /* && "$QACI_WORK" != / ]]
[[ "$QACI_SOURCE" == "$QACI_WORK/"* && "$QACI_BUILD" == "$QACI_WORK/"* ]]
[[ "$QACI_LOGS" == /* && "$QACI_HOME" == /* ]]
container=qt-android-ci-local-test
if [[ -n "${QACI_ARTIFACTS:-}" ]]; then
    for artifact in "$container" "$QACI_BUILD"; do
        grep -qxF "$artifact" "$QACI_ARTIFACTS" 2>/dev/null \
            || printf '%s\n' "$artifact" >> "$QACI_ARTIFACTS"
    done
fi
mkdir -p "$QACI_BUILD" "$QACI_LOGS" "$QACI_HOME"
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
args=(run --rm --name "$container" --user "$(id -u):$(id -g)" --cpus 4
    -v "$QACI_WORK:$QACI_WORK" -v "$QACI_LOGS:$QACI_LOGS" -v "$QACI_HOME:$QACI_HOME"
    -v "$QACI_JDK:$QACI_JDK:ro" -v "$script_dir:/qt-android-ci-recipe:ro"
    -e HOME="$QACI_HOME" -e JAVA_HOME="$QACI_JDK"
    -e QACI_WORK -e QACI_SOURCE -e QACI_BUILD -e QACI_LOGS -e QACI_AVD
    -w "$QACI_WORK")
if [[ -n "${QACI_SDK_SOURCE:-}" ]]; then
    args+=(-v "$QACI_SDK_SOURCE:$QACI_SDK_SOURCE:ro")
fi
if [[ "$mode" == run ]]; then
    kvm_gid=${QACI_KVM_GID:-$(stat -c %g /dev/kvm)}
    args+=(--device /dev/kvm --group-add "$kvm_gid")
else
    args+=(--memory 8g)
fi
exec docker "${args[@]}" "$QACI_IMAGE" bash /qt-android-ci-recipe/inside.sh "$mode"
