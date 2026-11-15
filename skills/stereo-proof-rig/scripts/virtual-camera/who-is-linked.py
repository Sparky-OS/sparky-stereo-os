#!/usr/bin/python3
"""Print, for each PipeWire link, the camera node (Video/Source) it comes from and the client node it goes to."""
import json, subprocess
d = json.loads(subprocess.run(['pw-dump'], capture_output=True, text=True, check=True).stdout)
nodes = {o['id']: o['info']['props'] for o in d if o['type'] == 'PipeWire:Interface:Node'}
seen = set()
for o in d:
    if o['type'] == 'PipeWire:Interface:Link':
        i = o['info']
        a, b = nodes.get(i['output-node-id'], {}), nodes.get(i['input-node-id'], {})
        if 'Video' in a.get('media.class', ''):
            seen.add((a.get('node.name'), b.get('node.name') or b.get('application.name')))
for s in sorted(seen, key=str):
    print('LINK camera=%s client=%s' % s)
if not seen:
    print('NO LINK')
