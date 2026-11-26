#!/usr/bin/python3
"""Print one camera's entry of the Camera page's store (QSettings INI, ~/.config/sparky-stereo-camera/cameras.ini) as JSON:
{"exists": bool, "version": str|None, "format": ..., "controls": {id: value}, "names": {id: name}}.  Usage: store.py FILE CARD-SUBSTRING"""
import json, sys
from urllib.parse import unquote
path, card = sys.argv[1], sys.argv[2]
entry, group = {"exists": False, "controls": {}, "names": {}}, None
try:
    lines = open(path, encoding="utf-8").read().splitlines()
except FileNotFoundError:
    lines = []
for line in lines:
    if line.startswith("[") and line.endswith("]"):
        group = unquote(line[1:-1])
        continue
    if group is None or card not in group or "=" not in line:
        continue
    entry["exists"] = True
    key, value = line.split("=", 1)
    if key.startswith("controls\\"):
        entry["controls"][key.split("\\", 1)[1]] = value
    elif key.startswith("names\\"):
        entry["names"][key.split("\\", 1)[1]] = value
    else:
        entry[key] = value
print(json.dumps(entry, sort_keys=True))
