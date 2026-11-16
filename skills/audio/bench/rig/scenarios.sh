#!/bin/bash
# The proof scenarios (ORDER 631), run in containers of one rig image: scenarios.sh IMAGE TAG EVIDENCE_DIR [SCENARIO...]
# IMAGE is sa631-rig:red (the published set: Debian's PipeWire and WirePlumber, the edition's repository) or
# sa631-rig:green (the same with the staged package installed by apt). Each scenario writes EVIDENCE_DIR/TAG-NAME.jsonl.
# Needs DOCKER_HOST (the lane's socket). Each container is named sa631-NAME and removed when it ends.
set -uo pipefail
IMG=$1 TAG=$2 EV=$3; shift 3
HERE=$(cd "$(dirname "$0")" && pwd)
# HW: an unpacked sparky-stereo-hardware package's usr/share/wireplumber (the headset hook, scenario hook)
HW=${HW:?set HW to the unpacked package's usr/share/wireplumber}
ALL="matrix pulse bluetooth dither24 dither16 person apply weakcpu hook wuh"
SCEN=${*:-$ALL}
run() { # NAME ROOT_PREP COMMAND... : root prepares, then the session runs as the unprivileged user "rig"
	local name=$1 prep=$2; shift 2
	docker run --rm --name "sa631-$name" --cpus 2 --ulimit core=0 -v "$HERE":/src:ro \
		-v "$HW/scripts/sparky-stereo-new-output.lua":/usr/share/wireplumber/scripts/sparky-stereo-new-output.lua:ro \
		-v "$HW/wireplumber.conf.d/50-sparky-stereo-new-output.conf":/usr/share/wireplumber/wireplumber.conf.d/50-sparky-stereo-new-output.conf:ro \
		"$IMG" sh -c "$prep; exec setpriv --reuid 1001 --regid 1001 --clear-groups env HOME=/home/rig bash /src/session.sh $*" 2>/dev/null
}
for s in $SCEN; do
	out=$EV/$TAG-$s.jsonl
	case $s in
	matrix) run matrix : python3 -I /src/proof.py rows | grep '^{' >"$out" ;;
	pulse) run pulse 'export SA631_PULSE=1' "python3 -I /src/proof.py rows --player paplay --devices dac --rates 44100,96000" | grep '^{' >"$out" ;;
	bluetooth) run bt : python3 -I /src/proof.py rows --devices bt --rates 44100,96000 | grep '^{' >"$out" ;;
	dither24) run dither24 : python3 -I /src/proof.py dither | grep '^{' >"$out" ;;
	dither16) run dither16 : python3 -I /src/proof.py dither --source16 | grep '^{' >"$out" ;;
	person) # a person's own files, in the home folder, beside the package's
		run person 'mkdir -p /home/rig/.config/pipewire/pipewire.conf.d /home/rig/.config/pipewire/client.conf.d /home/rig/.config/wireplumber/wireplumber.conf.d
printf "context.properties = {\n  default.clock.rate = 96000\n  default.clock.allowed-rates = [ 44100 96000 ]\n}\n" >/home/rig/.config/pipewire/pipewire.conf.d/99-clock-rates.conf
printf "stream.properties = {\n  resample.quality = 7\n}\n" >/home/rig/.config/pipewire/client.conf.d/99-quality.conf
printf "monitor.alsa.rules = [ { matches = [ { node.name = \"~alsa_output.*\" } ] actions = { update-props = { resample.quality = 6, dither.method = none } } } ]\n" >/home/rig/.config/wireplumber/wireplumber.conf.d/99-mine.conf
chown -R 1001:1001 /home/rig/.config' \
			"python3 -I /src/proof.py rows --devices dac,pcm16 --rates 44100,88200,96000,192000" | grep '^{' >"$out"
		run personapply 'mkdir -p /home/rig/.config/pipewire/pipewire.conf.d
printf "context.properties = {\n  default.clock.rate = 96000\n  default.clock.allowed-rates = [ 44100 96000 ]\n}\n" >/home/rig/.config/pipewire/pipewire.conf.d/99-clock-rates.conf
chown -R 1001:1001 /home/rig/.config' "python3 -I /src/proof.py apply" | grep '^{' >"$EV/$TAG-personapply.jsonl" ;;
	apply) # the list written before a USB DAC was plugged in; the session then gets the live list from PipeWire itself
		run apply 'f=/etc/pipewire/pipewire.conf.d/00-sparky-stereo-audio.conf; [ -f $f ] && sed -i "s/allowed-rates = .*/allowed-rates = [ 44100 48000 ]/" $f || true' \
			"python3 -I /src/proof.py liveapply" | grep '^{' >"$out" ;;
	weakcpu) # a processor that cannot carry quality 14: the same detection with a cost of 90 percent for the heaviest conversion
		run weakcpu 'command -v sparky-stereo-audio >/dev/null && { rm -rf /var/lib/sparky-stereo-audio; SPARKY_STEREO_AUDIO_PROC=/opt/sa631/proc-asound SPARKY_STEREO_AUDIO_CPU_COST=90 sparky-stereo-audio detect --write >/dev/null; } || true' \
			"python3 -I /src/proof.py rows --devices dac --rates 44100,192000" | grep '^{' >"$out" ;;
	hook) # the headset hook of sparky-stereo-hardware (the published file)
		run hook : "python3 -I /src/proof.py hook" | grep '^{' >"$out" ;;
	wuh) # the What U Hear bridge (a pw-loopback client from a user unit): one sink's monitor played to another
		run wuh : "python3 -I /src/proof.py wuh" | grep '^{' >"$out" ;;
	esac
	echo "$s: $(wc -l <"$out") lines"
done
