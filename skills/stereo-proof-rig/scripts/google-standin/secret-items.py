#!/usr/bin/python3
"""secret-items.py APPLICATION: DriveSync's items in the Secret Service, read through the interface (org.freedesktop.secrets).

Prints for each item: its label, its attributes, whether it is locked, and for its secret only the fields DriveSync's
envelope has, with the access token as the first 12 hex digits of its SHA-256 (never the token). Exit 2 when no service
answers, 1 when no item matches.
"""
import hashlib
import json
import sys
from gi.repository import Gio, GLib

app = sys.argv[1]
bus = Gio.bus_get_sync(Gio.BusType.SESSION)
def call(path, iface, method, args, reply):
	return bus.call_sync('org.freedesktop.secrets', path, iface, method, args, GLib.VariantType(reply), Gio.DBusCallFlags.NONE, 5000, None)
try:
	unlocked, locked = call('/org/freedesktop/secrets', 'org.freedesktop.Secret.Service', 'SearchItems',
		GLib.Variant('(a{ss})', ({'application': app},)), '(aoao)').unpack()
	_, session = call('/org/freedesktop/secrets', 'org.freedesktop.Secret.Service', 'OpenSession',
		GLib.Variant('(sv)', ('plain', GLib.Variant('s', ''))), '(vo)').unpack()
except GLib.Error as error:
	print('no Secret Service:', error.message)
	sys.exit(2)
owner = bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus', 'GetNameOwner',
	GLib.Variant('(s)', ('org.freedesktop.secrets',)), GLib.VariantType('(s)'), Gio.DBusCallFlags.NONE, 5000, None).unpack()[0]
pid = bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus', 'GetConnectionUnixProcessID',
	GLib.Variant('(s)', (owner,)), GLib.VariantType('(u)'), Gio.DBusCallFlags.NONE, 5000, None).unpack()[0]
import os
print('service owner:', owner, os.readlink(f'/proc/{pid}/exe'))
print('unlocked items:', len(unlocked), 'locked items:', len(locked))
for path in unlocked:
	props = call(path, 'org.freedesktop.DBus.Properties', 'GetAll', GLib.Variant('(s)', ('org.freedesktop.Secret.Item',)), '(a{sv})').unpack()[0]
	secret = call(path, 'org.freedesktop.Secret.Item', 'GetSecret', GLib.Variant('(o)', (session,)), '((oayays))').unpack()[0]
	value = json.loads(bytes(secret[2]))
	shown = {k: v for k, v in value.items() if k not in ('access', 'refresh')}
	shown['access_sha256_12'] = hashlib.sha256(value['access'].encode()).hexdigest()[:12]
	shown['refresh_present'] = bool(value.get('refresh'))
	print(json.dumps({'path': path, 'label': props.get('Label'), 'attributes': props.get('Attributes'), 'content_type': secret[3],
		'secret': shown}, sort_keys=True))
sys.exit(0 if unlocked or locked else 1)
