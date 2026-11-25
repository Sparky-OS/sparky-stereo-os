#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# prove.sh OUT: row 71's proof, one rerun. Every case is one fresh container and one new account's login on a 1920x1080
# virtual output of Stereo KWin (on the NVIDIA card), on a computer with a touch screen of its own (the hardware layer
# reads a sysfs fixture) in tablet mode unless the case says otherwise. RED is the published set (r1123a) with Gwenview,
# GREEN the same with the staged packages installed by apt. One row per claim in OUT/rows.tsv and OUT/rows.jsonl; the
# exit status is 1 when a row is not as expected. The load average is written at the start and the end.
# Environment: DOCKER_HOST (the lane's socket), RENDER_GROUP, CONTAINER_IDS, FAKEINPUT_DIR (the built fake input client),
# RIG_SCRIPTS (the skills' stereo-proof-rig/scripts), RED_IMAGE, GREEN_IMAGE; PARTS (optional: a space-separated subset of
# typing refuse absent hardware defaults retouch settings 3d).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
RIGD=$HERE/rig
OUT=${1:?an output folder that does not exist yet}
[ -e "$OUT" ] && { echo "$OUT exists: give a new folder" >&2; exit 2; }
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
: "${DOCKER_HOST:?}" "${RENDER_GROUP:?}" "${CONTAINER_IDS:?}" "${FAKEINPUT_DIR:?}" "${RIG_SCRIPTS:?}" "${RED_IMAGE:?}" "${GREEN_IMAGE:?}"
export DOCKER_HOST RENDER_GROUP CONTAINER_IDS FAKEINPUT_DIR RIG_SCRIPTS
PARTS=${PARTS:-typing refuse absent hardware defaults retouch settings 3d}
{ echo "start $(date -u +%FT%TZ) loadavg $(cut -d' ' -f1-3 /proc/loadavg)"; echo "red $RED_IMAGE $(docker image inspect -f '{{.Id}}' "$RED_IMAGE")"; echo "green $GREEN_IMAGE $(docker image inspect -f '{{.Id}}' "$GREEN_IMAGE")"; } > "$OUT/run.txt"
want() { case " $PARTS " in *" $1 "*) return 0 ;; esac; return 1; }
case_() { # case_ IMAGE DIR VAR=VALUE...
	local img=$1 dir=$2; shift 2
	bash "$RIGD/run-case.sh" "$img" "$OUT/$dir" "$@" >> "$OUT/cases.log" 2>&1
}
row() { # row STEP CLAIM RED GREEN EXPECTED_OK(0/1) EVIDENCE
	printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$([ "$5" = 1 ] && echo as-expected || echo NOT-AS-EXPECTED)" "$6" >> "$OUT/rows.tsv"
	python3 -c 'import json,sys; print(json.dumps(dict(zip(["step","claim","red","green","as_expected","evidence"], sys.argv[1:6] + [sys.argv[6]]), ensure_ascii=False)))' \
		"$1" "$2" "$3" "$4" "$([ "$5" = 1 ] && echo yes || echo no)" "$6" >> "$OUT/rows.jsonl"
}
res() { # res DIR KEY: a value of DIR/result.json
	python3 -c 'import json,sys
try: r = json.load(open(sys.argv[1]))
except Exception: print("no-result"); sys.exit()
v = r
for k in sys.argv[2].split("."):
    v = v.get(k) if isinstance(v, dict) else None
print(json.dumps(v, ensure_ascii=False))' "$OUT/$1/result.json" "$2"
}
printf 'step\tclaim\tred (control)\tgreen (this work)\tverdict\tevidence\n' > "$OUT/rows.tsv"
LANGS="en:en_US pt_BR:pt_BR es:es_ES fr:fr_FR de:de_DE pl:pl_PL ja:ja_JP ko:ko_KR zh_CN:zh_CN zh_TW:zh_TW"

if want typing; then
	for l in $LANGS; do
		c=${l%%:*}; loc=${l#*:}
		case_ "$RED_IMAGE" "red/type-$c" LOGIN_LANG="$loc.UTF-8" LANG_CASE="$c"
		case_ "$GREEN_IMAGE" "green/type-$c" LOGIN_LANG="$loc.UTF-8" LANG_CASE="$c"
		rs=$(res "red/type-$c" keyboard.shown); rk=$(res "red/type-$c" keyboard.kind); rt=$(res "red/type-$c" typed); ro=$(res "red/type-$c" ok)
		gs=$(res "green/type-$c" keyboard.shown); gk=$(res "green/type-$c" keyboard.kind); gt=$(res "green/type-$c" typed); go=$(res "green/type-$c" ok)
		case $c in
		ja | ko | zh_CN | zh_TW) exp_red='[ "$rs" = false ] && [ "$ro" = false ]'; exp_green='[ "$go" = true ] && [ "$gk" = "\"layer\"" ]' ;;
		*) exp_red='[ "$ro" = true ] && [ "$rk" = "\"input-panel\"" ]'; exp_green='[ "$go" = true ] && [ "$gk" = "\"input-panel\"" ]' ;;
		esac
		ok=0; eval "$exp_red" && eval "$exp_green" && ok=1
		row "3, 4" "$c: a touch on Kate's text in tablet mode, the sentence typed on the on-screen keys, read back from the saved document" \
			"keyboard $rs ($rk), typed $rt" "keyboard $gs ($gk), typed $gt" "$ok" "red/type-$c/result.json, green/type-$c/result.json"
	done
	for c in ja zh_CN; do
		n=$(res "green/type-$c" candidates_shown); ok=0; [ "${n:-0}" != null ] && [ "${n:-0}" -gt 0 ] 2>/dev/null && ok=1
		row 4 "$c: the keyboard's bar shows Fcitx 5's candidates and one is chosen by a touch" "no keyboard" "$n candidates on the bar, the first touched" "$ok" "green/type-$c/candidates.png"
	done
	for c in ja ko zh_CN zh_TW; do
		cur=$(res "green/type-$c" fcitx_before_typing.current); ok=0
		case $c in ja) w=mozc ;; ko) w=hangul ;; zh_CN) w=pinyin ;; zh_TW) w=chewing ;; esac
		[ "$cur" = "\"$w\"" ] && ok=1
		row 4 "$c: the input method chosen on the keyboard's own bar (a touch on it, a touch on the one wanted)" "no keyboard" "Fcitx 5's current input method $cur" "$ok" "green/type-$c/im-list.png, green/type-$c/steps.jsonl"
	done
fi

if want refuse; then
	case_ "$RED_IMAGE" red/refuse LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja-plain USER_SETUP=/lane/setup-fcitx-refuses.sh
	case_ "$GREEN_IMAGE" green/refuse LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja-plain USER_SETUP=/lane/setup-fcitx-refuses.sh
	# the sentence is said in the session's language: the log line carries it after "Plain typing:"
	told=$(grep -c 'Plain typing: "' "$OUT/green/refuse/session.log" 2>/dev/null); said=$(grep -m1 -o 'Plain typing: ".*"' "$OUT/green/refuse/session.log" 2>/dev/null | cut -d'"' -f2); ok=0
	[ "$(res red/refuse keyboard.shown)" = false ] && [ "$(res green/refuse ok)" = true ] && [ "${told:-0}" -gt 0 ] && ok=1
	row 4 "Fcitx 5 refusing (its keyboard addon off): the person is told on the keyboard and Latin typing still works" \
		"keyboard $(res red/refuse keyboard.shown), typed $(res red/refuse typed)" "keyboard $(res green/refuse keyboard.shown), told ($told log lines: \"$said\"), typed $(res green/refuse typed)" "$ok" "green/refuse/keys.png, green/refuse/session.log"
fi

if want absent; then
	m="$RIGD/fcitx-absent/fcitx5:/usr/bin/fcitx5:ro"
	RUN_MOUNTS=$m case_ "$RED_IMAGE" red/absent LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja-plain
	RUN_MOUNTS=$m case_ "$GREEN_IMAGE" green/absent LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja-plain
	# the sentence is said in the session's language: the log line carries it after "Plain typing:"
	told=$(grep -c 'Plain typing: "' "$OUT/green/absent/session.log" 2>/dev/null); said=$(grep -m1 -o 'Plain typing: ".*"' "$OUT/green/absent/session.log" 2>/dev/null | cut -d'"' -f2); ok=0
	[ "$(res red/absent keyboard.shown)" = false ] && [ "$(res green/absent ok)" = true ] && [ "${told:-0}" -gt 0 ] && ok=1
	row 4 "Fcitx 5 chosen but absent (its program ends at once): the person is told and Latin typing still works" \
		"keyboard $(res red/absent keyboard.shown), typed $(res red/absent typed)" "keyboard $(res green/absent keyboard.shown), told ($told log lines: \"$said\"), typed $(res green/absent typed)" "$ok" "green/absent/keys.png, green/absent/session.log"
fi

if want hardware; then
	case_ "$RED_IMAGE" red/hardware LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja STEP=hw-type.sh
	case_ "$GREEN_IMAGE" green/hardware LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja STEP=hw-type.sh
	rh=$(head -c 200 "$OUT/red/hardware/typed-hardware.txt" 2>/dev/null); gh=$(head -c 200 "$OUT/green/hardware/typed-hardware.txt" 2>/dev/null)
	ok=0; [ "$rh" = "日本語" ] && [ "$gh" = "日本語" ] && ok=1
	row 5 "ja: a hardware keyboard types through Fcitx 5 as before (Ctrl+Space, nihongo, Space, Enter)" "typed $rh" "typed $gh" "$ok" "red/hardware/hw.txt, green/hardware/hw.txt"
	gt=$(sed -n 's/^keyboard after the touch: //p' "$OUT/green/hardware/hw.txt"); gk=$(sed -n 's/^keyboard after a physical key: //p' "$OUT/green/hardware/hw.txt")
	rt=$(sed -n 's/^keyboard after the touch: //p' "$OUT/red/hardware/hw.txt")
	# after the key, Fcitx 5's own candidate popup (an input panel) may show the conversion: that is Fcitx 5's design
	ok=0; [ "$rt" = no ] && [ "$gt" = layer ] && [ "$gk" != layer ] && ok=1
	row 5 "ja: the on-screen keyboard shows on a touch and hides at the first physical key (Fcitx 5 leaves its keyboard mode)" "after the touch: $rt" "after the touch: $gt; after a physical key: $gk" "$ok" "green/hardware/after-touch.png, green/hardware/after-key.png"
	for d in red green; do im=$(cat "$OUT/$d/hardware/inputmethod.txt" 2>/dev/null); eval "${d}_im=\$im"; done
	ok=0; case "$green_im" in *org.fcitx.Fcitx5.desktop) case "$red_im" in *org.fcitx.Fcitx5.desktop) ok=1 ;; esac ;; esac
	row 5 "ja: Fcitx 5 stays KWin's input method (kwinrc [Wayland] InputMethod as the session reads it)" "$red_im" "$green_im" "$ok" "red/hardware/inputmethod.txt, green/hardware/inputmethod.txt"
fi

if want defaults; then
	case_ "$RED_IMAGE" red/tablet-off-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja TABLET=auto
	case_ "$GREEN_IMAGE" green/tablet-off-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja TABLET=auto
	case_ "$GREEN_IMAGE" green/tablet-off-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en TABLET=auto
	ok=0; [ "$(res red/tablet-off-ja keyboard.shown)" = false ] && [ "$(res green/tablet-off-ja keyboard.shown)" = false ] && [ "$(res green/tablet-off-en keyboard.shown)" = false ] && ok=1
	row 5 "outside tablet mode a touch on a text field shows no keyboard (\"Only when in Tablet Mode\"), ja and en" \
		"ja: $(res red/tablet-off-ja keyboard.shown)" "ja: $(res green/tablet-off-ja keyboard.shown); en: $(res green/tablet-off-en keyboard.shown)" "$ok" "green/tablet-off-ja/after-touch.png"
	case_ "$RED_IMAGE" red/no-touch-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja TOUCH_SCREEN=0
	case_ "$GREEN_IMAGE" green/no-touch-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja TOUCH_SCREEN=0
	gp=$(grep -c 'plasma-keyboard --fcitx$' "$OUT/green/no-touch-ja/processes.txt" 2>/dev/null); gw=$(cat "$OUT/green/no-touch-ja/showwithfcitx.txt" 2>/dev/null)
	ok=0; [ "$(res red/no-touch-ja keyboard.shown)" = false ] && [ "$(res green/no-touch-ja keyboard.shown)" = false ] && [ "${gp:-1}" = 0 ] && [ "$gw" = unset ] && ok=1
	row 5 "ja on a computer without a touch screen of its own: nothing changes (the keyboard for Fcitx 5 not started)" \
		"keyboard $(res red/no-touch-ja keyboard.shown)" "keyboard $(res green/no-touch-ja keyboard.shown); showWithFcitx $gw; processes $gp" "$ok" "green/no-touch-ja/processes.txt"
	case_ "$GREEN_IMAGE" green/switch-off-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja USER_SETUP=/lane/setup-switch-off.sh
	gw=$(cat "$OUT/green/switch-off-ja/showwithfcitx.txt" 2>/dev/null); ok=0
	[ "$(res green/switch-off-ja keyboard.shown)" = false ] && [ "$gw" = false ] && [ "$(res green/type-ja ok)" = true ] && ok=1
	row 5 "ja: the person's own choice wins (\"Show this keyboard when Fcitx 5 is the input method\" off in the person's file)" \
		"(not in the published set)" "on: typed $(res green/type-ja typed); off: keyboard $(res green/switch-off-ja keyboard.shown), showWithFcitx $gw" "$ok" "green/switch-off-ja/showwithfcitx.txt"
	for d in red green; do v=$(cat "$OUT/$d/type-en/showwithfcitx.txt" 2>/dev/null); eval "${d}_sw=\$v"; done
	ok=0; [ "$red_sw" = unset ] && [ "$green_sw" = true ] && ok=1
	row 5 "the default on a computer with a touch screen of its own: showWithFcitx from the hardware layer's folder" "$red_sw" "$green_sw" "$ok" "green/type-en/showwithfcitx.txt"
fi

if want retouch; then
	case_ "$GREEN_IMAGE" green/retouch-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en STEP=retouch.sh
	case_ "$GREEN_IMAGE" green/retouch-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja STEP=retouch.sh
	en=$(sed -n 's/^keyboard after a touch on the same field: //p' "$OUT/green/retouch-en/retouch.txt"); ja=$(sed -n 's/^keyboard after a touch on the same field: //p' "$OUT/green/retouch-ja/retouch.txt")
	# the known gap: KWin tells a keyboard that is not its input method nothing of a touch on a field that already has the focus
	ok=0; [ "$en" = panel ] && [ "$ja" = no ] && ok=1
	row "4 (gap)" "a field that has the focus from the pointer, then touched: KWin's own keyboard shows (en); Fcitx 5's keyboard does not (ja), a KWin change is needed" \
		"en: $en" "ja: $ja" "$ok" "green/retouch-en/retouch.txt, green/retouch-ja/retouch.txt"
fi

if want settings; then
	case_ "$RED_IMAGE" red/settings-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en STEP=kcm-page.sh
	case_ "$GREEN_IMAGE" green/settings-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en STEP=kcm-page.sh
	case_ "$GREEN_IMAGE" green/settings-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja STEP=kcm-page.sh
	# the pictures are read by a person: every option of the published page, plus the new switch, ticked on this computer
	ok=0; [ -s "$OUT/red/settings-en/kcm-page.png" ] && [ -s "$OUT/green/settings-en/kcm-page.png" ] && [ -s "$OUT/green/settings-ja/kcm-page.png" ] && ok=1
	row 5 "Plasma Keyboard's settings page keeps every option and has the new switch, on by default here (pictures, read)" "published page, en" "pages in en and ja" "$ok" "red/settings-en/kcm-page.png, green/settings-en/kcm-page.png, green/settings-ja/kcm-page.png"
fi

if want 3d; then
	case_ "$RED_IMAGE" red/3d-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en MODE=3d STEP=step6-3d.sh
	case_ "$GREEN_IMAGE" green/3d-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja MODE=3d STEP=step6-3d.sh
	case_ "$GREEN_IMAGE" green/3d-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en MODE=3d STEP=step6-3d.sh
	for d in red/3d-en green/3d-ja green/3d-en; do python3 -I "$RIGD/measure-3d.py" "$OUT/$d" > "$OUT/$d/measure.json" 2>> "$OUT/cases.log"; done
	m() { python3 -c 'import json,sys
d = json.load(open(sys.argv[1])); k = d.get("keyboard") or {}; b = d.get("behind") or {}; p = d.get("pair") or {}
print(k.get("disparity_px"), k.get("differing_at_disparity"), (b.get("left") or {}).get("differing"), (b.get("right") or {}).get("differing"),
      int((p.get("left_mean_rgb") or [0])[0] > 150 and (p.get("right_mean_rgb") or [0, 0, 0])[2] > 150))' "$OUT/$1/measure.json" 2>/dev/null; }
	read -r rd rdiff rbl rbr rp <<< "$(m red/3d-en)"; read -r gd gdiff gbl gbr gp <<< "$(m green/3d-ja)"; read -r ed ediff ebl ebr ep <<< "$(m green/3d-en)"
	ok=0; [ "$rd" = 0 ] && [ "$rdiff" = 0 ] && [ "$gd" = 0 ] && [ "$gdiff" = 0 ] && [ "$ed" = 0 ] && [ "$ediff" = 0 ] && ok=1
	row 6 "on a 3D output the keys are the same in both eyes, at the screen (shift and differing pixels in the keyboard's frame)" \
		"en (KWin's input panel): shift $rd, $rdiff px" "ja (Fcitx 5's keyboard): shift $gd, $gdiff px; en: shift $ed, $ediff px" "$ok" "green/3d-ja/after2.png, red/3d-en/after2.png"
	ok=0; [ "$rbl" = 0 ] && [ "$rbr" = 0 ] && [ "$gbl" = 0 ] && [ "$gbr" = 0 ] && [ "$rp" = 1 ] && [ "$gp" = 1 ] && ok=1
	row 6 "the stereo window behind is as it was (differing pixels outside the keyboard and Kate, each eye) and still a pair" \
		"en: $rbl / $rbr px, pair $rp" "ja: $gbl / $gbr px, pair $gp" "$ok" "green/3d-ja/measure.json, red/3d-en/measure.json"
fi

echo "end $(date -u +%FT%TZ) loadavg $(cut -d' ' -f1-3 /proc/loadavg)" >> "$OUT/run.txt"
column -t -s $'\t' "$OUT/rows.tsv" > "$OUT/rows.txt" 2>/dev/null || cp "$OUT/rows.tsv" "$OUT/rows.txt"
bad=$(grep -c 'NOT-AS-EXPECTED' "$OUT/rows.tsv")
echo "rows: $(($(wc -l < "$OUT/rows.tsv") - 1)), not as expected: $bad" | tee -a "$OUT/run.txt"
[ "$bad" = 0 ]
