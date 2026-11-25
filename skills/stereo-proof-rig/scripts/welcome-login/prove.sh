#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# prove.sh OUT: ORDER 63/720 milestone 1, step 4, every row from fresh logins, one container per case, one case at a time.
# Needs the lane's images (kw63-rig:published from mkrig.sh, kw63-rig:published-iso: the same with the ISO's last step,
# sparky-stereo-info's postinst run again; kw63-rig:candidate from mkcandidate.sh), the fake input client (FAKEINPUT_DIR),
# the first page's stereo picture (SOURCE), the three packages (DEBS) and the mockup pages (MOCKS).
# Environment: DOCKER_HOST, RENDER_GROUP, CONTAINER_IDS, FAKEINPUT_DIR, RIG_SCRIPTS, SOURCE, DEBS, MOCKS.
# Writes OUT/rows.tsv (row, claim, expected, measured, verdict) and exits 1 when a row is not as expected.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$(mkdir -p "${1:?output folder}" && cd "$1" && pwd)
[ -z "$(ls -A "$OUT")" ] || { echo "$OUT is not empty: give a new folder" >&2; exit 2; }
: "${SOURCE:?}" "${DEBS:?}" "${MOCKS:?}"
echo "start $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg)" > "$OUT/load.txt"
M="python3 -I $HERE/measure-welcome.py"
case_() { local name=$1 img=$2; shift 2; bash "$HERE/run-case.sh" "$img" "$OUT/$name" "$@" >> "$OUT/cases.log" 2>&1 || echo "case $name exit $?" >> "$OUT/cases.log"; }
printf 'row\tclaim\texpected\tmeasured\tverdict\n' > "$OUT/rows.tsv"
fails=0
row() { # row ID CLAIM EXPECTED MEASURED
	local v=FAIL; [ "$3" = "$4" ] && v=PASS; [ "$v" = PASS ] || fails=$((fails + 1))
	printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$v" >> "$OUT/rows.tsv"
}
added() { # the first-run windows KWin added in a login, sorted: "plasma-welcome yad", "yad", "none"
	local s; s=$(grep -o -E 'SPLASHLOG [0-9.]+ active=[^ ]* ADDED (org.kde.plasma-welcome|yad) ' "$1/session.log" 2>/dev/null | awk '{print $5}' | sed 's/org.kde.//' | sort -u | tr '\n' ' ' | sed 's/ $//')
	echo "${s:-none}"
}
verdict() { python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('verdict','none'))" "$1" 2>/dev/null || echo error; }

# the published set: a fresh install by apt, and the ISO's state (its pack step reinstalls sparky-stereo-info last)
case_ red-apt kw63-rig:published MODE=3d WAIT=40 AFTER=10 LOGINS=2
case_ red-iso kw63-rig:published-iso MODE=3d WAIT=40 AFTER=10 LOGINS=2
row R1 "published set, apt install: first-run windows at the first login" "plasma-welcome yad" "$(added "$OUT/red-apt/login1")"
row R2 "published set, ISO state: first-run windows at the first login" "yad" "$(added "$OUT/red-iso/login1")"
row R3 "published set, ISO state: first-run windows at the second login" "none" "$(added "$OUT/red-iso/login2")"

# the candidate: the first login on a 3D output, the pages driven, the button clicked, then the second login
case_ green-3d kw63-rig:candidate MODE=3d WAIT=40 AFTER=8 LOGINS=2 DRIVE=1 BUTTON_AT=119,284
G=$OUT/green-3d/login1
row R4 "candidate: first-run windows at the first login (Sparky Welcome leaves it in milestone 2)" "plasma-welcome yad" "$(added "$G")"
row R5 "candidate: first-run windows at the second login" "none" "$(added "$OUT/green-3d/login2")"
row R6 "candidate: the person's LastSeenVersion after the first login" "LastSeenVersion=6.7.4" "$(grep -o 'LastSeenVersion=.*' "$G/plasma-welcomerc.after" 2>/dev/null || echo none)"
row R7 "the Welcome window has the focus once the pointer rests on it" "True" "$(python3 -c "import json,sys; print([w['active'] for w in json.load(open(sys.argv[1]))['windows'] if w['cls']=='org.kde.plasma-welcome'][0])" "$G/windows.json" 2>/dev/null || echo none)"
$M page1 "$G/page1-Virtual-0.png" "$G/windows.json" "$SOURCE" > "$OUT/page1-3d.json" 2>&1
row R8 "first page, 3D output: the picture a pair of its own views, 0 differing pixels outside it" "PASS" "$(verdict "$OUT/page1-3d.json")"
case_ green-2d kw63-rig:candidate MODE=2d WAIT=40 AFTER=8 LOGINS=1 DRIVE=1
H=$OUT/green-2d/login1
$M page2 "$G/page2-Virtual-0.png" "$G/windows.json" 10 "$H/page2-Virtual-0.png" > "$OUT/page2-3d.json" 2>&1
row R9 "pointer page, 3D output, sunk limit 10: the window behind -1 left, +1 right of its 2D place, the rest at 0" "PASS" "$(verdict "$OUT/page2-3d.json")"
$M flat2d "$H/page1-Virtual-0.png" "$H/windows.json" "$SOURCE" "$OUT/page1-3d.json" > "$OUT/page1-2d.json" 2>&1
row R10 "first page, 2D output: one picture, the source's left view" "PASS" "$(verdict "$OUT/page1-2d.json")"
row R11 "2D output: the capture is one picture" "false" "$(head -1 "$H/shots.jsonl" | python3 -c "import json,sys; print(str(json.loads(sys.stdin.read())['stereo']).lower())" 2>/dev/null || echo none)"
row R12 "the button Open Window Behavior opens System Settings on Window Behavior" "Window Behavior" "$(python3 -c "
import json, sys
ws = json.load(open(sys.argv[1]))['windows']
print(next((w['caption'].split(' — ')[0] for w in ws if w['cls'] == 'systemsettings'), 'none'))" "$G/windows-after-click.json" 2>/dev/null || echo none)"

# the person's own limits move the drawing with them (sunk 20: -2 and +2)
case_ green-3d-sunk20 kw63-rig:candidate MODE=3d WAIT=40 AFTER=8 LOGINS=1 DRIVE=1 SUNK=20 POPPED=8
K=$OUT/green-3d-sunk20/login1
$M page2 "$K/page2-Virtual-0.png" "$K/windows.json" 20 "$H/page2-Virtual-0.png" > "$OUT/page2-3d-sunk20.json" 2>&1
row R13 "pointer page at the person's sunk limit 20: the window behind -2 left, +2 right" "PASS" "$(verdict "$OUT/page2-3d-sunk20.json")"
$M page2 "$K/page2-Virtual-0.png" "$K/windows.json" 10 "$H/page2-Virtual-0.png" > "$OUT/page2-3d-sunk20-as-10.json" 2>&1
row R14 "the measure fails on a wrong prediction (the sunk-20 login measured as sunk 10)" "FAIL" "$(verdict "$OUT/page2-3d-sunk20-as-10.json")"

# KDE's own first page, 2D output: Debian's plasma-welcome against the edition's, pixel for pixel
case_ kde-page-debian kw63-rig:published MODE=2d WAIT=40 AFTER=6 LOGINS=1 MOCK_PAGES=Welcome
case_ kde-page-ours kw63-rig:candidate MODE=2d WAIT=40 AFTER=6 LOGINS=1 MOCK_PAGES=Welcome
row R15 "KDE's own Welcome page on a 2D output: differing pixels, Debian's build against ours" "0" "$(python3 -c "
import json, sys
import numpy as np
from PIL import Image
def frame(p):
    return [w['fg'] for w in json.load(open(p))['windows'] if w['cls'] == 'org.kde.plasma-welcome'][0]
a, b = sys.argv[1], sys.argv[2]
fa, fb = frame(a + '/windows-mock.json'), frame(b + '/windows-mock.json')
if fa != fb: print('frames differ', fa, fb); sys.exit()
x, y, w, h = fa
A = np.asarray(Image.open(a + '/mock-1-Welcome-Virtual-0.png').convert('RGB')).astype(int)[y:y + h, x:x + w]
B = np.asarray(Image.open(b + '/mock-1-Welcome-Virtual-0.png').convert('RGB')).astype(int)[y:y + h, x:x + w]
print(int((np.abs(A - B).sum(axis=2) > 0).sum()))" "$OUT/kde-page-debian/login1" "$OUT/kde-page-ours/login1" 2>&1 | tail -1)"

# the upgrade from the ISO's state: the file that kept the Welcome Center closed goes, an administrator's file stays
mkdir -p "$OUT/upgrade"; name=kw63-upgrade-$$
docker create --name "$name" --ulimit core=1 --cpus 4 --user 0 --network none --mount "type=bind,src=$DEBS,dst=/extra,readonly" \
	--mount "type=bind,src=$OUT/upgrade,dst=/logs" kw63-rig:published-iso sh -c 'export DEBIAN_FRONTEND=noninteractive
grep -c "^# sparky-stereo-info" /etc/xdg/plasma-welcomerc > /logs/marked-before.txt
dpkg -i /extra/*.deb > /logs/dpkg.txt 2>&1; echo $? > /logs/dpkg-exit.txt
[ -e /etc/xdg/plasma-welcomerc ] && echo present > /logs/after.txt || echo gone > /logs/after.txt
printf "[General]\nLastSeenVersion=6.7.4\n" > /etc/xdg/plasma-welcomerc
dpkg -i /extra/sparky-stereo-info_*.deb > /logs/dpkg2.txt 2>&1
[ -e /etc/xdg/plasma-welcomerc ] && echo kept > /logs/admin.txt || echo removed > /logs/admin.txt
chown -R 1000:1000 /logs' > /dev/null
docker inspect -f '{{.Id}}' "$name" >> "$CONTAINER_IDS"; docker start -a "$name" >> "$OUT/cases.log" 2>&1; docker rm -f "$name" > /dev/null
row R16 "upgrade from the ISO state: the marked /etc/xdg/plasma-welcomerc" "1 gone 0" "$(cat "$OUT/upgrade/marked-before.txt") $(cat "$OUT/upgrade/after.txt") $(cat "$OUT/upgrade/dpkg-exit.txt")"
row R17 "upgrade: a plasma-welcomerc without the mark (an administrator's) stays" "kept" "$(cat "$OUT/upgrade/admin.txt")"

# the mockups of the remaining pages, drawn in the same session (not shipped)
RUN_MOUNTS="$MOCKS:/usr/share/plasma/plasma-welcome/extra-pages:ro" bash "$HERE/run-case.sh" kw63-rig:candidate "$OUT/mockups" \
	MODE=3d WAIT=40 AFTER=6 LOGINS=1 MOCK_PAGES=02-Touch,03-Sparky,04-Testers >> "$OUT/cases.log" 2>&1 || echo "case mockups exit $?" >> "$OUT/cases.log"
row R18 "mockups captured (touch, SparkyLinux's elements, testers)" "3" "$(ls "$OUT/mockups/login1"/mock-*-Virtual-0.png 2>/dev/null | wc -l)"

echo "end $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg)" >> "$OUT/load.txt"
column -t -s $'\t' "$OUT/rows.tsv"
echo "rows not as expected: $fails"
[ "$fails" = 0 ]
