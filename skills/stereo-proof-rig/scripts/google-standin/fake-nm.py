#!/usr/bin/python3
"""fake-nm.py STATE_FILE: a stand-in NetworkManager on the (private) system bus with the two properties GLib's network
monitor reads (gio/gnetworkmonitornm.c): Connectivity (4, full) and Metered (1 yes, 2 no). STATE_FILE holds "metered" or
"unmetered"; a change is published with PropertiesChanged, as NetworkManager does.
"""
import sys
from gi.repository import Gio, GLib

XML = '''<node><interface name="org.freedesktop.NetworkManager">
<property name="Connectivity" type="u" access="read"/><property name="Metered" type="u" access="read"/>
<property name="State" type="u" access="read"/><property name="NetworkingEnabled" type="b" access="read"/>
<property name="Version" type="s" access="read"/><property name="PrimaryConnection" type="o" access="read"/>
<method name="CheckConnectivity"><arg type="u" direction="out"/></method>
</interface></node>'''
STATE = sys.argv[1]
current = {'metered': None}


def read():
	try:
		return open(STATE).read().strip() == 'metered'
	except OSError:
		return False


def value(name):
	return {'Connectivity': GLib.Variant('u', 4), 'Metered': GLib.Variant('u', 1 if current['metered'] else 2),
		'State': GLib.Variant('u', 70), 'NetworkingEnabled': GLib.Variant('b', True), 'Version': GLib.Variant('s', '1.54.0'),
		'PrimaryConnection': GLib.Variant('o', '/')}[name]


def acquired(connection, name):
	info = Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0]
	connection.register_object('/org/freedesktop/NetworkManager', info,
		lambda c, s, p, i, m, params, inv: inv.return_value(GLib.Variant('(u)', (4,))),
		lambda c, s, p, i, prop: value(prop), None)

	def poll():
		metered = read()
		if metered != current['metered']:
			current['metered'] = metered
			changed = GLib.Variant('(sa{sv}as)', ('org.freedesktop.NetworkManager', {'Metered': value('Metered')}, []))
			connection.emit_signal(None, '/org/freedesktop/NetworkManager', 'org.freedesktop.DBus.Properties',
				'PropertiesChanged', changed)
			print('metered' if metered else 'unmetered', flush=True)
		return True
	poll()
	GLib.timeout_add(200, poll)


current['metered'] = read()
Gio.bus_own_name(Gio.BusType.SYSTEM, 'org.freedesktop.NetworkManager', Gio.BusNameOwnerFlags.NONE, None, acquired,
	lambda *a: sys.exit('name lost'))
GLib.MainLoop().run()
