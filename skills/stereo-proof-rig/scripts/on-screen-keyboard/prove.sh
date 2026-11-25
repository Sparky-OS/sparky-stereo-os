#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# prove.sh OUT: row 71's proof, one rerun (milestone 1's rows and the second round's). Every case is one fresh container
# and one new account's login on a 1920x1080 virtual output of Stereo KWin (on the NVIDIA card), on a computer with a
# touch screen of its own (the hardware layer reads a sysfs fixture) in tablet mode unless the case says otherwise.
# RED is the published set (r1123a) with Gwenview and the programs the rows type into (Konsole, zenity, the Stereo
# Browser, Qt's qml tool); STAGED that with the staged set this round starts from (Plasma Keyboard 6.7.4-2+stereo3d1,
# sparky-stereo-hardware 0.1.42 and KWin 6.7.4-2+stereo3d66 of row 81's stage); GREEN the red image with this round's
# packages (KWin +stereo3d67, Plasma Keyboard +stereo3d2, sparky-stereo-hardware 0.1.42), all installed by apt. One row
# per claim in OUT/rows.tsv and OUT/rows.jsonl; the exit status is 1 when a row is not as expected. The load average is
# written at the start and the end.
# Environment: DOCKER_HOST (the lane's socket), RENDER_GROUP, CONTAINER_IDS, FAKEINPUT_DIR (the built fake input client),
# RIG_SCRIPTS (the skills' stereo-proof-rig/scripts), RED_IMAGE, STAGED_IMAGE, GREEN_IMAGE; PARTS (optional: a
# space-separated subset of typing refuse absent hardware defaults retouch settings 3d filter inview 3dmoved readable
# hardware2 pages programs scales twoscreens polish).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
RIGD=$HERE/rig
OUT=${1:?an output folder that does not exist yet}
[ -e "$OUT" ] && { echo "$OUT exists: give a new folder" >&2; exit 2; }
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
: "${DOCKER_HOST:?}" "${RENDER_GROUP:?}" "${CONTAINER_IDS:?}" "${FAKEINPUT_DIR:?}" "${RIG_SCRIPTS:?}" "${RED_IMAGE:?}" "${STAGED_IMAGE:?}" "${GREEN_IMAGE:?}"
export DOCKER_HOST RENDER_GROUP CONTAINER_IDS FAKEINPUT_DIR RIG_SCRIPTS
PARTS=${PARTS:-typing refuse absent hardware defaults retouch settings 3d filter inview 3dmoved readable hardware2 pages programs scales twoscreens polish}
{ echo "start $(date -u +%FT%TZ) loadavg $(cut -d' ' -f1-3 /proc/loadavg)"; for v in RED STAGED GREEN; do i=${v}_IMAGE; echo "$v ${!i} $(docker image inspect -f '{{.Id}}' "${!i}")"; done; } > "$OUT/run.txt"
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
	# milestone 1's gap (its row "4 (gap)"), closed in KWin +stereo3d67: red is the staged set it was found on
	for d in staged green; do
		img=$STAGED_IMAGE; [ $d = green ] && img=$GREEN_IMAGE
		case_ "$img" $d/retouch-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en STEP=retouch.sh
		case_ "$img" $d/retouch-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja STEP=retouch.sh
	done
	rt() { sed -n 's/^keyboard after a touch on the same field: //p' "$OUT/$1/retouch.txt" 2>/dev/null; }
	se=$(rt staged/retouch-en); sj=$(rt staged/retouch-ja); ge=$(rt green/retouch-en); gj=$(rt green/retouch-ja)
	ok=0; [ "$se" = panel ] && [ "$sj" = no ] && [ "$ge" = panel ] && [ "$gj" = layer ] && ok=1
	row 2 "a field that has the focus from the pointer, then touched: the keyboard shows in ja as KWin's own does in en (milestone 1's gap)" \
		"staged: en $se, ja $sj" "en $ge, ja $gj" "$ok" "staged/retouch-ja/retouch.txt, green/retouch-ja/retouch.txt, green/retouch-en/retouch.txt"
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

# ---- the second round (CONTINUATION-2): red is the staged set where a row is about KWin +stereo3d67 or Plasma Keyboard
# +stereo3d2, the published set where it is about the published keyboard; the Latin session is the control throughout
jv() { python3 -c 'import json,sys
try: d = json.load(open(sys.argv[1]))
except Exception: print("no-result"); sys.exit()
for k in sys.argv[2].split("."):
    d = d.get(k) if isinstance(d, dict) else None
print(json.dumps(d, ensure_ascii=False))' "$OUT/$1" "$2"; }
img_of() { case $1 in red) echo "$RED_IMAGE" ;; staged) echo "$STAGED_IMAGE" ;; green) echo "$GREEN_IMAGE" ;; esac; }

if want inview; then
	# KWin's rule for its own panel, measured first on the published set: a window in the lower half is moved up, a
	# maximized one shortened, to end where the keys begin; a full-screen window is left as it is. Kate and a GTK 4 dialog.
	for mode in lower max; do
		for d in staged green; do
			case_ "$(img_of $d)" $d/inview-$mode-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja INVIEW=$mode
			case_ "$(img_of $d)" $d/inview-$mode-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en INVIEW=$mode
		done
		v() { echo "kbd $(jv $1/result.json keyboard.kind) clear $(jv $1/result.json inview.clear_of_keyboard) typed $(jv $1/result.json inview.typed_in_file)"; }
		ok=0
		[ "$(jv green/inview-$mode-ja/result.json inview.clear_of_keyboard)" = true ] && [ "$(jv green/inview-$mode-ja/result.json inview.typed_in_file)" = true ] \
			&& [ "$(jv green/inview-$mode-en/result.json inview.clear_of_keyboard)" = true ] && [ "$(jv staged/inview-$mode-en/result.json inview.clear_of_keyboard)" = true ] \
			&& [ "$(jv staged/inview-$mode-ja/result.json inview.clear_of_keyboard)" != true ] && ok=1
		row 3 "Kate, the field at the bottom of a window $([ $mode = lower ] && echo 'in the lower half (moved up)' || echo 'maximized (shortened)'): in ja the window ends where the keys begin, as with KWin's own keyboard in en" \
			"staged: ja $(v staged/inview-$mode-ja); en $(v staged/inview-$mode-en)" "ja $(v green/inview-$mode-ja); en $(v green/inview-$mode-en)" "$ok" \
			"green/inview-$mode-ja/inview-before.png, green/inview-$mode-ja/result.json, staged/inview-$mode-ja/inview-before.png"
	done
	case_ "$GREEN_IMAGE" green/inview-full-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja INVIEW=full
	case_ "$GREEN_IMAGE" green/inview-full-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en INVIEW=full
	gj=$(jv green/inview-full-ja/result.json inview); ge=$(jv green/inview-full-en/result.json inview)
	ok=0; [ "$(jv green/inview-full-ja/result.json keyboard.shown)" = true ] && [ "$(jv green/inview-full-ja/result.json inview.clear_of_keyboard)" = false ] \
		&& [ "$(jv green/inview-full-en/result.json inview.clear_of_keyboard)" = false ] && ok=1
	row 3 "Kate full screen: KWin leaves a full-screen window as it is for either keyboard (its own rule); the keyboard shows over it in ja as in en" \
		"en: kbd $(jv green/inview-full-en/result.json keyboard.kind), clear $(jv green/inview-full-en/result.json inview.clear_of_keyboard)" \
		"ja: kbd $(jv green/inview-full-ja/result.json keyboard.kind), clear $(jv green/inview-full-ja/result.json inview.clear_of_keyboard)" "$ok" "green/inview-full-ja/inview-before.png"
	case_ "$STAGED_IMAGE" staged/inview-zenity-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja INVIEW=lower TARGET=zenity
	case_ "$GREEN_IMAGE" green/inview-zenity-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja INVIEW=lower TARGET=zenity
	case_ "$GREEN_IMAGE" green/inview-zenity-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en INVIEW=lower TARGET=zenity
	ok=0; [ "$(jv green/inview-zenity-ja/result.json inview.clear_of_keyboard)" = true ] && [ "$(jv green/inview-zenity-ja/result.json ok)" = true ] \
		&& [ "$(jv green/inview-zenity-en/result.json inview.clear_of_keyboard)" = true ] && [ "$(jv staged/inview-zenity-ja/result.json inview.clear_of_keyboard)" != true ] && ok=1
	row 3 "a GTK 4 dialog (zenity) at the bottom of the screen: in ja it is moved clear of the keys and the entry typed into, as in en" \
		"staged ja: clear $(jv staged/inview-zenity-ja/result.json inview.clear_of_keyboard), typed $(jv staged/inview-zenity-ja/result.json typed)" \
		"ja: clear $(jv green/inview-zenity-ja/result.json inview.clear_of_keyboard), typed $(jv green/inview-zenity-ja/result.json typed); en: clear $(jv green/inview-zenity-en/result.json inview.clear_of_keyboard)" \
		"$ok" "green/inview-zenity-ja/inview-before.png, green/inview-zenity-ja/result.json"
	ok=0; ev=$(grep -h -c 'input_panel_state(' "$OUT/green/inview-lower-ja/kate-wl.log" 2>/dev/null); [ "${ev:-0}" -gt 0 ] && ok=1
	row 3 "what the client is told in ja: Kate (text-input v2) receives input_panel_state as from KWin's own panel (en)" \
		"staged ja: $(grep -h -c 'input_panel_state(' "$OUT/staged/inview-lower-ja/kate-wl.log" 2>/dev/null) events; green en: $(jv green/inview-lower-en/result.json inview.input_panel_states)" \
		"ja: $ev events, $(jv green/inview-lower-ja/result.json inview.input_panel_states)" "$ok" "green/inview-lower-ja/kate-wl.log, green/inview-lower-en/kate-wl.log"
fi

if want filter; then
	# KWin merge request 9601 (backported in +stereo3d67): only KWin's own input method binds the input-method protocols.
	# Fcitx 5 says which it got in its self-diagnosis ("Using Wayland native input method protocol: 1" when it bound
	# zwp_input_method_v1); KWin's own keyboard (its panel's pid is KWin's, which starts it on a private socket) types on
	for d in staged green; do case_ "$(img_of $d)" $d/filter-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en STEP=step-fcitx-activated.sh; done
	nat() { grep -h -o 'Using Wayland native input method protocol: [01]' "$OUT/$1/filter-en/container.log" 2>/dev/null | tail -1 | grep -o '[01]$'; }
	po() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d.get("program"), d.get("ok"))' "$OUT/$1/filter-en/panel-owner.txt" 2>/dev/null; }
	sn=$(nat staged); gn=$(nat green); sp=$(po staged); gp=$(po green)
	# a second witness: the input-method globals offered to an ordinary client (Kate, in the in-view cases)
	og() { jv $1/inview-lower-ja/result.json inview.offered_input_method_globals 2>/dev/null; }
	ok=0; [ "$sn" = 1 ] && [ "$gn" = 0 ] && [ "$gp" = "kwin_wayland True" ] && ok=1
	row "2, 7" "en: a Fcitx 5 started by D-Bus activation behind KWin's back no longer binds KWin's input-method protocol; KWin's own keyboard types (KWin MR 9601, backported)" \
		"Fcitx 5's native input method protocol: $sn; panel and typed: $sp; globals offered to Kate: $(og staged)" "protocol: $gn; panel and typed: $gp; globals offered to Kate: $(og green)" "$ok" "staged/filter-en/container.log, green/filter-en/container.log, */filter-en/panel-owner.txt, */inview-lower-ja/kate-wl.log"
fi

if want 3dmoved; then
	case_ "$STAGED_IMAGE" staged/3dmoved-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja MODE=3d STEP=step3-3d-moved.sh
	case_ "$GREEN_IMAGE" green/3dmoved-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja MODE=3d STEP=step3-3d-moved.sh
	case_ "$GREEN_IMAGE" green/3dmoved-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en MODE=3d STEP=step3-3d-moved.sh
	for d in staged/3dmoved-ja green/3dmoved-ja green/3dmoved-en; do python3 -I "$RIGD/measure-moved.py" "$OUT/$d" > "$OUT/$d/measure.json" 2>> "$OUT/cases.log"; done
	mv_() { echo "moved $(jv $1/measure.json moved), clear $(jv $1/measure.json clear_of_keyboard), pair kept $(jv $1/measure.json pair_kept), disparity $(jv $1/measure.json picture_before.disparity_px) -> $(jv $1/measure.json picture_after.disparity_px)"; }
	ok=0; [ "$(jv green/3dmoved-ja/measure.json moved)" = true ] && [ "$(jv green/3dmoved-ja/measure.json clear_of_keyboard)" = true ] \
		&& [ "$(jv green/3dmoved-en/measure.json moved)" = true ] && [ "$(jv staged/3dmoved-ja/measure.json moved)" = false ] && ok=1
	row 3 "a declared stereo window holding a field, in the lower half of a 3D output: moved clear of the keys in ja as in en" \
		"staged ja: $(mv_ staged/3dmoved-ja)" "ja: $(mv_ green/3dmoved-ja); en: $(mv_ green/3dmoved-en)" "$ok" "green/3dmoved-ja/before.png, green/3dmoved-ja/after2.png"
	ok=0; [ "$(jv green/3dmoved-ja/measure.json pair_kept)" = true ] && [ "$(jv green/3dmoved-en/measure.json pair_kept)" = true ] && ok=1
	row "3, 6" "after the move its 3D area is still a correct pair: red left view, blue right view, the same size and disparity, where the window now is" \
		"(not moved on the staged set)" "ja: $(jv green/3dmoved-ja/measure.json pair_checks); en: $(jv green/3dmoved-en/measure.json pair_checks)" "$ok" "green/3dmoved-ja/measure.json, green/3dmoved-en/measure.json"
fi

if want readable; then
	case_ "$STAGED_IMAGE" staged/refuse LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja-plain USER_SETUP=/lane/setup-fcitx-refuses.sh
	[ -d "$OUT/green/refuse" ] || case_ "$GREEN_IMAGE" green/refuse LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja-plain USER_SETUP=/lane/setup-fcitx-refuses.sh
	python3 -I "$RIGD/contrast.py" --control > "$OUT/contrast-control.json"; cc=$?
	for d in staged green; do
		fr=$(jv $d/refuse/result.json keyboard.window.fg | tr -d '[] ')
		python3 -I "$RIGD/contrast.py" "$OUT/$d/refuse/keys.png" "$fr" > "$OUT/$d/refuse/contrast.json" 2>> "$OUT/cases.log"
	done
	sr=$(jv staged/refuse/contrast.json ratio); gr=$(jv green/refuse/contrast.json ratio)
	ok=0; [ "$cc" = 0 ] && python3 -c 'import sys; sys.exit(0 if float(sys.argv[1]) < 4.5 <= float(sys.argv[2]) else 1)' "$sr" "$gr" 2>/dev/null && ok=1
	row 4 "the sentence \"Fcitx 5 does not answer\" is readable: contrast 4.5:1 or more on the bar (WCAG 2.x; the measure proved on its control)" \
		"staged: $sr:1, glyph $(jv staged/refuse/contrast.json glyph) on $(jv staged/refuse/contrast.json background)" "$gr:1, glyph $(jv green/refuse/contrast.json glyph) on $(jv green/refuse/contrast.json background)" "$ok" \
		"staged/refuse/keys.png, green/refuse/keys.png, contrast-control.json"
fi

if want hardware2; then
	for c in ko zh_CN; do
		loc=ko_KR; exp=한국어; [ $c = zh_CN ] && { loc=zh_CN; exp=中文; }
		case_ "$RED_IMAGE" red/hardware-$c LOGIN_LANG=$loc.UTF-8 LANG_CASE=$c HW_LANG=$c STEP=hw-type.sh
		case_ "$GREEN_IMAGE" green/hardware-$c LOGIN_LANG=$loc.UTF-8 LANG_CASE=$c HW_LANG=$c STEP=hw-type.sh
		rh=$(head -c 200 "$OUT/red/hardware-$c/typed-hardware.txt" 2>/dev/null); gh=$(head -c 200 "$OUT/green/hardware-$c/typed-hardware.txt" 2>/dev/null)
		ok=0; [ "$rh" = "$exp" ] && [ "$gh" = "$exp" ] && ok=1
		row 5 "$c: a hardware keyboard types through Fcitx 5 as before (the keys of $exp, then $([ $c = ko ] && echo Enter || echo Space))" "typed $rh" "typed $gh" "$ok" "red/hardware-$c/hw.txt, green/hardware-$c/hw.txt"
	done
fi

if want pages; then
	case_ "$GREEN_IMAGE" green/pages-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja-pages
	case_ "$GREEN_IMAGE" green/swipe-zh_CN LOGIN_LANG=zh_CN.UTF-8 LANG_CASE=zh_CN-swipe
	p1=$(jv green/pages-ja/result.json page1); p2=$(jv green/pages-ja/result.json page2)
	ok=0; [ "$(jv green/pages-ja/result.json ok)" = true ] && [ "$p1" != "$p2" ] && [ "$p2" != null ] && ok=1
	row 5 "ja (Mozc hands a page at a time): the bar's \"›\" turns to Fcitx 5's next page by touch and a candidate there is committed" "no keyboard (published)" \
		"page 1 $p1; page 2 $p2; typed $(jv green/pages-ja/result.json typed)" "$ok" "green/pages-ja/page2.png, green/pages-ja/result.json"
	ok=0; [ "$(jv green/swipe-zh_CN/result.json ok)" = true ] && ok=1
	row 5 "zh_CN (Pinyin hands all candidates): the bar's row swiped by touch, a later candidate committed" "no keyboard (published)" \
		"$(jv green/swipe-zh_CN/result.json visible_before) visible of $(jv green/swipe-zh_CN/result.json all_candidates | python3 -c 'import json,sys; print(len(json.load(sys.stdin) or []))' 2>/dev/null); swiped to index $(jv green/swipe-zh_CN/result.json swiped_index), typed $(jv green/swipe-zh_CN/result.json typed)" \
		"$ok" "green/swipe-zh_CN/swiped.png, green/swipe-zh_CN/result.json"
fi

if want programs; then
	for t in konsole zenity systemsettings browser; do
		case_ "$GREEN_IMAGE" green/prog-$t-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja TARGET=$t
		case_ "$GREEN_IMAGE" green/prog-$t-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en TARGET=$t
		pv() { echo "kbd $(jv $1/result.json keyboard.kind), typed $(jv $1/result.json typed), field change $(jv $1/result.json field_change_px), ok $(jv $1/result.json ok)"; }
		ok=0; [ "$(jv green/prog-$t-ja/result.json ok)" = true ] && [ "$(jv green/prog-$t-en/result.json ok)" = true ] && ok=1
		case $t in konsole) n="Konsole (a line read by bash)" ;; zenity) n="a GTK 4 program's field (zenity's entry)" ;; systemsettings) n="System Settings' search field" ;; browser) n="the Stereo Browser's address field" ;; esac
		row 5 "ja: $n typed into by touch as in en" "en: $(pv green/prog-$t-en)" "ja: $(pv green/prog-$t-ja)" "$ok" "green/prog-$t-ja/finished.png, green/prog-$t-ja/result.json"
	done
fi

if want scales; then
	for sc in 1.25 1.5; do
		case_ "$GREEN_IMAGE" green/scale$sc-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja SCALE=$sc
		case_ "$GREEN_IMAGE" green/scale$sc-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en SCALE=$sc
		ok=0; [ "$(jv green/scale$sc-ja/result.json ok)" = true ] && [ "$(jv green/scale$sc-en/result.json ok)" = true ] && ok=1
		row 5 "at $(python3 -c "print(int(float('$sc')*100))") %: the keyboard shows on a touch and the sentence is typed, ja as en" \
			"en: kbd $(jv green/scale$sc-en/result.json keyboard.kind), typed $(jv green/scale$sc-en/result.json typed)" "ja: kbd $(jv green/scale$sc-ja/result.json keyboard.kind), typed $(jv green/scale$sc-ja/result.json typed)" "$ok" \
			"green/scale$sc-ja/keys.png, green/scale$sc-ja/outputs.txt"
	done
fi

if want twoscreens; then
	case_ "$GREEN_IMAGE" green/twoscreens-ja LOGIN_LANG=ja_JP.UTF-8 LANG_CASE=ja OUTPUTS=2 STEP=twoscreens.sh
	case_ "$GREEN_IMAGE" green/twoscreens-en LOGIN_LANG=en_US.UTF-8 LANG_CASE=en OUTPUTS=2 STEP=twoscreens.sh
	tj=$(tr '\n' ' ' < "$OUT/green/twoscreens-ja/twoscreens.txt" 2>/dev/null); te=$(tr '\n' ' ' < "$OUT/green/twoscreens-en/twoscreens.txt" 2>/dev/null)
	okf() { grep -q '^second: keyboard [a-z]* on Virtual-1 ' "$OUT/$1/twoscreens.txt" 2>/dev/null && grep -q '^first: keyboard [a-z]* on Virtual-0 ' "$OUT/$1/twoscreens.txt" 2>/dev/null; }
	ok=0; okf green/twoscreens-ja && okf green/twoscreens-en && ok=1
	row 5 "two screens: a touch on the field of a window on the second screen brings the keyboard there, back on the first with a touch there, ja as en" "en: $te" "ja: $tj" "$ok" \
		"green/twoscreens-ja/second-screen.png, green/twoscreens-ja/first-screen.png, green/twoscreens-ja/twoscreens.txt"
fi

if want polish; then
	case_ "$RED_IMAGE" red/pl-long LOGIN_LANG=pl_PL.UTF-8 LANG_CASE=pl-long
	case_ "$GREEN_IMAGE" green/pl-long LOGIN_LANG=pl_PL.UTF-8 LANG_CASE=pl-long
	ok=0; [ "$(jv red/pl-long/result.json ok)" = true ] && [ "$(jv green/pl-long/result.json ok)" = true ] && ok=1
	row 6 "pl: \"Dzień dobry\" typed with its diacritic by the keyboard's own long press (n held, the finger slides to ń), published and this round" \
		"typed $(jv red/pl-long/result.json typed)" "typed $(jv green/pl-long/result.json typed)" "$ok" "red/pl-long/typed.png, green/pl-long/typed.png"
fi

echo "end $(date -u +%FT%TZ) loadavg $(cut -d' ' -f1-3 /proc/loadavg)" >> "$OUT/run.txt"
column -t -s $'\t' "$OUT/rows.tsv" > "$OUT/rows.txt" 2>/dev/null || cp "$OUT/rows.tsv" "$OUT/rows.txt"
bad=$(grep -c 'NOT-AS-EXPECTED' "$OUT/rows.tsv")
echo "rows: $(($(wc -l < "$OUT/rows.tsv") - 1)), not as expected: $bad" | tee -a "$OUT/run.txt"
[ "$bad" = 0 ]
