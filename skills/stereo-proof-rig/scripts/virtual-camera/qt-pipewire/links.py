#!/usr/bin/python3
"""The rig's video graph: the "default" metadata's video keys, each Video/Source node, and for each link
from a Video/Source node the stream it feeds with the process id of that stream's client."""
import json
import subprocess

d = json.loads(subprocess.run(['pw-dump'], capture_output=True, text=True, check=True).stdout)
nodes = {o['id']: o for o in d if o['type'] == 'PipeWire:Interface:Node'}
clients = {o['id']: o['info']['props'] for o in d if o['type'] == 'PipeWire:Interface:Client'}
for o in d:
    if o['type'] == 'PipeWire:Interface:Metadata' and o['props'].get('metadata.name') == 'default':
        keys = [(m['key'], m['value']) for m in o.get('metadata', []) if 'video' in m['key']]
        print('METADATA', json.dumps(keys))
for o in nodes.values():
    p = o['info']['props']
    if p.get('media.class') == 'Video/Source':
        print('NODE', p.get('node.name'), 'api=%s' % p.get('device.api'), o['info']['state'])
seen = set()
for o in d:
    if o['type'] != 'PipeWire:Interface:Link':
        continue
    i = o['info']
    a, b = nodes.get(i['output-node-id']), nodes.get(i['input-node-id'])
    if not a or not b:
        continue
    pa, pb = a['info']['props'], b['info']['props']
    if pa.get('media.class') != 'Video/Source':
        continue
    client = clients.get(pb.get('client.id'), {})
    pid = client.get('application.process.id') or pb.get('application.process.id')
    seen.add((pa.get('node.name'), pb.get('node.name'), pid, i.get('state')))
for s in sorted(seen, key=str):
    print('LINK camera=%s stream=%s pid=%s state=%s' % s)
if not seen:
    print('NO LINK')
