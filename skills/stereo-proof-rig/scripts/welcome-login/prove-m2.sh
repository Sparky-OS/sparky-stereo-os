#!/bin/bash
# prove-m2.sh OUT [STEP ...]: ORDER 63/720 milestone 2, every case in a fresh container, one row per claim in OUT/rows.tsv
# (step, row, claim, expected, measured, PASS or FAIL, evidence), the load at start and end in OUT/load.txt; exits 1 when
# a row is not as expected. STEP: m1 m2 m3 m4 m5 m6 m7 m8 m9 (all when none is named). Cases run one after another.
# Images: kw63-rig:published (the published set by apt), kw63-rig:published-iso (the ISO's state), kw63-rig:published-apps
# (published, with Koko, the stereo wallpaper, Calamares and Dolphin), kw63-rig:layer1233 (that, with stereo-layer
# 1.23.3, the staged layer), kw63-rig:published-variety (published-apps with Stereo Variety and its indicator library, as
# the ISO installs the desktop meta with its Recommends), kw63-rig:candidate (published-variety with the successors),
# kw63-rig:candidate-iso (the ISO's state with the successors), kw63-rig:candidate-lang (candidate with ten locales).
# Environment: DOCKER_HOST, RENDER_GROUP, CONTAINER_IDS, FAKEINPUT_DIR, RIG_SCRIPTS, PICS (the folder of the first
# page's any-screen.pns).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$(mkdir -p "${1:?output folder}" && cd "$1" && pwd); shift
[ -z "$(ls -A "$OUT")" ] || { echo "$OUT is not empty" >&2; exit 1; }
STEPS=${*:-m1 m2 m3 m4 m5 m6 m7 m8 m9}
: "${PICS:?}" "${RIG_SCRIPTS:?}" "${TESTS:?the welcome recipe tests folder}" "${HTTPS_ONLY_APT:?}" "${REPO:?}"
# M7: TREE (the build clone), APTCONF (the published apt configuration of sparky-stereo-apt), PLAN (apt's plan of the
# candidate over the published set, mklayer.sh's plan.txt)
: "${TREE:?}" "${APTCONF:?}" "${PLAN:?}"
echo "start $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg)" > "$OUT/load.txt"
printf 'step\trow\tclaim\texpected\tmeasured\tresult\tevidence\n' > "$OUT/rows.tsv"
bad=0
row() { # step row claim expected measured evidence
	local r=PASS; [ "$4" = "$5" ] || { r=FAIL; bad=$((bad + 1)); }
	printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" "$r" "$6" >> "$OUT/rows.tsv"
	echo "$1 $2 $r: $3 (expected [$4], measured [$5])"
}
run() { # case image VAR=VALUE...
	local c=$1 img=$2; shift 2
	bash "$HERE/run-case.sh" "$img" "$OUT/$c" "$@" >> "$OUT/cases.log" 2>&1 || echo "case $c: exit $?" >> "$OUT/cases.log"
}
verdict() { python3 "$HERE/eyes-align.py" "$@" > "$1.align.json" 2>/dev/null; python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['verdict'])" "$1.align.json" 2>/dev/null || echo none; }
logline() { grep -h "$2" "$1" 2>/dev/null | head -1 | sed 's/.*\(stereoActive=[a-z]*\).*/\1/'; }
note() { # step row claim measured evidence: a measurement recorded beside the rows, neither PASS nor FAIL (what the rig does
	# not settle: the task bar under a fake touch screen gave different answers in different runs)
	printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "-" "$4" "NOTE" "$5" >> "$OUT/rows.tsv"
	echo "$1 $2 NOTE: $3 (measured [$4])"
}
opened() { # the first-run windows KWin added in a login (or only the class named), sorted: "plasma-welcome yad", "none"
	local s; s=$(grep -o -E 'SPLASHLOG [0-9.]+ active=[^ ]* ADDED (org.kde.plasma-welcome|yad) ' "$1" 2>/dev/null | awk '{print $5}' | sed 's/org.kde.//' | sort -u | tr '\n' ' ' | sed 's/ $//')
	[ -n "${2:-}" ] && { case " $s " in *" $2 "*) s=$2 ;; *) s= ;; esac; }
	echo "${s:-none}"
}
# a field of page-clicks.sh's results ($R): field PAGE NAME FIELD
field() { awk -F'\t' -v p="$1" -v n="$2" -v f="$3" '$1 == p && $2 == n { for (i = 3; i <= NF; i++) if (index($i, f "=") == 1) print substr($i, length(f) + 2) }' "$R" | head -1; }
PAGES_MOUNT="$HERE/m1-pages:/usr/share/plasma/plasma-welcome/extra-pages:ro $PICS:/diag:ro"

if [[ " $STEPS " == *" m1 "* ]]; then
	# M1: a StereoPicture under clips that hold it (a Welcome page in Kirigami's ColumnView), and under one that cuts it
	for img in layer1233 candidate; do
		RUN_MOUNTS="$PAGES_MOUNT" run m1-clip-$img kw63-rig:$img QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 MOCK_PAGES=90-ClipHolds.qml,91-ClipCuts.qml
		d=$OUT/m1-clip-$img/login1
		want=$([ $img = candidate ] && echo true || echo false)
		row m1 holds-$img "picture under clips that hold it, stereo-layer $([ $img = candidate ] && echo 1.23.4 || echo 1.23.3): stereoActive" "stereoActive=$want" "$(logline $d/mock-welcome.log 'DIAG holds')" "$d/mock-welcome.log"
		want=$([ $img = candidate ] && echo pair || echo "one view")
		row m1 holds-eyes-$img "the same picture in the captured eyes" "$want" "$(verdict $d/mock-1-90-ClipHolds.qml-Virtual-0.png window:org.kde.plasma-welcome:$d/windows-mock.json)" "$d/mock-1-90-ClipHolds.qml-Virtual-0.png"
		row m1 cuts-$img "picture under a clip that cuts it: stereoActive" "stereoActive=false" "$(logline $d/mock-welcome.log 'DIAG cuts')" "$d/mock-welcome.log"
		row m1 cuts-eyes-$img "the cut picture in the captured eyes" "one view" "$(verdict $d/mock-2-91-ClipCuts.qml-Virtual-0.png window:org.kde.plasma-welcome:$d/windows-mock.json)" "$d/mock-2-91-ClipCuts.qml-Virtual-0.png"
		said=$(grep -c 'StereoPicture file:///diag/any-screen.pns: QQuickItem.*clips it, so the picture is shown flat' $d/mock-welcome.log 2>/dev/null)
		row m1 cuts-told-$img "the log says why the cut picture is flat (lines)" "$([ $img = candidate ] && echo 1 || echo 0)" "${said:-0}" "$d/mock-welcome.log"
	done
	# M1: the other programs with a StereoPicture in QML, on the published set (1.22.0) and with 1.23.4
	for img in published-apps candidate; do
		RUN_MOUNTS="$PICS:/diag:ro" run m1-koko-$img kw63-rig:$img QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 APP_WAIT=18 "APP_CMD=koko /diag/any-screen.pns"
		d=$OUT/m1-koko-$img/login1
		row m1 koko-$img "Koko's viewer, a stereo picture ($img)" "pair" "$(verdict $d/app-Virtual-0.png window:org.kde.koko:$d/windows-app.json)" "$d/app-Virtual-0.png"
		RUN_MOUNTS="$PICS:/diag:ro" run m1-wallpaper-$img kw63-rig:$img QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 APP_WAIT=15 "APP_CMD=python3 /lane/set-wallpaper.py org.sparky.stereoimage file:///diag/any-screen.pns"
		d=$OUT/m1-wallpaper-$img/login1
		row m1 wallpaper-$img "the stereo wallpaper, a stereo picture ($img)" "pair" "$(verdict $d/app-Virtual-0.png 400,100,1300,800)" "$d/app-Virtual-0.png"
		RUN_MOUNTS="$HERE/calamares-cfg:/calamares-cfg:ro" run m1-calamares-$img kw63-rig:$img QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 APP_WAIT=40 "APP_CMD=calamares -d -c /calamares-cfg"
		d=$OUT/m1-calamares-$img/login1
		row m1 calamares-$img "the installer's slideshow ($img)" "pair" "$(verdict $d/app-Virtual-0.png window:io.calamares.calamares:$d/windows-app.json)" "$d/app-Virtual-0.png"
	done
fi

if [[ " $STEPS " == *" m2 "* ]]; then
	# M2: real clicks on every button and link of the three new pages (a stand-in browser records addresses, a stand-in
	# pkexec the commands that ask for root); and a program that is missing is said on the page
	SP=05-SparkyWorld.qml; HP=06-HelpTest.qml; TP=01-TouchAndTabletMode.qml
	clicks="$SP:home:190,228 $SP:forums:465,228 $SP:wiki:190,266 $SP:git:465,266 $SP:donate:190,304 $SP:sponsors:465,304"
	clicks="$clicks $SP:appcenter:190,342 $SP:about:190,380 $SP:system:465,380"
	clicks="$clicks $SP:facebook:86,440 $SP:x:148,440 $SP:mewe:199,440 $SP:telegram:274,440 $SP:reddit:350,440 $SP:patreon:421,440"
	clicks="$clicks $SP:mastodon:504,440 $SP:signal:76,466 $SP:wikipedia:152,466 $SP:rss:222,466"
	# Upgrade last: the rig stops its password window, the helper then fails, and the page says so above the buttons
	clicks="$clicks $SP:upgrade:465,342"
	clicks="$clicks $HP:report:317,364 $HP:copy:327,330 $TP:general:112,229 $TP:keyboard:296,229"
	# a session where the hardware layer says a touch screen is there, so the touch page shows (Daniel, 2026-11-25)
	run m2-clicks kw63-rig:candidate QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 STANDIN_PKEXEC=1 USER_SETUP=/lane/m2-setup.sh APP_WAIT=230 SPARKY_STEREO_HAS_TABLET_MODE=/bin/true \
		"PAGES=$SP,$HP,$TP" "CLICKS=$clicks" "APP_CMD=bash /lane/page-clicks.sh"
	R=$OUT/m2-clicks/clicks/results.tsv
	for spec in home=https://sparkylinux.org/ forums=https://forum.sparkylinux.org/ wiki=https://wiki.sparkylinux.org/ \
		git=https://github.com/sparkylinux donate=https://sparkylinux.org/donate/ sponsors=https://sparkylinux.org/sponsoring/ \
		facebook=https://www.facebook.com/groups/SparkyLinux/ x=https://x.com/SparkyLinux mewe=https://mewe.com/join/sparkylinux \
		telegram=https://t.me/sparkylinux reddit=https://www.reddit.com/r/SparkyLinuxOrg patreon=https://www.patreon.com/sparkylinux \
		mastodon=https://mastodon.social/@SparkyLinux \
		signal=https://signal.group/#CjQKIJTIFdCzG2za1ZC8TE8dxOkeMB_Q03oPTpddsEiVXtHdEhBZs7BP9ItOowNXF6J7GF4A \
		wikipedia=https://en.wikipedia.org/wiki/SparkyLinux rss=https://sparkylinux.org/feed/; do
		row m2 sparky-${spec%%=*} "SparkyLinux page, ${spec%%=*}: the address opened" "${spec#*=}" "$(field $SP ${spec%%=*} url)" "$R"
	done
	row m2 sparky-appcenter "SparkyLinux page, AppCenter: the command run as root" "/usr/bin/sparky-aptus-appcenter" "$(field $SP appcenter pkexec)" "$R"
	row m2 sparky-upgrade "SparkyLinux page, Upgrade: the command run as root" "/usr/bin/sparky-aptus-upgrade" "$(field $SP upgrade pkexec)" "$R"
	row m2 sparky-upgrade-said "Upgrade's helper stopped in the rig: the page says the command failed (the log line)" "1" "$(grep -c 'The command "/usr/bin/sparky-stereo-welcome-upgrade" failed' $OUT/m2-clicks/clicks/welcome-$SP.log)" "$OUT/m2-clicks/clicks/$SP-upgrade.png"
	row m2 sparky-upgrade-locale "Upgrade at its first use: then the languages, through spsudo's password window" "yad" "$(field $SP upgrade windows | cut -d'|' -f1)" "$R"
	row m2 sparky-about "SparkyLinux page, About: the window that opens" "yad" "$(field $SP about windows | cut -d'|' -f1)" "$R"
	row m2 sparky-system "SparkyLinux page, System info: the window that opens" "yad" "$(field $SP system windows | cut -d'|' -f1)" "$R"
	row m2 help-copy "Help Test page, Copy: the clipboard holds stereo-display-info's text" "yes" "$(field $HP copy clipboard | grep -q 'Compositor stereo'          && echo yes || echo no)" "$R"
	row m2 help-report "Help Test page, Report a problem: the address opened" "https://github.com/Sparky-OS/sparky-stereo-os/issues" "$(field $HP report url)" "$R"
	row m2 touch-general "Touch page, Open General Behavior: the window" "systemsettings|General Behavior — System Settings" "$(field $TP general windows)" "$R"
	row m2 touch-keyboard "Touch page, Open Virtual Keyboard: the window" "systemsettings|Virtual Keyboard — System Settings" "$(field $TP keyboard windows)" "$R"
	# a program the page runs is missing: the page says so (Plasma Welcome's own words, in its log too)
	RUN_MOUNTS="$HERE/missing-program:/usr/bin/sparky-system:ro" run m2-missing kw63-rig:candidate QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 \
		USER_SETUP=/lane/m2-setup.sh APP_WAIT=30 "PAGES=$SP" "CLICKS=$SP:system:465,380" "APP_CMD=bash /lane/page-clicks.sh"
	row m2 missing-said "a missing program: the page's message (the log line)" "1" "$(grep -c 'The command "/usr/bin/sparky-system" could not be found' $OUT/m2-missing/clicks/welcome-$SP.log)" "$OUT/m2-missing/clicks/$SP-system.png"
fi

if [[ " $STEPS " == *" m3 "* ]]; then
	# M3: what a mouse click and a tap of one finger do, under KDE's default click setting and under single click
	for click in default single; do
		run m3-touch-$click kw63-rig:candidate QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 USER_SETUP=/lane/touch-setup.sh \
			CLICK=$([ $click = default ] && echo "" || echo $click) ICON_AT=52,42 ITEM_AT=214,95 APP_WAIT=110 "APP_CMD=bash /lane/touch-measure.sh run"
		T=$OUT/m3-touch-$click/touch
		dolphin_caption() { python3 -c "
import json, sys
c = [w['caption'] for w in json.load(open(sys.argv[1]))['windows'] or [] if w['cls'] == 'org.kde.dolphin' and w['normal']]
print(c[0] if c else 'no Dolphin window')" "$1" 2>/dev/null || echo none; }
		active() { python3 -c "
import json, sys
c = [w['cls'] for w in json.load(open(sys.argv[1]))['windows'] or [] if w['active']]
print(c[0] if c else 'none')" "$1" 2>/dev/null || echo none; }
		menu() { python3 -c "
import json, sys
before = {w['internalId'] if 'internalId' in w else (w['cls'], tuple(w['fg'])) for w in json.load(open(sys.argv[1]))['windows'] or []}
after = json.load(open(sys.argv[2]))['windows'] or []
new = [w for w in after if w['cls'] in ('plasmashell', 'org.kde.plasmashell') and (w['cls'], tuple(w['fg'])) not in before]
print('menu' if new or any(w['active'] and w['cls'] in ('plasmashell', 'org.kde.plasmashell') for w in after) else 'no menu')" "$1" "$2" 2>/dev/null || echo none; }
		open_click=$([ $click = single ] && echo "TouchTest — Dolphin" || echo "no Dolphin window")
		row m3 desktop-click-$click "desktop icon, a mouse click ($click)" "$open_click" "$(dolphin_caption $T/folder-click.json)" "$T/folder-click.png"
		row m3 desktop-tap-$click "desktop icon, a tap ($click)" "TouchTest — Dolphin" "$(dolphin_caption $T/folder-tap.json)" "$T/folder-tap.png"
		in_click=$([ $click = single ] && echo "Inner — Dolphin" || echo "TouchTest — Dolphin")
		row m3 dolphin-click-$click "Dolphin item, a mouse click ($click)" "$in_click" "$(dolphin_caption $T/dolphin-click.json)" "$T/dolphin-click.png"
		row m3 dolphin-tap-$click "Dolphin item, a tap ($click)" "Inner — Dolphin" "$(dolphin_caption $T/dolphin-tap.json)" "$T/dolphin-tap.png"
		note m3 task-tap-$click "task bar, one tap on an inactive window's button: the active window ($click)" "$(active $T/tm-tap.json)" "$T/tm-tap.png"
		note m3 task-tap2-$click "task bar, two more taps on that button: the active window ($click)" "$(active $T/tm-tap2.json)" "$T/tm-tap2.png"
		row m3 task-click-$click "task bar, a mouse click on an inactive window's button: the active window ($click)" "org.kde.dolphin" "$(active $T/tm-click.json)" "$T/tm-click.png"
		note m3 task-hold-$click "task bar, a long touch on an inactive window's button ($click)" "$(menu $T/tm-click.json $T/tm-hold.json)" "$T/tm-hold.png"
	done
	# the touch page as shipped (Daniel, 2026-11-25: "Only with a touch screen"): shown where the hardware layer says a touch
	# screen of the computer's own is there, not where it says none, and not on the rig's own machine (no touch screen)
	for found in true false shipped; do
		if [ $found = shipped ]; then ov=; else ov=SPARKY_STEREO_HAS_TABLET_MODE=/bin/$found; fi
		run m3-cond-$found kw63-rig:candidate QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 $ov APP_WAIT=14 \
			PAGES=01-TouchAndTabletMode.qml,06-HelpTest.qml "APP_CMD=bash /lane/cond-check.sh"
		C=$OUT/m3-cond-$found/cond
		row m3 cond-mark-$found "hardware layer $([ $found = shipped ] && echo 'on the rig, unchanged' || echo "says $found"): the touch mark in the session's XDG_CONFIG_DIRS" "$([ $found = true ] && echo yes || echo no)" "$(grep -q sparky-stereo-welcome/touch-screen/xdg $C/xdg-config-dirs.txt && echo yes || echo no)" "$C/xdg-config-dirs.txt"
		row m3 cond-page-$found "the first page shown of Touch, Help Test" "$([ $found = true ] && echo touch || echo help)" "$(python3 $HERE/which-page.py $C/first.png $C/windows.json $HERE/refs)" "$C/first.png"
	done
fi

if [[ " $STEPS " == *" m4 "* ]]; then
	# M4 a: Sparky Welcome's first-run unit under a real user manager (systemd as PID 1)
	for img in published-apps candidate; do
		want=$([ $img = candidate ] && echo skipped || echo started)
		TESTS=$TESTS bash "$HERE/unit-case.sh" kw63-rig:$img "$OUT/m4-unit-$img" $want >> "$OUT/cases.log" 2>&1
		row m4 unit-$img "Sparky Welcome's first-run unit at a login ($img)" "exit 0" "$(tail -1 "$OUT/m4-unit-$img/test.txt")" "$OUT/m4-unit-$img/test.txt"
	done
	# M4 b: a new account on the candidate: what opens at the first and second login (the rig's session starts autostart
	# entries itself, with no user manager, so Sparky Welcome's start there is not the edition's: it is row a)
	run m4-new-candidate kw63-rig:candidate LOGINS=2 WAIT=45
	for n in 1 2; do
		want=$([ $n = 1 ] && echo plasma-welcome || echo none)
		row m4 new-login$n "a new account, login $n: the Welcome Center opens" "$want" "$(opened "$OUT/m4-new-candidate/login$n/session.log" plasma-welcome)" "$OUT/m4-new-candidate/login$n/session.log"
	done
	# M4 c: an account made before the upgrade (ISO's state, then apt), at its next login after it
	for base in iso apt; do
		src=$([ $base = iso ] && echo published-iso || echo published-variety)
		dst=$([ $base = iso ] && echo candidate-iso || echo candidate)
		run m4-$base-before kw63-rig:$src LOGINS=1 WAIT=45
		RUN_MOUNTS="$OUT/m4-$base-before/home:/seed:ro" run m4-$base-after kw63-rig:$dst LOGINS=1 WAIT=45 SEED_HOME=/seed
		row m4 $base-before "existing account ($base state), first login before the upgrade: first-run windows" "$([ $base = iso ] && echo yad || echo 'plasma-welcome yad')" "$(opened "$OUT/m4-$base-before/login1/session.log")" "$OUT/m4-$base-before/login1/session.log"
		row m4 $base-after "the same account after the upgrade, next login: the Welcome Center" "$([ $base = iso ] && echo plasma-welcome || echo none)" "$(opened "$OUT/m4-$base-after/login1/session.log" plasma-welcome)" "$OUT/m4-$base-after/login1/session.log"
		row m4 $base-marks "Sparky Welcome's mark kept after the upgrade" "yes" "$([ -e "$OUT/m4-$base-after/home/.config/autostart/sparky-welcome.desktop" ] && echo yes || echo no)" "$OUT/m4-$base-after/home/.config/autostart"
	done
fi

if [[ " $STEPS " == *" m5 "* ]]; then
	# M5: the live session's first run: the live user's own plasma-welcomerc from the welcome package's live-config hook,
	# then a login of that user (the rig cannot boot the live medium: the hook is run as live-config runs it)
	bash "$HERE/live-seed.sh" kw63-rig:candidate "$OUT/m5-live/seed" >> "$OUT/cases.log" 2>&1
	row m5 live-file "the hook writes the live user's plasma-welcomerc" "LiveEnvironment=true LiveInstaller=calamares" "$(grep -E '^Live' "$OUT/m5-live/seed/.config/plasma-welcomerc" 2>/dev/null | tr '\n' ' ' | sed 's/ $//')" "$OUT/m5-live/live-seed.txt"
	RUN_MOUNTS="$OUT/m5-live/seed:/seed:ro" run m5-live/session kw63-rig:candidate SEED_HOME=/seed LOGINS=1 WAIT=45 DRIVE=1
	D=$OUT/m5-live/session/login1
	row m5 live-mode "the live user's login: the Welcome Center started in its live mode" "yes" "$(grep -q 'plasma-welcome --live-environment' $D/processes.txt && echo yes || echo no)" "$D/processes.txt"
	row m5 live-first-page "its first page: KDE's live page with the installer" "live" "$(python3 $HERE/which-page.py $D/page1-Virtual-0.png $D/windows.json $HERE/refs)" "$D/page1-Virtual-0.png"
	row m5 live-second-page "its next page: the edition's first page, the picture a pair" "pair" "$(MEASURE_SCALE=1 verdict $D/page2-Virtual-0.png window:org.kde.plasma-welcome:$D/windows-page2.json)" "$D/page2-Virtual-0.png"
fi

if [[ " $STEPS " == *" m6 "* ]]; then
	# M6: one login per language, the first page and the pointer page captured; the words of the first page's heading
	# compared with the English login's
	for lang in en_US pt_BR es_ES fr_FR de_DE pl_PL ja_JP ko_KR zh_CN zh_TW; do
		run m6-$lang kw63-rig:candidate-lang LOGIN_LANG=$lang.UTF-8 LOGINS=1 WAIT=45 DRIVE=1
	done
	for lang in pt_BR es_ES fr_FR de_DE pl_PL ja_JP ko_KR zh_CN zh_TW; do
		D=$OUT/m6-$lang/login1
		row m6 heading-$lang "$lang: the first page's heading is not the English one" "translated" "$(python3 $HERE/heading-differs.py $OUT/m6-en_US/login1/page1-Virtual-0.png $OUT/m6-en_US/login1/windows.json $D/page1-Virtual-0.png $D/windows.json)" "$D/page1-Virtual-0.png"
		row m6 catalogue-$lang "$lang: the catalogue the session reads" "/usr/share/locale/${lang%%_*}$(case $lang in pt_BR|zh_CN|zh_TW) echo _${lang#*_};; esac)/LC_MESSAGES/sparky-stereo-welcome.mo" "$(grep -o '/usr/share/locale/[^ ]*sparky-stereo-welcome.mo' $D/catalogue.txt 2>/dev/null | head -1)" "$D/catalogue.txt"
	done
fi

if [[ " $STEPS " == *" m7 "* ]]; then
	# M7: the image's selection and apt's choice
	row m7 image-list "sparky-stereo-welcome in the image group (make-lists.py, made into sparky-stereo-desktop by make-meta.py)" "yes" "$(grep -qx sparky-stereo-welcome "$TREE/sparky-os/lists/image.list" && grep -q "'sparky-stereo-welcome'" "$TREE/sparky-os/lists/make-lists.py" && echo yes || echo no)" "$TREE/sparky-os/lists/image.list"
	row m7 version "plasma-welcome +stereo3d2 sorts after Debian's 6.7.4-1+b1" "yes" "$(dpkg --compare-versions 6.7.4-1+stereo3d2+lc1 gt 6.7.4-1+b1 && echo yes || echo no)" "dpkg --compare-versions"
	row m7 pin "the edition's tree is pinned at 1001 over Debian (published sparky-stereo-apt's preferences)" "1001" "$(awk '/^Package: \*$/{p=1} p && /^Pin: release o=Sparky Stereo OS$/{q=1} p && q && /^Pin-Priority:/{print $2; exit}' "$APTCONF/sparky-stereo")" "$APTCONF/sparky-stereo"
	row m7 inst "apt's plan over the published set: the packages installed" "8" "$(grep -c '^Inst' "$PLAN")" "$PLAN"
	row m7 remv "apt's plan over the published set: the packages removed" "0" "$(grep -c '^Remv' "$PLAN")" "$PLAN"
fi

if [[ " $STEPS " == *" m8 "* ]]; then
	# M8: 125 % (one output, 3D and 2D) and two outputs (both 3D); the first page's pair and the pointer page's drawing
	run m8-125-3d kw63-rig:candidate SCALE=1.25 LOGINS=1 WAIT=45 DRIVE=1
	run m8-125-2d kw63-rig:candidate SCALE=1.25 MODE=2d LOGINS=1 WAIT=45 DRIVE=1
	D=$OUT/m8-125-3d/login1; D2=$OUT/m8-125-2d/login1
	# the compositor resamples the pair at 125 %: each eye at least 20 dB from its own view and 5 dB nearer it than the other
	MEASURE_SCALE=1.25 MEASURE_MIN_DB=20 python3 $HERE/measure-welcome.py page1 $D/page1-Virtual-0.png $D/windows.json $PICS/any-screen.pns > $D/page1.json
	MEASURE_SCALE=1.25 python3 $HERE/measure-welcome.py page2 $D/page2-Virtual-0.png $D/windows-page2.json 10 $D2/page2-Virtual-0.png > $D/page2.json
	row m8 page1-125 "125 %: the first page's picture a pair of its own views, nothing else differing" "PASS" "$(python3 -c "import json; print(json.load(open('$D/page1.json'))['verdict'])" 2>/dev/null)" "$D/page1.json"
	row m8 page2-125 "125 %: the drawing's window behind -1/+1 device pixels, the rest at the screen" "PASS" "$(python3 -c "import json; print(json.load(open('$D/page2.json'))['verdict'])" 2>/dev/null)" "$D/page2.json"
	run m8-two-3d kw63-rig:candidate OUTPUTS=2 LOGINS=1 WAIT=45 DRIVE=1
	run m8-two-2d kw63-rig:candidate OUTPUTS=2 MODE=2d LOGINS=1 WAIT=45 DRIVE=1
	D=$OUT/m8-two-3d/login1; D2=$OUT/m8-two-2d/login1
	on=$(python3 $HERE/output-of.py $D/windows.json $D/session.log)
	ox=$(python3 $HERE/output-of.py $D/windows.json $D/session.log x)
	MEASURE_ORIGIN_X=$ox python3 $HERE/measure-welcome.py page1 $D/page1-$on.png $D/windows.json $PICS/any-screen.pns > $D/page1.json
	MEASURE_ORIGIN_X=$ox python3 $HERE/measure-welcome.py page2 $D/page2-$on.png $D/windows-page2.json 10 $D2/page2-$on.png > $D/page2.json
	row m8 page1-two "two outputs: the first page's picture a pair on the output it opens on ($on)" "PASS" "$(python3 -c "import json; print(json.load(open('$D/page1.json'))['verdict'])" 2>/dev/null)" "$D/page1.json"
	row m8 page2-two "two outputs: the drawing's window behind -1/+1, the rest at the screen" "PASS" "$(python3 -c "import json; print(json.load(open('$D/page2.json'))['verdict'])" 2>/dev/null)" "$D/page2.json"
fi

if [[ " $STEPS " == *" m9 "* ]]; then
	# M9: the three pages of 2026-11-25 (Daniel: "pick the ones you think are valuable enought to be there"): a real click on
	# each button, Variety's on a new account (its first start) and on one that started it before; the depth page's drawing
	# at the rig's limits (KWin's 10 sunk, 4 popped), the keys page flat; the wallpaper page's condition; the pages in four
	# languages
	DP=02-Your3DDepth.qml; WP=03-ChangingWallpaper.qml; KP=04-WindowsKeysAndSessions.qml
	for ran in 0 1; do
		run m9-clicks-ran$ran kw63-rig:candidate QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 USER_SETUP=/lane/m9-setup.sh VARIETY_RAN=$ran \
			APP_WAIT=90 "PAGES=$DP,$WP,$KP" "CLICKS=$DP:depth:93,338 $WP:variety:128,302 $KP:shortcuts:94,338 $KP:session:267,338" \
			"APP_CMD=bash /lane/page-clicks.sh"
	done
	R=$OUT/m9-clicks-ran0/clicks/results.tsv
	row m9 depth-open "depth page, Open 3D Depth: the window" "systemsettings|3D Depth — System Settings" "$(field $DP depth windows)" "$R"
	row m9 variety-first "wallpaper page, Open Variety's Preferences, Variety's first start: the window" "variety|Welcome to Variety!" "$(field $WP variety windows)" "$R"
	row m9 keys-shortcuts "keys page, Open Shortcuts: the window" "systemsettings|Shortcuts — System Settings" "$(field $KP shortcuts windows)" "$R"
	row m9 keys-session "keys page, Open Desktop Session: the window" "systemsettings|Desktop Session — System Settings" "$(field $KP session windows)" "$R"
	R=$OUT/m9-clicks-ran1/clicks/results.tsv
	row m9 variety-again "wallpaper page, Open Variety's Preferences, Variety started before: the window" "variety|Variety Preferences" "$(field $WP variety windows)" "$R"
	# the drawing: each part's shift between the eyes and whether it then aligns completely (eyes-align.py), on the frame
	C=$OUT/m9-clicks-ran0/clicks
	read -r fx fy < <(python3 -c "import json,sys; print(*[int(v) for v in [w for w in json.load(open(sys.argv[1]))['windows'] if w['cls'] == 'org.kde.plasma-welcome'][0]['fg'][:2]])" "$C/$DP-open.json" 2>/dev/null || echo 0 0)
	part() { python3 "$HERE/eyes-align.py" "$C/$DP-open.png" "$((fx + $1)),$((fy + $2)),$3,$4" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['best_shift'], d['verdict'])" 2>/dev/null || echo none; }
	row m9 depth-sun "depth page's drawing: the wallpaper's sun, its shift (the sunk limit, 10)" "10 one view" "$(part 405 383 45 35)" "$C/$DP-open.png"
	row m9 depth-window "depth page's drawing: the window's lines, its shift (the screen)" "0 one view" "$(part 240 430 80 40)" "$C/$DP-open.png"
	row m9 depth-menu "depth page's drawing: the menu, its shift (the popped limit, 4)" "-4 one view" "$(part 335 445 70 45)" "$C/$DP-open.png"
	row m9 keys-flat "keys page: its window the same in both eyes" "one view" "$(verdict $C/$KP-open.png window:org.kde.plasma-welcome:$C/$KP-open.json)" "$C/$KP-open.png"
	# the wallpaper page's condition: shown where Variety is installed, not where it is not (the env script's own test,
	# pointed at a program that is not there)
	for has in installed missing; do
		if [ $has = missing ]; then ov=SPARKY_STEREO_VARIETY=/nonexistent/variety; else ov=; fi
		run m9-cond-$has kw63-rig:candidate QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 $ov APP_WAIT=14 \
			PAGES=$WP,06-HelpTest.qml "APP_CMD=bash /lane/cond-check.sh"
		C=$OUT/m9-cond-$has/cond
		row m9 cond-mark-$has "Variety $has: the wallpaper mark in the session's XDG_CONFIG_DIRS" "$([ $has = installed ] && echo yes || echo no)" "$(grep -q sparky-stereo-welcome/variety/xdg $C/xdg-config-dirs.txt && echo yes || echo no)" "$C/xdg-config-dirs.txt"
		row m9 cond-page-$has "Variety $has: the first page shown of Wallpaper, Help Test" "$([ $has = installed ] && echo wallpaper || echo help)" "$(python3 $HERE/which-page.py $C/first.png $C/windows.json $HERE/refs)" "$C/first.png"
	done
	# the three pages in four languages, each heading against the English one
	for lang in en_US pt_BR de_DE ja_JP; do
		run m9-lang-$lang kw63-rig:candidate-lang LOGIN_LANG=$lang.UTF-8 QUIET_FIRST_RUN=1 LOGINS=1 WAIT=10 AFTER=4 APP_WAIT=40 \
			"PAGES=$DP,$WP,$KP" "APP_CMD=bash /lane/page-clicks.sh"
	done
	E=$OUT/m9-lang-en_US/clicks
	for lang in pt_BR de_DE ja_JP; do
		C=$OUT/m9-lang-$lang/clicks
		for pg in $DP $WP $KP; do
			row m9 heading-${pg%%-*}-$lang "$lang: the heading of $pg is not the English one" "translated" "$(python3 $HERE/heading-differs.py $E/$pg-open.png $E/$pg-open.json $C/$pg-open.png $C/$pg-open.json 2>/dev/null || echo none)" "$C/$pg-open.png"
		done
	done
fi

echo "end $(date -u +%FT%TZ) load $(cut -d' ' -f1-3 /proc/loadavg)" >> "$OUT/load.txt"
echo "rows: $(grep -c -P '\t(PASS|FAIL)\t' "$OUT/rows.tsv"), notes: $(grep -c -P '\tNOTE\t' "$OUT/rows.tsv"), not as expected: $bad"
[ "$bad" = 0 ]
