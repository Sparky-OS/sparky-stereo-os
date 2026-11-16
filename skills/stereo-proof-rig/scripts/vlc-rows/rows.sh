#!/bin/bash
# SPDX-License-Identifier: MIT
# rows.sh LISTFILE: runs each row of the list, one fresh container each. A line: NAME IMAGE LOCALE SCALE FILM (FILM = the start of a file name in $WORK/fix:
# 3d-silent, 2d-sound, audio-only ...). Environment as drun.sh. The timeline is the same for every row (seconds after VLC starts): the window is placed
# at 3, captures every second from 1 to 16 and at 21.5 (a loaded machine starts VLC late: the notice must be caught wherever it falls), the pointer
# goes over the volume slider at 18, the volume is read through MPRIS at 12 and 28, the Up key (volume up) is pressed at 24.
set -u
here=$(cd "$(dirname "$0")" && pwd)
W=${WORK:?the scratch folder}
while read -r name image locale scale film; do
	case $name in ''|'#'*) continue;; esac
	ksd=""; [ "$scale" != 1 ] && ksd="output.Virtual-0.scale.$scale"
	case $film in 3d-*) ksd="$ksd output.Virtual-0.mode.2";; esac
	"$here/drun.sh" "$image" "$name" LOCALE=$locale SCALE=$scale KSD="$ksd" FILE=/fix/$(ls "$W/fix" | grep "^$film\.") CAPS="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 21.5" HOVER=18 VOLS="12 28" KEYS="24:103" > "$W/rows/$name.out" 2>&1
	echo "$name $image $locale $scale $film rc=$? $(cat "$W/rows/$name/vlc.rc" 2>/dev/null | tr '\n' ' ')"
done < "$1"
