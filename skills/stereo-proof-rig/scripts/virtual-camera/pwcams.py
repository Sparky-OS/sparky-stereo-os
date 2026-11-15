#!/usr/bin/python3
"""Compact view of the rig's PipeWire video sources and the default-video metadata."""
import json, subprocess
d = json.loads(subprocess.run(['pw-dump'], capture_output=True, text=True, check=True).stdout)
for o in d:
    if o['type'] == 'PipeWire:Interface:Node':
        p = o['info']['props']
        if 'Video' in p.get('media.class', ''):
            print('node', o['id'], p.get('media.class'), p.get('node.name'), p.get('api.v4l2.path'), o['info']['state'])
    if o['type'] == 'PipeWire:Interface:Metadata' and o['props'].get('metadata.name') == 'default':
        print('default', [(m['key'], m['value']) for m in o.get('metadata', []) if 'video' in m['key']])
