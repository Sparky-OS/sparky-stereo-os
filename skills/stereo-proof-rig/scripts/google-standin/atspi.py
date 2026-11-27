#!/usr/bin/python3
"""atspi.py: read and press an application's widgets through AT-SPI, by role and name, as an assistive tool does.

  atspi.py tree APP                      print every node: depth, role, name, actions, showing
  atspi.py press APP ROLE NAME [N]       do the first action of the Nth (default 1st) showing node with that role and name
  atspi.py wait APP ROLE NAME SECONDS    exit 0 once such a node shows, 1 on timeout
  atspi.py text APP ROLE NAME TEXT       set the text of an editable node
  atspi.py focus APP ROLE NAME           give the node the keyboard focus (then keys through fake input)
NAME matches when it equals the node's name or, with a leading ~, when it is contained in it.
"""
import sys
import time

import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi


def apps(name):
	desktop = Atspi.get_desktop(0)
	for i in range(desktop.get_child_count()):
		app = desktop.get_child_at_index(i)
		if app is not None and name.lower() in (app.get_name() or '').lower():
			yield app


def walk(node, depth=0):
	yield node, depth
	try:
		count = node.get_child_count()
	except Exception:
		return
	for i in range(count):
		try:
			child = node.get_child_at_index(i)
		except Exception:
			continue
		if child is not None:
			yield from walk(child, depth + 1)


def showing(node):
	try:
		return node.get_state_set().contains(Atspi.StateType.SHOWING)
	except Exception:
		return False


def action_names(node):
	iface = node.get_action_iface()
	if iface is None:
		return []
	return [iface.get_action_name(i) for i in range(iface.get_n_actions())]


def matches(node, role, name):
	try:
		node_role, node_name = node.get_role_name(), node.get_name() or ''
	except Exception:
		return False
	hit = name[1:] in node_name if name.startswith('~') else node_name == name
	return node_role == role and hit and showing(node)


def find(app_name, role, name, nth=1):
	seen = 0
	for app in apps(app_name):
		for node, _ in walk(app):
			if matches(node, role, name):
				seen += 1
				if seen == nth:
					return node
	return None


def main():
	command = sys.argv[1]
	if command == 'tree':
		for app in apps(sys.argv[2]):
			for node, depth in walk(app):
				try:
					print(f"{'  ' * depth}{node.get_role_name()} | {node.get_name()!r} | {action_names(node)} | {'showing' if showing(node) else ''}")
				except Exception as error:
					print(f"{'  ' * depth}? {error}")
		return 0
	if command == 'wait':
		deadline = time.time() + float(sys.argv[5])
		while time.time() < deadline:
			if find(sys.argv[2], sys.argv[3], sys.argv[4]):
				return 0
			time.sleep(0.5)
		return 1
	node = find(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]) if command in ('press', 'focus') and len(sys.argv) > 5 else 1)
	if node is None:
		print(f'not found: {sys.argv[3]} {sys.argv[4]!r}', file=sys.stderr)
		return 1
	if command == 'press':
		iface = node.get_action_iface()
		if iface is None or iface.get_n_actions() == 0:
			print('no action', file=sys.stderr)
			return 1
		return 0 if iface.do_action(0) else 1
	if command == 'focus':
		component = node.get_component_iface()
		return 0 if component is not None and component.grab_focus() else 1
	if command == 'text':
		iface = node.get_editable_text_iface()
		return 0 if iface is not None and iface.set_text_contents(sys.argv[5]) else 1
	return 2


sys.exit(main())
