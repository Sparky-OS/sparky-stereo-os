#!/bin/sh
# A stored per-file packing wins over the file's own mark: the thumbnail of a left-first side by side file, without and with
# a stored "side by side, right eye first" (libstereo-policy's store, as Dolphin's menu writes it)
set -eu
D=$1; export QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME=$2 XDG_STATE_HOME=$D/state LC_ALL=C.UTF-8
P=/usr/lib/x86_64-linux-gnu/qt6/plugins/kf6/thumbcreator/ffmpegthumbs.so
/opt/thumb-driver/thumb-driver $P $D/files/film.mkv $D/before.png 512 >/dev/null
python3 /scripts/analyze-capture.py $D/before.png 256 | sed 's/^/without a stored choice: /'
python3 - "$D/files/film.mkv" <<'PY'
import ctypes, sys
lib = ctypes.CDLL("libstereo-policy.so.1")
class Choice(ctypes.Structure):
    _fields_ = [("layout", ctypes.c_int), ("order", ctypes.c_int), ("anaglyph", ctypes.c_int), ("view", ctypes.c_int), ("swap_eyes", ctypes.c_int)]
c = Choice(1, 1, 0, 0, 0)  # side by side, right eye first
print("set_file_choice:", lib.stereo_policy_set_file_choice(sys.argv[1].encode(), ctypes.byref(c)))
PY
/opt/thumb-driver/thumb-driver $P $D/files/film.mkv $D/after.png 512 >/dev/null
python3 /scripts/analyze-capture.py $D/after.png 256 | sed 's/^/with "side by side, right eye first" stored: /'
