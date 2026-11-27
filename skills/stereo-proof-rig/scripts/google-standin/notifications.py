#!/usr/bin/python3
"""notifications.py FILE: the Notify calls of a dbus-monitor log, one JSON line each (application, summary, body,
action labels, desktop-entry hint, urgency), as the notification server received them."""
import json
import re
import sys

text = open(sys.argv[1], encoding='utf-8', errors='replace').read()
for call in text.split('method call ')[1:]:
	if 'member=Notify' not in call.splitlines()[0]:
		continue
	strings = re.findall(r'^\s+string "((?:[^"\\]|\\.)*)"', call, re.M)
	actions = re.search(r'^\s+array \[\n((?:\s+string .*\n)*)\s+\]', call, re.M)
	labels = re.findall(r'string "((?:[^"\\]|\\.)*)"', actions.group(1))[1::2] if actions else []
	entry = re.search(r'string "desktop-entry"\s+variant\s+string "([^"]*)"', call)
	urgency = re.search(r'string "urgency"\s+variant\s+byte (\d+)', call)
	time = re.search(r'time=([0-9.]+)', call)
	print(json.dumps({'time': float(time.group(1)) if time else None, 'app': strings[0] if strings else None,
		'summary': strings[2] if len(strings) > 2 else None, 'body': strings[3] if len(strings) > 3 else None,
		'actions': labels, 'desktop_entry': entry.group(1) if entry else None,
		'urgency': int(urgency.group(1)) if urgency else None}, ensure_ascii=False))
