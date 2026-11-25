#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# FreeCAD's own formatting and lint checks on the files a change touches, in a container,
# with the versions FreeCAD's configuration pins. The checkout is mounted read-only and is not
# changed: the checks run in a shared clone made inside the container.
#
#   freecad-checks.sh [--all-files] [--tools-ref REF] [--image IMAGE] [--work DIR] CHECKOUT BASE [HEAD]
#
# CHECKOUT  a FreeCAD clone (a blobless clone works when BASE and HEAD are checked out once)
# BASE      the commit the change is built on (for a branch on main: git merge-base main HEAD)
# HEAD      the change's last commit (default: HEAD of CHECKOUT)
# --all-files  run the pre-commit hooks on every file they cover (the baseline of a revision)
# --tools-ref  the revision whose tools/lint scripts and spelling list are used (default HEAD:
#              a pull request's CI runs the tree merged into its target branch)
#
# Exit status: 0 when every check passed, 1 when at least one reported a finding, 2 on a usage
# or setup error. Each check prints one line: PASS, FINDINGS or SKIPPED, with the CI's own
# behaviour for it (blocking, or warning only).
set -euo pipefail

image=${FREECAD_CHECKS_IMAGE:-}
work=""
all_files=0
tools_ref=""
while [ $# -gt 0 ]; do
    case "$1" in
        --all-files) all_files=1; shift ;;
        --tools-ref) tools_ref=$2; shift 2 ;;
        --image) image=$2; shift 2 ;;
        --work) work=$2; shift 2 ;;
        -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
        --) shift; break ;;
        -*) echo "freecad-checks: unknown option $1" >&2; exit 2 ;;
        *) break ;;
    esac
done
if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    echo "usage: freecad-checks.sh [--all-files] [--image IMAGE] [--work DIR] CHECKOUT BASE [HEAD]" >&2
    exit 2
fi
checkout=$(cd "$1" && pwd)
base_ref=$2
head_ref=${3:-HEAD}
if [ -z "$image" ]; then
    echo "freecad-checks: give the image with --image or FREECAD_CHECKS_IMAGE (see the skill's CI page for how it is made)" >&2
    exit 2
fi
base=$(git -C "$checkout" rev-parse --verify "$base_ref^{commit}")
head=$(git -C "$checkout" rev-parse --verify "$head_ref^{commit}")
tools=$(git -C "$checkout" rev-parse --verify "${tools_ref:-$head}^{commit}")
if [ -z "$work" ]; then
    work=$(mktemp -d "${TMPDIR:-/var/tmp}/freecad-checks.XXXXXX")
fi
mkdir -p "$work/home"
echo "freecad-checks: base $base head $head tools $tools; scratch $work"

# -i: the checks are this script's own lines, read by bash from standard input; without it
# bash -s reads nothing and the container exits 0 having run nothing
set +e
docker run -i --rm --pull=never --ulimit core=1 --cpus 4 --platform linux/amd64 \
    --user "$(id -u):$(id -g)" -e HOME=/work/home -e PRE_COMMIT_HOME=/work/home/pre-commit \
    -v "$checkout:$checkout:ro" -v "$work:/work" \
    "$image" bash -s -- "$checkout" "$base" "$head" "$all_files" "$tools" <<'INNER' | tee "$work/summary.txt"
set -uo pipefail
src=$1; base=$2; head=$3; all_files=$4; tools_rev=$5
# the lint scripts print GitHub's problem-matcher lines with this path; outside GitHub it is unset
export RUNNER_WORKSPACE=/work
rm -rf /work/tree /work/tools /work/logs /work/report
git clone -q --shared --no-checkout "$src" /work/tree || exit 2
cd /work/tree || exit 2
git -c advice.detachedHead=false checkout -q --detach "$head" || exit 2
mkdir -p /work/tools /work/logs /work/report
git archive "$tools_rev" tools/lint .github/codespellignore | tar -x -C /work/tools || exit 2
lint=/work/tools/tools/lint
report=/work/report/report.md
: > "$report"
mapfile -t files < <(git diff --name-only --diff-filter=ACMR "$base" "$head")
mapfile -t cpp < <(printf '%s\n' "${files[@]}" | grep -E '\.(c|cc|cu|cuh|c\+\+|cpp|cxx|h|hh|h\+\+|hpp|hxx)$' || true)
mapfile -t py < <(printf '%s\n' "${files[@]}" | grep -E '\.pyi?$' || true)
echo "changed files: ${#files[@]} (C++ ${#cpp[@]}, Python ${#py[@]})"
failed=0
say() { printf '%-34s %-9s %s\n' "$1" "$2" "$3"; }
run() {  # name, CI behaviour, command...
    local name=$1 ci=$2; shift 2
    local log="/work/logs/${name// /-}.log"
    if "$@" > "$log" 2>&1; then
        say "$name" PASS "($ci)"
    else
        say "$name" FINDINGS "($ci) log: $log"
        failed=1
    fi
}
# 1. pre-commit, with the hooks and revisions .pre-commit-config.yaml pins (pre-commit.ci on a PR)
if [ "$all_files" = 1 ]; then
    run "pre-commit (all files)" "pre-commit.ci on the PR" pre-commit run --all-files --show-diff-on-failure
elif [ ${#files[@]} -gt 0 ]; then
    run "pre-commit" "pre-commit.ci on the PR" pre-commit run --from-ref "$base" --to-ref "$head" --show-diff-on-failure
else
    say "pre-commit" SKIPPED "(no changed files)"
fi
# 2. the Lint job's checks (sub_lint.yml), with its own scripts and arguments
if [ -f src/Tools/sync_version.py ]; then
    run "version sync" "Lint, blocking" python3 src/Tools/sync_version.py --check
else
    say "version sync" SKIPPED "(this revision has no src/Tools/sync_version.py)"
fi
run "file case" "Lint, blocking" bash -c '! git ls-files | sort -f | uniq -di | grep .'
if [ ${#cpp[@]} -gt 0 ]; then
    run "Qt string connections" "Lint, warning only" python3 "$lint/qt_connections.py" \
        --files "${cpp[@]}" --log-dir /work/logs --report-file "$report"
else
    say "Qt string connections" SKIPPED "(no C++ files)"
fi
if [ ${#files[@]} -gt 0 ]; then
    run "codespell" "Lint, warning only" python3 "$lint/codespell.py" --files "${files[@]}" \
        --ignore-words /work/tools/.github/codespellignore \
        --skip "./.git*,*.po,*.ts,*.svg,./src/3rdParty,./src/Base/swig*,./src/Mod/Robot/App/kdl_cp,./src/Mod/Import/App/SCL*,./src/Doc/FreeCAD.uml,./build/" \
        --log-dir /work/logs --report-file "$report"
else
    say "codespell" SKIPPED "(no changed files)"
fi
if [ ${#py[@]} -gt 0 ]; then
    run "pylint" "Lint, warning only" python3 "$lint/pylint.py" --files "${py[@]}" \
        --disable C0302,C0303 --log-dir /work/logs --report-file "$report"
else
    say "pylint" SKIPPED "(no Python files)"
fi
say "clang-tidy" SKIPPED "(needs a configured build: the skill's CI page, the build tier)"
say "binding stub smoke check" SKIPPED "(needs pixi: the skill's CI page)"
echo "checks done"
exit "$failed"
INNER
status=${PIPESTATUS[0]}
set -e
# A run that printed no verdicts ran nothing: never a pass
if ! grep -q '^checks done$' "$work/summary.txt"; then
    echo "freecad-checks: the container ran no checks (exit $status): see the lines above" >&2
    [ "$status" -eq 0 ] && status=2
fi
echo "freecad-checks: exit $status (logs in $work/logs)"
exit "$status"
