#!/bin/bash
# The rows of rows 678 and 682, as uid 1000 inside the proof container (inner.sh): a private session bus, PipeWire (its own V4L2
# source opening the rig's user-space cameras through vcam-shim.so) and WirePlumber, the installed sparky-stereo-camera, its command
# and its page's engine (kcm-probe), the problems engine. Each row prints PASS or FAIL with the value it read; GAP is a measurement
# of a program this package does not change (Qt Multimedia, PipeWire). Expectations are those of 0.1.3: on 0.1.2 a FAIL is the red.
# Usage: rows.sh red|green [ROW...] | before-upgrade | after-upgrade | stop
set -u
: "${RUN:?}"
PHASE=${1:?}
shift
ENVFILE=$RUN/env.sh
ROWS=$RUN/rows.txt
STORE=$RUN/home/.config/sparky-stereo-camera/cameras.ini

row() { # row NAME RESULT(0 = as expected) DETAIL
	local s=FAIL
	[ "$2" = 0 ] && s=PASS
	echo "$s $1: $3" | tee -a "$ROWS"
}
gap() { echo "GAP $1: $2" | tee -a "$ROWS"; }
waitfor() { # waitfor SECONDS COMMAND...: polls the state every 0.2 s; status 1 when it never came
	local end=$(($(date +%s) + $1))
	shift
	until "$@" >/dev/null 2>&1; do
		[ "$(date +%s)" -ge "$end" ] && return 1
		sleep 0.2
	done
}
jq_() { python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"; }

start_session() {
	cat >"$ENVFILE" <<EOF
export XDG_RUNTIME_DIR=$RUN/xdg-run XDG_CONFIG_HOME=$RUN/home/.config XDG_STATE_HOME=$RUN/home/.local/state XDG_DATA_HOME=$RUN/home/.local/share
export VCAM_ROOT=$RUN/vcam SHIM=$RUN/vcam/vcam-shim.so QT_QPA_PLATFORM=offscreen QT_MEDIA_BACKEND=ffmpeg LANG=C.UTF-8 LC_ALL=C.UTF-8
export PATH=$RUN/bin:\$PATH KM_TABLE=/hw/share/known-machines.json KM_SYSFS=$RUN/sys-other SPARKY_STEREO_CAMERA_SYSFS=$RUN/sys-other
EOF
	. "$ENVFILE"
	mkdir -p "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME/wireplumber/wireplumber.conf.d" "$XDG_STATE_HOME" "$RUN/bin"
	chmod 700 "$XDG_RUNTIME_DIR"
	# no monitor of WirePlumber's looks for devices: the only cameras are the rig's nodes (nothing of the host is opened)
	printf 'wireplumber.profiles = {\n  main = {\n    monitor.alsa = disabled\n    monitor.alsa-midi = disabled\n    monitor.bluez = disabled\n    monitor.v4l2 = disabled\n    monitor.libcamera = disabled\n  }\n}\n' >"$XDG_CONFIG_HOME/wireplumber/wireplumber.conf.d/90-rig.conf"
	cp /rig/machines/sparky-stereo-known-machines "$RUN/bin/"
	sh /rig/machines/make-sysfs.sh "$RUN/sys-vaio" vaio
	sh /rig/machines/make-sysfs.sh "$RUN/sys-other" other
	dbus-daemon --session --fork --print-address --print-pid --address="unix:path=$XDG_RUNTIME_DIR/bus" >"$RUN/dbus-address"
	echo "export DBUS_SESSION_BUS_ADDRESS=$(head -1 "$RUN/dbus-address")" >>"$ENVFILE"
	. "$ENVFILE"
	sed -n 2p "$RUN/dbus-address" >"$RUN/pids"
	LD_PRELOAD=$SHIM pipewire >"$RUN/pipewire.log" 2>&1 &
	echo $! >>"$RUN/pids"
	waitfor 20 pw-cli info 0 || { echo "pipewire did not start"; cat "$RUN/pipewire.log"; exit 1; }
	wireplumber >"$RUN/wireplumber.log" 2>&1 &
	echo $! >>"$RUN/pids"
	waitfor 20 sh -c 'pw-cli ls Metadata | grep -q "metadata.name = \"default\""' || { echo "wireplumber did not start"; exit 1; }
	plug 30 cam-imac "FaceTime HD Camera"
	plug 31 cam-a10 "EasyCamera"
	plug 32 cam-flags "Virtual camera flags"
	plug 33 cam-modes "Virtual camera modes"
	plug 34 cam-vaio "Integrated Camera"
	plug 35 cam-held "Virtual camera held"
}

node_id() { pw-cli ls Node | python3 -c "
import re,sys
cur=None
for line in sys.stdin:
    m=re.match(r'\s*id (\d+), type PipeWire:Interface:Node',line)
    if m: cur=m.group(1)
    if 'node.name = \"$1\"' in line: print(cur)"; }
plug() { # plug N NAME DESCRIPTION: the camera appears as PipeWire's own V4L2 source node, at its defaults
	pw-cli create-node spa-node-factory "{ factory.name=api.v4l2.source node.name=$2 node.description=\"$3\" api.v4l2.path=\"/dev/video$1\" object.path=\"v4l2:/dev/video$1\" media.class=\"Video/Source\" media.role=Camera object.linger=true }" >>"$RUN/nodes.log" 2>&1
	waitfor 10 sh -c "[ -n \"\$(pw-cli ls Node | grep 'node.name = \"$2\"')\" ]" || echo "node $2 did not appear" | tee -a "$RUN/nodes.log"
}
unplug() { # unplug N NAME: the node goes and the camera forgets its values (a camera starts at its defaults)
	local id
	id=$(node_id "$2")
	[ -n "$id" ] && pw-cli destroy "$id" >>"$RUN/nodes.log" 2>&1
	waitfor 10 sh -c "[ -z \"\$(pw-cli ls Node | grep 'node.name = \"$2\"')\" ]"
	rm -f "$VCAM_ROOT/video$1.state"
}
replug() { unplug "$1" "$2"; plug "$1" "$2" "$3"; }
CLI() { LD_PRELOAD=$SHIM sparky-stereo-camera "$@"; }
KCM() { LD_PRELOAD=$SHIM "$RUN/probes/kcm-probe" "$PLUGIN" "$@" 2>>"$RUN/kcm-probe.err"; }
cid() { CLI controls "$1" | jq_ "[c['id'] for c in d if c['name']=='$2'][0]"; }
cval() { CLI control "$1" "$2" | jq_ "d['value']"; }
modeof() { CLI mode "$1" | jq_ "'%s %d %d %g' % (d['format'], d['width'], d['height'], d['fps'])"; }
store() { python3 /rig/store.py "$STORE" "$1"; }
problems() { # the problems engine's keys of this package that contain TEXT
	sparky-stereo-problems list --json 2>/dev/null | python3 -c "
import json,sys
try: d=json.load(sys.stdin)
except Exception: d=[]
d=d if isinstance(d,list) else d.get('problems',[])
print(' '.join(sorted(p.get('key','') for p in d if p.get('package')=='sparky-stereo-camera' and '$1' in p.get('key',''))))"
}
clear_all() {
	for k in $(problems :); do sparky-stereo-problems clear sparky-stereo-camera "$k" >/dev/null 2>&1; done
	rm -f "$STORE"
}
mark() { echo "MARK $1" >>"$VCAM_ROOT/video$2.log"; }
after_mark() { sed -n "/^MARK $1\$/,\$p" "$VCAM_ROOT/video$2.log"; }

row_imac() {
	clear_all
	replug 30 cam-imac "FaceTime HD Camera"
	local idT idI idB s rc out p
	idT=$(cid cam-imac white_balance_temperature)
	idI=$(cid cam-imac iris_relative)
	idB=$(cid cam-imac brightness)
	CLI control cam-imac brightness 10
	s=$(store FaceTime)
	echo "$s" | jq_ "'$idB' in d['controls']" | grep -q True
	row imac-save-keeps-a-setting $? "store: $s"
	echo "$s" | jq_ "'$idT' in d['controls']" | grep -q False
	row imac-save-not-inactive-white-balance-temperature $? "temperature $idT in the store: $(echo "$s" | jq_ "d['controls'].get('$idT')")"
	echo "$s" | jq_ "'$idI' in d['controls']" | grep -q False
	row imac-save-not-iris-relative $? "iris relative $idI in the store: $(echo "$s" | jq_ "d['controls'].get('$idI')")"
	replug 30 cam-imac "FaceTime HD Camera"
	out=$(CLI apply cam-imac 2>&1)
	rc=$?
	row imac-apply-succeeds $rc "exit $rc: $(echo "$out" | tr '\n' '|')"
	p=$(problems FaceTime)
	[ -z "$p" ]
	row imac-no-problem-kept $? "problems: [${p}]"
	[ "$(cval cam-imac brightness)" = 10 ]
	row imac-setting-applied-at-plug-in $? "brightness $(cval cam-imac brightness)"
}

row_before_upgrade() {
	# 0.1.2 installed: the iMac's state as row 678 found it
	clear_all
	replug 30 cam-imac "FaceTime HD Camera"
	local idT idI s out p
	idT=$(cid cam-imac white_balance_temperature)
	idI=$(cid cam-imac iris_relative)
	CLI control cam-imac brightness 10
	s=$(store FaceTime)
	echo "$s" >"$RUN/store-0.1.2.json"
	echo "$s" | jq_ "'$idT' in d['controls'] and '$idI' in d['controls']" | grep -q True
	row red-reproduced-0.1.2-saves-both $? "store: $s"
	replug 30 cam-imac "FaceTime HD Camera"
	out=$(CLI apply cam-imac 2>&1)
	p=$(problems FaceTime)
	[ "$(echo $p | wc -w)" = 2 ]
	row red-reproduced-0.1.2-two-problems $? "apply: $(echo "$out" | tr '\n' '|'); problems: [$p]"
	sparky-stereo-problems list | head -8 >"$RUN/problems-0.1.2.txt"
	echo "$idT $idI" >"$RUN/imac-ids"
	# the A10 as the main session ran it (2026-11-26): automatic white balance off, the temperature 3000, automatic on again; then a
	# reset (sharpness to the clamped default 100). The store holds the person's 3000, and the next plug-in refuses it with a problem.
	replug 31 cam-a10 "EasyCamera"
	CLI control cam-a10 white_balance_automatic 0
	CLI control cam-a10 white_balance_temperature 3000
	CLI control cam-a10 white_balance_automatic 1
	CLI reset cam-a10
	s=$(store EasyCamera)
	echo "$s" >"$RUN/store-a10-0.1.2.json"
	echo "$s" | jq_ "d['controls'].get('$(cid cam-a10 white_balance_temperature)')=='3000' and 'sharpness' in d['names'].values()" | grep -q True
	row red-reproduced-0.1.2-a10-store-holds-3000-and-sharpness $? "store: $s"
	replug 31 cam-a10 "EasyCamera"
	out=$(CLI apply cam-a10 2>&1)
	p=$(problems EasyCamera)
	[ "$(echo $p | wc -w)" = 1 ]
	row red-reproduced-0.1.2-a10-temperature-refused-with-a-problem $? "apply: $(echo "$out" | grep -v journal | tr '\n' '|'); problems: [$p]"
}

row_after_upgrade() {
	local idT idI s out rc p idT10
	read -r idT idI <"$RUN/imac-ids"
	# the unit applies the saved choice when the camera appears (at login it is already there): the same call
	replug 30 cam-imac "FaceTime HD Camera"
	out=$(CLI apply cam-imac 2>&1)
	rc=$?
	echo "$out" >"$RUN/apply-after-upgrade.txt"
	row upgrade-apply-succeeds $rc "exit $rc: $(echo "$out" | grep -v journal | tr '\n' '|')"
	s=$(store FaceTime)
	echo "$s" >"$RUN/store-after-upgrade.json"
	echo "$s" | jq_ "'$idT' in d['controls'] and '$idI' not in d['controls'] and d.get('version')=='2' and '$(cid cam-imac brightness)' in d['controls']" | grep -q True
	row upgrade-imac-temperature-kept-iris-removed $? "store: $s"
	echo "$out" | grep -q "removed the saved value 88 of iris_relative: not a setting: a motion control" && echo "$out" | grep -q "white_balance_temperature is inactive now; its saved value 5547 waits for it"
	row upgrade-journal-says-only-what-is-known $? "$(echo "$out" | grep -E 'removed|inactive now' | tr '\n' '|')"
	echo "$out" | grep -q "saved while the control was inactive"
	[ $? != 0 ]
	row upgrade-journal-no-unmeasured-claim $? "no line says a value was saved while inactive"
	p=$(problems FaceTime)
	[ -z "$p" ]
	row upgrade-problems-cleared $? "problems: [$p]"
	out=$(CLI apply cam-imac 2>&1)
	echo "$out" | grep -q removed
	[ $? != 0 ]
	row upgrade-cleaned-only-once $? "second apply: $(echo "$out" | grep -v journal | tr '\n' '|')"
	# the A10's case: the person's 3000 kept and waiting, the sharpness at the default removed, no problem
	idT10=$(cid cam-a10 white_balance_temperature)
	replug 31 cam-a10 "EasyCamera"
	out=$(CLI apply cam-a10 2>&1)
	rc=$?
	s=$(store EasyCamera)
	echo "$s" >"$RUN/store-a10-after-upgrade.json"
	echo "$s" | jq_ "d['controls'].get('$idT10')=='3000' and 'sharpness' not in d['names'].values() and d.get('version')=='2'" | grep -q True && [ "$rc" = 0 ] && [ -z "$(problems EasyCamera)" ]
	row upgrade-a10-manual-temperature-kept-waiting $? "exit $rc; store: $s; problems [$(problems EasyCamera)]; $(echo "$out" | grep -E 'removed|inactive now' | tr '\n' '|')"
	out=$(CLI control cam-a10 white_balance_automatic 0 2>&1)
	[ "$(cval cam-a10 white_balance_temperature)" = 3000 ] && store EasyCamera | jq_ "d['controls'].get('$idT10')" | grep -qx 3000
	row upgrade-a10-temperature-applies-when-active-again $? "after automatic white balance off: temperature $(cval cam-a10 white_balance_temperature); $(echo "$out" | tr '\n' '|')"
}

row_refusal() {
	clear_all
	replug 30 cam-imac "FaceTime HD Camera"
	local idB rc1 p1 p3 rc
	idB=$(cid cam-imac brightness)
	CLI control cam-imac brightness 20
	sed -i 's/^ctrl brightness int -64 64 1 0 clamp$/ctrl brightness int -64 64 1 0 clamp refuse/' "$VCAM_ROOT/video30.cfg"
	replug 30 cam-imac "FaceTime HD Camera"
	CLI apply cam-imac >/dev/null 2>&1
	rc1=$?
	p1=$(problems "control-$idB")
	CLI apply cam-imac >/dev/null 2>&1
	CLI apply cam-imac >/dev/null 2>&1
	p3=$(problems "control-$idB")
	[ "$rc1" != 0 ] && [ "$(echo $p1 | wc -w)" = 1 ] && [ "$p1" = "$p3" ]
	row refusal-told-and-kept-once $? "exit $rc1; after one apply [$p1], after three [$p3]"
	sed -i 's/ clamp refuse$/ clamp/' "$VCAM_ROOT/video30.cfg"
	replug 30 cam-imac "FaceTime HD Camera"
	CLI apply cam-imac >/dev/null 2>&1
	rc=$?
	[ "$rc" = 0 ] && [ -z "$(problems "control-$idB")" ]
	row refusal-cleared-when-it-works $? "exit $rc, problems [$(problems "control-$idB")]"
}

row_flags() {
	clear_all
	replug 32 cam-flags "Virtual camera flags"
	local json got s
	json=$(CLI controls cam-flags)
	echo "$json" >"$RUN/flags-controls.json"
	for spec in brightness:setting contrast:read-only saturation:write-only hue:volatile gamma:action gain:setting sharpness:setting \
		backlight_compensation:setting rotate:setting whichminmax_ctrl:setting lut_ctrl:payload roi_ctrl:payload big_ctrl:not-editable \
		white_balance_automatic:setting white_balance_temperature:setting focus_absolute:setting focus_automatic_continuous:setting \
		norange_ctrl:no-range pan_relative:motion tilt_relative:motion focus_relative:motion zoom_relative:motion iris_relative:motion \
		zoom_continuous:motion pan_speed:motion tilt_speed:motion pan_reset:button; do
		got=$(echo "$json" | jq_ "[c.get('keep','(no keep field)') for c in d if c['name']=='${spec%%:*}'][0]")
		[ "$got" = "${spec#*:}" ]
		row "flags-rule-${spec%%:*}" $? "keep=$got (expected ${spec#*:})"
	done
	echo "$json" | jq_ "[c['name'] for c in d if c['name']=='disabled_ctrl']" | grep -q '\[\]'
	row flags-disabled-not-listed $? "V4L2_CTRL_FLAG_DISABLED: ignored by the application"
	CLI control cam-flags brightness 101
	s=$(store "Virtual camera flags")
	got=$(echo "$s" | jq_ "' '.join(sorted(d['names'].values()))")
	[ "$got" = "backlight_compensation brightness rotate sharpness whichminmax_ctrl" ]
	row flags-store-only-settings $? "saved: $got"
}

row_cluster() {
	# a governed control whose id is lower than its governing control's: the apply must set the governing one first
	clear_all
	replug 32 cam-flags "Virtual camera flags"
	local out rc v
	CLI control cam-flags focus_automatic_continuous 0
	CLI control cam-flags focus_absolute 100
	CLI mode cam-flags YUYV 640x480 30
	replug 32 cam-flags "Virtual camera flags"
	mark cluster 32
	out=$(CLI apply cam-flags 2>&1)
	rc=$?
	v=$(cval cam-flags focus_absolute)
	[ "$rc" = 0 ] && [ "$v" = 100 ] && [ -z "$(problems "Virtual_camera_flags")" ]
	row cluster-governing-control-first $? "exit $rc, focus_absolute $v, problems [$(problems Virtual_camera_flags)]; $(echo "$out" | tr '\n' '|')"
	after_mark cluster 32 | grep -v MARK | sed 's/^[^ ]* [0-9]* //' | tr '\n' '|' >"$RUN/cluster-order.txt"
	after_mark cluster 32 | awk '/S_CTRL rotate/{r=NR} /S_FMT/{if(!f)f=NR} END{exit !(r && f && r<f)}'
	row cluster-layout-control-before-the-mode $? "order: $(cat "$RUN/cluster-order.txt")"
}

row_a10() {
	clear_all
	replug 31 cam-a10 "EasyCamera"
	local json s
	json=$(CLI controls cam-a10)
	echo "$json" | jq_ "[(c['inactive'], c.get('keep')) for c in d if c['name']=='white_balance_temperature'][0]" | grep -q "(True, 'setting')"
	row a10-temperature-inactive-shown-as-reported $? "$(echo "$json" | jq_ "[(c['inactive'], c.get('keep'), c['value']) for c in d if c['name']=='white_balance_temperature'][0]")"
	echo "$json" | jq_ "[c.get('effectiveDefault') for c in d if c['name']=='sharpness'][0]" | grep -qx 100
	row a10-sharpness-default-in-range $? "sharpness default 120, maximum 100, effectiveDefault $(echo "$json" | jq_ "[c.get('effectiveDefault') for c in d if c['name']=='sharpness'][0]")"
	CLI reset cam-a10
	s=$(store EasyCamera)
	echo "$s" | jq_ "'sharpness' in d['names'].values()" | grep -q False
	row a10-reset-does-not-save-sharpness $? "after reset sharpness=$(cval cam-a10 sharpness); store: $s"
	replug 31 cam-a10 "EasyCamera"
	CLI apply cam-a10 >/dev/null 2>&1
	[ -z "$(problems EasyCamera)" ]
	row a10-apply-no-problem $? "problems [$(problems EasyCamera)]"
}

row_modes() {
	clear_all
	replug 33 cam-modes "Virtual camera modes"
	local out m s idB
	out=$(CLI best cam-modes 2>&1)
	echo "$out" | jq_ "'%s %d %d %g' % (d['mode']['format'], d['mode']['width'], d['mode']['height'], d['mode']['fps'])" 2>/dev/null | grep -qx "MJPG 2592 1944 15"
	row modes-best-is-largest-then-fastest $? "$(echo "$out" | tr -d '\n ' | cut -c1-200)"
	CLI apply cam-modes >/dev/null 2>&1
	m=$(modeof cam-modes)
	[ "$m" = "MJPG 2592 1944 15" ]
	row modes-unset-camera-starts-at-best $? "device after apply: $m (driver's first: YUYV 640 480 30)"
	replug 33 cam-modes "Virtual camera modes"
	m=$(KCM load current=cam-modes mode | grep '^mode')
	[ "$m" = "mode MJPG 2592 1944 15" ]
	row modes-page-first-values-best $? "page: $m"
	CLI mode cam-modes YUYV 1280x720 10
	replug 33 cam-modes "Virtual camera modes"
	CLI apply cam-modes >/dev/null 2>&1
	m=$(modeof cam-modes)
	[ "$m" = "YUYV 1280 720 10" ]
	row modes-saved-choice-kept $? "device after apply: $m"
	m=$(KCM load current=cam-modes mode | grep '^mode')
	[ "$m" = "mode YUYV 1280 720 10" ]
	row modes-page-shows-saved-choice $? "page: $m"
	clear_all
	replug 33 cam-modes "Virtual camera modes"
	CLI control cam-modes brightness 100
	replug 33 cam-modes "Virtual camera modes"
	CLI apply cam-modes >/dev/null 2>&1
	m=$(modeof cam-modes)
	[ "$m" = "MJPG 2592 1944 15" ] && [ "$(cval cam-modes brightness)" = 100 ]
	row modes-remembered-camera-without-mode-starts-at-best $? "mode $m, brightness $(cval cam-modes brightness), store $(store "Virtual camera modes")"
	clear_all
	replug 33 cam-modes "Virtual camera modes"
	idB=$(cid cam-modes brightness)
	KCM load current=cam-modes "set=$idB:90" save >/dev/null
	s=$(store "Virtual camera modes")
	echo "$s" | jq_ "'format' not in d and d['controls'].get('$idB')=='90'" | grep -q True
	row modes-page-apply-does-not-freeze-the-best-mode $? "store: $s"
	CLI mode cam-modes YUYV 640x480 30
	out=$(KCM load current=cam-modes defaults mode save)
	s=$(store "Virtual camera modes")
	echo "$out" | grep -qx "mode MJPG 2592 1944 15" && echo "$s" | jq_ "'format' not in d" | grep -q True
	row modes-page-defaults-best-mode-and-forget-saved $? "$(echo "$out" | grep '^mode'); store: $s"
}

row_page() {
	clear_all
	replug 31 cam-a10 "EasyCamera"
	local idW out
	idW=$(cid cam-a10 white_balance_automatic)
	out=$(KCM load current=cam-a10 controls "set=$idW:0" controls)
	echo "$out" | grep '^controls' | python3 -c "
import json,sys
lists=[json.loads(l.split(' ',1)[1]) for l in sys.stdin]
t=[[c['inactive'] for c in l if c['name']=='white_balance_temperature'][0] for l in lists]
print(t); sys.exit(0 if t==[True, False] else 1)" >"$RUN/page-follow.txt"
	row page-follows-a-governing-control $? "temperature inactive before and after automatic white balance off: $(cat "$RUN/page-follow.txt")"
	replug 32 cam-flags "Virtual camera flags"
	out=$(KCM load current=cam-flags controls | grep '^controls')
	echo "$out" | cut -d' ' -f2- | python3 -c "
import json,sys
d={c['name']:c['note'] for c in json.load(sys.stdin)}
want={'pan_relative':'moves the camera','hue':'changes this value by itself','norange_ctrl':'no range','gain':'Another program is using this control','white_balance_temperature':'not using this control now'}
bad=[k for k,v in want.items() if v not in d.get(k,'')]
print(bad or 'all notes'); sys.exit(1 if bad else 0)" >"$RUN/page-notes.txt"
	row page-says-why-a-control-is-not-kept $? "$(cat "$RUN/page-notes.txt")"
	LANGUAGE=de LANG=de_DE.UTF-8 LC_ALL=de_DE.UTF-8 KCM load current=cam-flags controls | grep '^controls' | cut -d' ' -f2- | python3 -c "
import json,sys
d={c['name']:c['note'] for c in json.load(sys.stdin)}
print(d.get('hue','')); sys.exit(0 if d.get('hue') and 'changes' not in d['hue'] else 1)" >"$RUN/page-notes-de.txt"
	row page-notes-in-german $? "hue: $(cat "$RUN/page-notes-de.txt")"
	replug 35 cam-held "Virtual camera held"
	out=$(KCM load current=cam-held setmode=YUYV:320:240:30 error | grep '^error')
	echo "$out" | grep -q "Another program is using"
	row page-shows-a-refused-mode $? "$out"
}

row_vaio() {
	clear_all
	replug 34 cam-vaio "Integrated Camera"
	local m
	m=$(KM_TABLE=/rig/machines/known-machines-vaio-caveat.json KM_SYSFS=$RUN/sys-vaio SPARKY_STEREO_CAMERA_SYSFS=$RUN/sys-vaio CLI best cam-vaio)
	echo "$m" | jq_ "'%s %d %d %g %s %s' % (d['mode']['format'], d['mode']['width'], d['mode']['height'], d['mode']['fps'], d['usb'], ','.join(d['allowedFormats']))" 2>/dev/null | grep -qx "MJPG 1280 720 30 0bda:5722 MJPG"
	row vaio-caveat-wins $? "$(echo "$m" | tr -d '\n ' | cut -c1-200)"
	m=$(KM_TABLE=/hw/share/known-machines.json KM_SYSFS=$RUN/sys-vaio SPARKY_STEREO_CAMERA_SYSFS=$RUN/sys-vaio CLI best cam-vaio)
	echo "$m" | jq_ "'%s %d %d' % (d['mode']['format'], d['mode']['width'], d['mode']['height'])" 2>/dev/null | grep -qx "YUYV 1600 1200"
	row vaio-published-table-has-no-caveat $? "$(echo "$m" | tr -d '\n ' | cut -c1-200)"
	m=$(KM_TABLE=/rig/machines/known-machines-vaio-caveat.json KM_SYSFS=$RUN/sys-other SPARKY_STEREO_CAMERA_SYSFS=$RUN/sys-vaio CLI best cam-vaio)
	echo "$m" | jq_ "'%s %d %d' % (d['mode']['format'], d['mode']['width'], d['mode']['height'])" 2>/dev/null | grep -qx "YUYV 1600 1200"
	row vaio-caveat-only-on-that-machine $? "$(echo "$m" | tr -d '\n ' | cut -c1-200)"
	KM_TABLE=/rig/machines/known-machines-vaio-caveat.json KM_SYSFS=$RUN/sys-vaio SPARKY_STEREO_CAMERA_SYSFS=$RUN/sys-vaio CLI apply cam-vaio >/dev/null 2>&1
	m=$(modeof cam-vaio)
	[ "$m" = "MJPG 1280 720 30" ]
	row vaio-apply-takes-the-caveat-mode $? "device: $m"
}

row_watch() {
	clear_all
	replug 33 cam-modes "Virtual camera modes"
	CLI mode cam-modes YUYV 640x480 30 >/dev/null
	rm -f "$STORE"
	LD_PRELOAD=$SHIM sparky-stereo-camera watch >"$RUN/watch.log" 2>&1 &
	local pid=$! m
	waitfor 20 grep -q "camera cam-modes:.*saved settings applied" "$RUN/watch.log"
	unplug 33 cam-modes
	local before
	before=$(grep -c "camera cam-modes:.*saved settings applied" "$RUN/watch.log")
	plug 33 cam-modes "Virtual camera modes"
	waitfor 20 sh -c "[ \$(grep -c 'camera cam-modes:.*saved settings applied' '$RUN/watch.log') -gt $before ]"
	m=$(modeof cam-modes)
	kill "$pid" 2>/dev/null
	wait "$pid" 2>/dev/null
	[ "$m" = "MJPG 2592 1944 15" ]
	row watch-plugged-camera-starts-at-best $? "after plug-in: $m; $(grep cam-modes "$RUN/watch.log" | tail -2 | tr '\n' '|')"
}

set_by() { # set_by MARK PROCESS: the last mode PROCESS set on video33 after MARK ("MJPG 2592x1944"), empty when none yet
	after_mark "$1" 33 | grep "^$2 [0-9]* S_FMT" | tail -1 | cut -d' ' -f4-
}
who_gets() { # who_gets LABEL WANT: what a Qt program and a PipeWire program negotiate with the camera now, against the camera's mode
	local want=$2 q p pid
	mark "qt-$1" 33
	LD_PRELOAD=$SHIM "$RUN/probes/qt-probe" /dev/video33 >"$RUN/qt-probe-$1.txt" 2>&1 &
	pid=$!
	until [ -n "$(set_by "qt-$1" qt-probe)" ] || ! kill -0 "$pid" 2>/dev/null; do sleep 0.2; done
	wait "$pid" 2>/dev/null
	q=$(set_by "qt-$1" qt-probe)
	if [ "$q" = "$want" ]; then row "who-qt-program-$1" 0 "Qt set $q"; else gap "who-qt-program-$1" "Qt Multimedia set [$q]; the camera's $1 mode is [$want] (Qt's QPlatformCamera::findBestCameraFormat; probe: $(grep -v '^listed' "$RUN/qt-probe-$1.txt" | tr '\n' '|'))"; fi
	mark "pw-$1" 33
	timeout 20 gst-launch-1.0 -q pipewiresrc target-object=cam-modes stream-properties="props,media.type=Video,media.category=Capture,media.role=Camera" num-buffers=1 ! fakesink >"$RUN/gst-$1.txt" 2>&1
	p=$(set_by "pw-$1" pipewire)
	if [ "$p" = "$want" ]; then row "who-pipewire-program-$1" 0 "PipeWire set $p"; else gap "who-pipewire-program-$1" "PipeWire's V4L2 source set [$p] for a client with no preference of its own (GStreamer pipewiresrc); the camera's $1 mode is [$want] (spa_v4l2_enum_format offers the driver's order)"; fi
}

row_who() {
	clear_all
	replug 33 cam-modes "Virtual camera modes"
	CLI apply cam-modes >/dev/null 2>&1
	who_gets best "MJPG 2592x1944"
	CLI mode cam-modes YUYV 1280x720 10
	replug 33 cam-modes "Virtual camera modes"
	CLI apply cam-modes >/dev/null 2>&1
	who_gets saved "YUYV 1280x720"
}

row_a10manual() {
	# 0.1.3's own rule on the A10's case: a manual temperature set while the control was active is kept, waits under automatic
	# white balance without a problem, and is set again as soon as automatic white balance is off (command and page)
	clear_all
	replug 31 cam-a10 "EasyCamera"
	local idT idW s out rc
	idT=$(cid cam-a10 white_balance_temperature)
	idW=$(cid cam-a10 white_balance_automatic)
	CLI control cam-a10 white_balance_automatic 0
	CLI control cam-a10 white_balance_temperature 3000
	CLI control cam-a10 white_balance_automatic 1
	s=$(store EasyCamera)
	echo "$s" | jq_ "d['controls'].get('$idT')=='3000'" | grep -q True
	row a10-manual-temperature-saved-while-active-is-kept $? "store: $s"
	replug 31 cam-a10 "EasyCamera"
	out=$(CLI apply cam-a10 2>&1)
	rc=$?
	[ "$rc" = 0 ] && [ -z "$(problems EasyCamera)" ] && echo "$out" | grep -q "white_balance_temperature is inactive now; its saved value 3000 waits for it"
	row a10-manual-temperature-waits-without-a-problem $? "exit $rc; $(echo "$out" | grep -v journal | tr '\n' '|') problems [$(problems EasyCamera)]"
	CLI control cam-a10 white_balance_automatic 0 >"$RUN/a10-active-again.txt" 2>&1
	[ "$(cval cam-a10 white_balance_temperature)" = 3000 ]
	row a10-manual-temperature-applies-when-active-again $? "temperature after automatic off: $(cval cam-a10 white_balance_temperature); $(tr '\n' '|' <"$RUN/a10-active-again.txt")"
	CLI control cam-a10 white_balance_automatic 1 >/dev/null 2>&1
	replug 31 cam-a10 "EasyCamera"
	KCM load current=cam-a10 "set=$idW:0" controls | grep '^controls' | cut -d' ' -f2- | python3 -c "
import json,sys
t={c['name']:c for c in json.load(sys.stdin)}['white_balance_temperature']
print('inactive', t['inactive'], 'value', t['value']); sys.exit(0 if (not t['inactive'] and t['value']==3000) else 1)" >"$RUN/page-a10-active-again.txt"
	row page-a10-temperature-applies-when-active-again $? "$(cat "$RUN/page-a10-active-again.txt")"
}

row_sentence() {
	clear_all
	replug 33 cam-modes "Virtual camera modes"
	local en pt
	en=$(QT_QUICK_BACKEND=software KCM load followers "grab=$RUN/page-en.png" | grep -E '^(followers|grab)' | tr '\n' '|')
	echo "$en" | grep -q "follow this default camera; they choose their own picture size and frame rate" && echo "$en" | grep -q "grab .* saved"
	row sentence-on-the-page-english $? "$en"
	pt=$(LANGUAGE=pt_BR LANG=pt_BR.UTF-8 LC_ALL=pt_BR.UTF-8 QT_QUICK_BACKEND=software KCM load followers "grab=$RUN/page-pt_BR.png" | grep -E '^(followers|grab)' | tr '\n' '|')
	echo "$pt" | grep -q "seguem esta câmera padrão; eles escolhem o próprio tamanho de imagem" && echo "$pt" | grep -q "grab .* saved"
	row sentence-on-the-page-portuguese $? "$pt"
}

row_notfound() {
	# every verb that takes a NAME, for a camera that is not there: said, never answered
	clear_all
	local cmd out rc bad="" took start
	for cmd in "formats cam-absent" "best cam-absent" "mode cam-absent" "controls cam-absent" "control cam-absent brightness" "reset cam-absent" \
		"save cam-absent" "packing cam-absent mono" "apply cam-absent" "default cam-absent"; do
		start=$(date +%s%N)
		# shellcheck disable=SC2086
		out=$(CLI $cmd 2>&1)
		rc=$?
		took=$((($(date +%s%N) - start) / 1000000))
		if [ "$rc" = 0 ] || ! echo "$out" | grep -q "No camera called cam-absent is present."; then bad="$bad [$cmd: exit $rc: $(echo "$out" | head -c 80)]"; fi
		echo "$cmd: exit $rc after $took ms: $out" >>"$RUN/notfound.txt"
	done
	[ -z "$bad" ]
	row notfound-every-verb-says-so $? "${bad:-10 verbs exit non-zero with the sentence; times in notfound.txt}"
}

row_restart() {
	# the camera's node is made again while a command asks for it: the command waits for PipeWire's answer instead of saying nothing
	clear_all
	replug 33 cam-modes "Virtual camera modes"
	unplug 33 cam-modes
	# a pw-dump in front of the real one for this row only, so the node comes back only after the command has asked PipeWire once
	mkdir -p "$RUN/bin-restart"
	printf '#!/bin/sh\necho "$$" >>"%s/pw-dump-calls.log"\nexec /usr/bin/pw-dump "$@"\n' "$RUN" >"$RUN/bin-restart/pw-dump"
	chmod +x "$RUN/bin-restart/pw-dump"
	rm -f "$RUN/pw-dump-calls.log"
	(PATH=$RUN/bin-restart:$PATH CLI formats cam-modes >"$RUN/restart-formats.json" 2>"$RUN/restart-formats.err"; echo $? >"$RUN/restart-formats.rc") &
	local pid=$! rc n
	waitfor 20 test -s "$RUN/pw-dump-calls.log"
	plug 33 cam-modes "Virtual camera modes"
	wait "$pid"
	echo "pw-dump calls by the command: $(wc -l <"$RUN/pw-dump-calls.log")" >>"$RUN/restart-formats.err"
	rc=$(cat "$RUN/restart-formats.rc")
	n=$(python3 -c "import json,sys; print(sum(len(f['sizes']) for f in json.load(open(sys.argv[1]))))" "$RUN/restart-formats.json" 2>/dev/null)
	[ "$rc" = 0 ] && [ "$n" = 7 ]
	row restart-command-waits-for-the-node $? "exit $rc, $n sizes; $(head -c 120 "$RUN/restart-formats.err")"
}

row_gone() {
	# PipeWire lists the camera, its device opens and does not answer (going away or still starting): said, never an empty answer
	clear_all
	replug 33 cam-modes "Virtual camera modes"
	touch "$VCAM_ROOT/video33.gone"
	local v out rc bad=""
	for v in formats mode controls best; do
		out=$(CLI "$v" cam-modes 2>&1)
		rc=$?
		echo "$v: exit $rc: $out" >>"$RUN/gone.txt"
		if [ "$rc" = 0 ] || ! echo "$out" | grep -q "is not connected any more"; then bad="$bad [$v: exit $rc: $(echo "$out" | tr '\n' ' ' | head -c 80)]"; fi
	done
	rm -f "$VCAM_ROOT/video33.gone"
	out=$(CLI formats cam-modes 2>&1)
	rc=$?
	[ -z "$bad" ] && [ "$rc" = 0 ]
	row gone-device-said-not-answered-empty $? "${bad:-formats, mode, controls and best exit non-zero with the sentence}; answering again: exit $rc"
}

row_retry() {
	# the unit meets a camera whose device does not answer yet: it tries again at its next pass, and applies when it answers
	clear_all
	unplug 33 cam-modes
	touch "$VCAM_ROOT/video33.gone"
	plug 33 cam-modes "Virtual camera modes"
	LD_PRELOAD=$SHIM sparky-stereo-camera watch >"$RUN/retry-watch.log" 2>&1 &
	local pid=$! m
	waitfor 20 grep -q "camera cam-modes:" "$RUN/retry-watch.log"
	rm -f "$VCAM_ROOT/video33.gone"
	waitfor 20 sh -c "LD_PRELOAD=$SHIM sparky-stereo-camera mode cam-modes 2>/dev/null | grep -q '\"width\": 2592'"
	m=$(modeof cam-modes)
	kill "$pid" 2>/dev/null
	wait "$pid" 2>/dev/null
	[ "$m" = "MJPG 2592 1944 15" ]
	row retry-unit-applies-once-the-device-answers $? "mode $m; $(grep cam-modes "$RUN/retry-watch.log" | tr '\n' '|' | head -c 300)"
}

case $PHASE in
stop)
	. "$ENVFILE" 2>/dev/null
	for p in $(cat "$RUN/pids" 2>/dev/null); do kill "$p" 2>/dev/null; done
	exit 0
	;;
before-upgrade)
	start_session
	PLUGIN=$(dpkg -L sparky-stereo-camera | grep 'kcm_sparkystereo_camera.so$')
	echo "== $(date -u +%FT%TZ) phase before-upgrade, sparky-stereo-camera $(dpkg-query -W -f='${Version}' sparky-stereo-camera)" | tee -a "$ROWS"
	row_before_upgrade
	exit 0
	;;
after-upgrade)
	. "$ENVFILE"
	PLUGIN=$(dpkg -L sparky-stereo-camera | grep 'kcm_sparkystereo_camera.so$')
	echo "== $(date -u +%FT%TZ) phase after-upgrade, sparky-stereo-camera $(dpkg-query -W -f='${Version}' sparky-stereo-camera)" | tee -a "$ROWS"
	row_after_upgrade
	exit 0
	;;
esac
start_session
PLUGIN=$(dpkg -L sparky-stereo-camera | grep 'kcm_sparkystereo_camera.so$')
echo "== $(date -u +%FT%TZ) phase $PHASE, sparky-stereo-camera $(dpkg-query -W -f='${Version}' sparky-stereo-camera), plugin $PLUGIN" | tee -a "$ROWS"
[ $# = 0 ] && set -- imac refusal flags cluster a10 a10manual modes page sentence vaio watch notfound restart gone retry who
for r in "$@"; do "row_$r"; done
echo "== $(date -u +%FT%TZ) done: $(grep -c '^PASS' "$ROWS") PASS, $(grep -c '^FAIL' "$ROWS") FAIL, $(grep -c '^GAP' "$ROWS") GAP" | tee -a "$ROWS"
