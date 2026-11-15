#!/bin/bash
# Dolphin's video thumbnail of each fixture: the ffmpegthumbs plug-in run through KIO's ThumbnailCreator API
# (thumb-driver), without the film strip, then each view measured (analyze-capture.py; a stereo thumbnail holds
# both views side by side, left view first).
# Usage (in the thumbnail image): thumb-run.sh FIXTURES OUTDIR CONFIGDIR [SIZE]
set -u
export QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME=$3 LC_ALL=C.UTF-8
PLUGIN=/usr/lib/x86_64-linux-gnu/qt6/plugins/kf6/thumbcreator/ffmpegthumbs.so
mkdir -p "$2"
python3 - "$1/cases.json" <<'PY' > "$2/list.txt"
import json, sys
for name, c in sorted(json.load(open(sys.argv[1])).items()):
    print(name, c["packing"])
PY
while read -r name packing; do
	out="$2/$name.png"
	/opt/thumb-driver/thumb-driver "$PLUGIN" "$1/$name.mkv" "$out" "${4:-512}" > "$2/$name.log" 2>&1 || { echo "{\"capture\": \"$name\", \"error\": \"no thumbnail\"}"; continue; }
	w=$(python3 -c "from PIL import Image; print(Image.open('$out').size[0])")
	ow=$w; [ "$packing" != mono ] && ow=$((w / 2))
	python3 /scripts/analyze-capture.py "$out" "$ow" | sed "s/\"capture\": \"[^\"]*\"/\"capture\": \"$name\"/"
done < "$2/list.txt"
