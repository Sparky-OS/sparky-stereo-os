#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# clean-machine.sh: prove the skills check and the hooks on a machine that has nothing but this repository.
#
#   sh hooks/tests/clean-machine.sh        from a checkout or an unpacked snapshot, as any user
#
# It needs python3, python3-yaml and git, and uses exiftool when it is installed. No network, no AI tool.
# It makes a toy workspace in the default layout under a temporary folder, with each hook's configuration made from
# its example, and writes nowhere else: the repository can be mounted read-only.
# It prints one PASS or FAIL line per step and exits 1 when any step failed.
set -eu
REPO=$(cd "$(dirname "$0")/../.." && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
W=$WORK/workspace
export PYTHONDONTWRITEBYTECODE=1
unset SPARKY_WORKSPACE SPARKY_HOOKS_CONFIG_DIR SPARKY_HOOK_DIALECT SPARKY_PUBLISH_CHECK_CONFIG 2>/dev/null || true
failed=0
cd "$REPO"

step() { printf '\n== %s\n' "$1"; }
pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failed=1; }
run() { # run LABEL LINES COMMAND...: the command's own exit status decides; its last LINES lines are shown
	label=$1
	lines=$2
	shift 2
	if "$@" >"$WORK/out.txt" 2>&1; then status=PASS; else status=FAIL; failed=1; fi
	tail -n "$lines" "$WORK/out.txt" | sed 's/^/    /'
	printf '%s  %s\n' "$status" "$label"
}
expect() { # expect WHAT WANTED GOT
	if [ "$2" = "$3" ]; then pass "$1: $3"; else fail "$1: wanted $2, got $3"; fi
}
# the answer of a hook: "deny", "ask", "context", "notice" or "nothing"
answer() {
	python3 -c '
import json, sys
text = sys.stdin.read().strip()
out = json.loads(text) if text else {}
specific = out.get("hookSpecificOutput") or {}
print(specific.get("permissionDecision") or ("context" if specific.get("additionalContext") else "notice" if out.get("systemMessage") else "nothing"))'
}
event() { # event NAME TOOL TOOL_INPUT_JSON
	printf '{"hook_event_name":"%s","tool_name":"%s","tool_input":%s,"session_id":"clean-machine","transcript_path":"%s/session.jsonl","cwd":"%s"}' "$1" "$2" "$3" "$WORK" "$WORK"
}
hook() { python3 "$REPO/hooks/$1/hook.py" --config "$W/private/hooks/$1.json"; }

step "1. the skills check, with the description window"
run "check-skills.py" 1 python3 tools/check-skills.py
run "check-skills.py --anchors: every local link with a fragment lands on a heading" 1 python3 tools/check-skills.py --anchors
if python3 tools/check-skills.py --count >"$WORK/count.txt"; then pass "check-skills.py --count: no description over a limit"; else fail "a description is over a limit"; fi
head -n 3 "$WORK/count.txt" | sed 's/^/    /'

step "2. the tests of the checker and of the token counter"
run "tools/tests/test_check_skills.py" 3 python3 tools/tests/test_check_skills.py

step "3. every hook's tests"
run "hooks/tests/run.py" 1 python3 hooks/tests/run.py

step "4. a toy workspace in the default layout, each configuration from its example"
python3 hooks/install.py init "$W" >"$WORK/init.out" || fail "install.py init"
expect "configurations written" 7 "$(grep -c '^wrote' "$WORK/init.out")"
for name in check-every-default one-format-inside how-we-write-upstream; do printf 'A fact of the toy workspace.\n' >"$W/memory/$name.md"; done
run "install.py check" 1 python3 hooks/install.py check "$W"
( cd "$W" && find . -maxdepth 3 | sort | sed 's/^/    /' )

step "5. the wiring for Claude Code, written to a settings file and run as a shell runs it"
python3 hooks/install.py wire claude "$W" --write "$WORK/settings.json" >/dev/null || fail "install.py wire"
python3 - "$WORK/settings.json" "$WORK" <<'PY' && pass "every wired command ran and answered" || fail "a wired command failed"
import json, subprocess, sys
settings, work = json.load(open(sys.argv[1])), sys.argv[2]
event = {"session_id": "wired", "transcript_path": work + "/wired.jsonl", "cwd": work, "hook_event_name": "PreToolUse",
         "tool_name": "Bash", "tool_input": {"command": "ls"}}
count = 0
for name, groups in settings["hooks"].items():
    for group in groups:
        for handler in group["hooks"]:
            r = subprocess.run(handler["command"], shell=True, input=json.dumps(dict(event, hook_event_name=name)), capture_output=True, text=True)
            assert r.returncode == 0 and r.stderr == "" and "could not run" not in r.stdout, (handler["command"], r.stdout, r.stderr)
            count += 1
print(f"    {count} handlers in {len(settings['hooks'])} events")
PY

step "6. design-reading: refused, two reads, passes"
expect "a command before the reading" deny "$(event PreToolUse Bash '{"command":"ls"}' | hook design-reading | answer)"
event PostToolUse Read "{\"file_path\":\"$W/memory/check-every-default.md\"}" | hook design-reading
expect "after one of two files" deny "$(event PreToolUse Bash '{"command":"ls"}' | hook design-reading | answer)"
event PostToolUse Read "{\"file_path\":\"$W/memory/one-format-inside.md\"}" | hook design-reading
expect "after both files" nothing "$(event PreToolUse Bash '{"command":"ls"}' | hook design-reading | answer)"

step "7. outreach-guard: refuse, read, consult, pass"
SEND='{"command":"gh pr create --repo FFmpeg/FFmpeg --title x --body-file body.md"}'
event PreToolUse Bash "$SEND" | hook outreach-guard >"$WORK/refusal.json"
expect "the command, with nothing read" deny "$(answer <"$WORK/refusal.json")"
python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["hookSpecificOutput"]["permissionDecisionReason"])' "$WORK/refusal.json" | sed 's/^/    /'
for file in "$REPO/skills/upstream-outreach/SKILL.md" "$REPO/skills/contrib-ffmpeg/SKILL.md" "$W/memory/how-we-write-upstream.md"; do
	event PostToolUse Read "{\"file_path\":\"$file\"}" | hook outreach-guard
done
expect "the three files read, no consult yet" deny "$(event PreToolUse Bash "$SEND" | hook outreach-guard | answer)"
event PostToolUse mcp__reference__consult_knowledge '{"query":"frame packing"}' | hook outreach-guard
expect "read and consulted" context "$(event PreToolUse Bash "$SEND" | hook outreach-guard | answer)"
expect "a read of the same project passes at once" nothing "$(event PreToolUse Bash '{"command":"gh pr view 1 --repo FFmpeg/FFmpeg"}' | hook outreach-guard | answer)"
expect "refusals logged" 2 "$(grep -c 'gh pr create' "$W/state/hooks/outreach-guard/refused.log")"
expect "passes logged" 1 "$(grep -c 'gh pr create' "$W/state/hooks/outreach-guard/passed.log")"

step "8. a hook without its configuration lets the action through and says so"
expect "no configuration" notice "$(event PreToolUse Bash '{"command":"ls"}' | XDG_STATE_HOME="$WORK/xdg" python3 hooks/disk-floors/hook.py --config "$WORK/absent.json" | answer)"

step "9. the publish check on this section and both skills, with the example configuration"
files=$(find hooks skills/making-skills skills/development-hooks tools/tests tools/check-skills.py tools/skill-window/wordpiece.py tools/skill-window/regenerate.py tools/skill-window/README.md -type f ! -name '*.pyc' | sort)
# shellcheck disable=SC2086
out=$(python3 hooks/publish-check/publish_check.py --config "$W/private/hooks/publish-check.json" --files $files) || true
expect "$(printf '%s\n' "$files" | wc -l) files" "publish-check: clean" "$out"

printf '\n'
if [ "$failed" = 0 ]; then echo "clean-machine proof: every step passed"; else echo "clean-machine proof: FAILED, see the FAIL lines above"; fi
exit "$failed"
