#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# The build part of FreeCAD's "CI primary" Ubuntu job, in a container: the same apt package
# script, CMake 4.2.3, the release preset with the job's options, then the C++ test executables,
# and clang-tidy on the lines a change touches (the Lint job's step).
#
#   freecad-ci-build.sh --image UBUNTU_26_04 --build DIR [--target T]... [--tidy-base BASE] CHECKOUT
#
# CHECKOUT  a FreeCAD clone with the revision to test checked out and the submodules
#           src/3rdParty/GSL, src/3rdParty/OndselSolver and src/Mod/AddonManager initialised;
#           it is mounted read-only
# --build   a folder for the build (several GB) and the logs
# --target  a test target to build and run (default Gui_tests_run); repeat for more
# --tidy-base  run clang-tidy on the lines changed since this commit
# APT_PREPARE  optional host file, run with sh before apt (a site's apt policy); APT_CA another
#           file mounted at /run/host-ca.crt for it
# Exit status: 0 all built and passed, 1 a build or test failed, 2 setup error.
set -euo pipefail

image=""; build=""; targets=(); tidy_base=""
while [ $# -gt 0 ]; do
    case "$1" in
        --image) image=$2; shift 2 ;;
        --build) build=$2; shift 2 ;;
        --target) targets+=("$2"); shift 2 ;;
        --tidy-base) tidy_base=$2; shift 2 ;;
        -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
        -*) echo "freecad-ci-build: unknown option $1" >&2; exit 2 ;;
        *) break ;;
    esac
done
if [ $# -ne 1 ] || [ -z "$image" ] || [ -z "$build" ]; then
    echo "usage: freecad-ci-build.sh --image IMAGE --build DIR [--target T]... [--tidy-base BASE] CHECKOUT" >&2
    exit 2
fi
checkout=$(cd "$1" && pwd)
[ ${#targets[@]} -gt 0 ] || targets=(Gui_tests_run)
mkdir -p "$build"
build=$(cd "$build" && pwd)
head=$(git -C "$checkout" rev-parse HEAD)
tidy=""
if [ -n "$tidy_base" ]; then
    tidy=$(git -C "$checkout" rev-parse --verify "$tidy_base^{commit}")
fi
mounts=(-v "$checkout:/src:ro" -v "$build:/build")
if [ -n "${APT_PREPARE:-}" ]; then
    mounts+=(-v "$APT_PREPARE:/run/apt-prepare.sh:ro")
    [ -n "${APT_CA:-}" ] && mounts+=(-v "$APT_CA:/run/host-ca.crt:ro")
fi
echo "freecad-ci-build: $checkout at $head; build $build; targets ${targets[*]}"
set +e
docker run -i --rm --pull=never --ulimit core=1 --cpus 4 --platform linux/amd64 "${mounts[@]}" \
    -e TARGETS="${targets[*]}" -e TIDY_BASE="$tidy" -e OWNER="$(id -u):$(id -g)" \
    "$image" bash -s <<'INNER' | tee "$build/ci-build.log"
set -uo pipefail
export DEBIAN_FRONTEND=noninteractive
[ -f /run/apt-prepare.sh ] && { sh /run/apt-prepare.sh || exit 2; }
# the job's runner has sudo; the container is root
printf '#!/bin/sh\nexec "$@"\n' > /usr/local/bin/sudo && chmod 755 /usr/local/bin/sudo
bash /src/package/ubuntu/install-apt-packages.sh > /build/apt.log 2>&1 || { echo "apt packages: FAILED (see apt.log)"; exit 2; }
apt-get install -y -qq --no-install-recommends clang-tidy curl ca-certificates xvfb xauth >> /build/apt.log 2>&1 || exit 2
# the downloaded packages stay in the container's layer, on the host's Docker disk, until cleaned
apt-get clean
echo "apt packages: installed; clang-tidy $(clang-tidy --version | grep -o 'version [0-9.]*')"
# CMake 4.2.3, as the job's setup-cmake step, checked against Kitware's published SHA-256
cd /tmp && curl -sSfLO https://github.com/Kitware/CMake/releases/download/v4.2.3/cmake-4.2.3-linux-x86_64.tar.gz \
    && echo '5bb505d5e0cca0480a330f7f27ccf52c2b8b5214c5bba97df08899f5ef650c23  cmake-4.2.3-linux-x86_64.tar.gz' | sha256sum -c --quiet \
    && tar -xzf cmake-4.2.3-linux-x86_64.tar.gz -C /opt || { echo "cmake 4.2.3: FAILED"; exit 2; }
export PATH=/opt/cmake-4.2.3-linux-x86_64/bin:$PATH
chown "$OWNER" /build
as_owner() { setpriv --reuid="${OWNER%:*}" --regid="${OWNER#*:}" --clear-groups -- env HOME=/build/home "$@"; }
mkdir -p /build/home && chown "$OWNER" /build/home
status=0
# FreeCAD's configure writes into its source tree (src/3rdParty/Clipper2 configure_file), so it
# builds a copy, never the read-only checkout
rm -rf /build/src && as_owner cp -a /src/. /build/src || { echo "source copy: FAILED"; exit 2; }
# a cache made for another source folder is refused by CMake ("does not match the source")
if [ -f /build/release/CMakeCache.txt ] && ! grep -qx 'CMAKE_HOME_DIRECTORY:INTERNAL=/build/src' /build/release/CMakeCache.txt; then
    rm -rf /build/release
fi
if as_owner cmake -S /build/src -B /build/release -G Ninja --preset release -DFREECAD_USE_EXTERNAL_COIN_PIVY=ON \
        -DFREECAD_USE_EXTERNAL_PYCXX=ON -DFREECAD_USE_EXTERNAL_JSON=ON > /build/configure.log 2>&1; then
    echo "configure: PASS"
else
    echo "configure: FAILED (see configure.log)"; exit 1
fi
if as_owner cmake --build /build/release --target $TARGETS -- -j4 > /build/build.log 2>&1; then
    echo "build $TARGETS: PASS"
else
    echo "build $TARGETS: FAILED (see build.log)"; exit 1
fi
for t in $TARGETS; do
    if as_owner xvfb-run -a /build/release/tests/$t --gtest_output=json:/build/$t.json > /build/$t.log 2>&1; then
        echo "test $t: PASS ($(grep -c '^\[       OK \]' /build/$t.log) passed)"
    else
        echo "test $t: FAILED (see $t.log)"; status=1
    fi
done
if [ -n "$TIDY_BASE" ]; then
    cd /src
    # the Lint job's line filter, made from the local diff instead of GitHub's API
    python3 - "$TIDY_BASE" > /build/tidy-lines.json <<'PY'
import json, re, subprocess, sys
diff = subprocess.run(["git", "-c", "safe.directory=*", "diff", "-U0", "--diff-filter=ACMR", sys.argv[1], "HEAD", "--",
                       "*.c", "*.cc", "*.cpp", "*.cxx", "*.h", "*.hh", "*.hpp", "*.hxx"],
                      capture_output=True, text=True, check=True).stdout
files, name = {}, None
for line in diff.splitlines():
    if line.startswith("+++ b/"):
        name = line[6:]
        files[name] = []
    m = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", line)
    if m and name:
        start, count = int(m.group(1)), int(m.group(2) or 1)
        if count:
            files[name].append([start, start + count - 1])
print(json.dumps([{"name": "/build/src/" + n, "lines": l} for n, l in files.items() if l]))
PY
    mapfile -t tidyfiles < <(python3 -c 'import json,sys; [print(e["name"]) for e in json.load(open(sys.argv[1]))]' /build/tidy-lines.json)
    if [ ${#tidyfiles[@]} -gt 0 ]; then
        # clang_tidy.py runs "clang-tidy -p build" in its working folder and writes its fixes there
        mkdir -p /build/tidy-cwd && ln -sfn /build/release /build/tidy-cwd/build && chown -R "$OWNER" /build/tidy-cwd
        cd /build/tidy-cwd
        if as_owner env RUNNER_WORKSPACE=/build python3 /build/src/tools/lint/clang_tidy.py --files "${tidyfiles[@]}" \
                --line-filter "$(cat /build/tidy-lines.json)" --clang-style file \
                --log-dir /build/tidy --report-file /build/tidy/report.md > /build/clang-tidy.log 2>&1; then
            echo "clang-tidy: PASS (no errors; warnings in tidy/clang-tidy.log)"
        else
            echo "clang-tidy: FINDINGS (see clang-tidy.log)"; status=1
        fi
    fi
fi
chown -R "$OWNER" /build
echo "ci build done"
exit $status
INNER
status=${PIPESTATUS[0]}
set -e
if ! grep -q '^ci build done$' "$build/ci-build.log"; then
    echo "freecad-ci-build: the container did not finish its steps (exit $status)" >&2
    [ "$status" -eq 0 ] && status=2
fi
echo "freecad-ci-build: exit $status (logs in $build)"
exit "$status"
