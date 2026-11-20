#!/usr/bin/env python3
"""Join the three reviewed workflow artifacts for iphone-renew.py; never sign/install."""
import argparse
import getpass
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

ROLES = {'kdeconnect':('kdeconnect','org.sparkyos.kdeconnect'),
         'cardboard':('cardboard','org.sparkyos.cardboard'),
         'flat-headset':('flat-headset','org.sparkyos.flatheadset')}

def assemble(root, commit, udid, destination):
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Use the complete reviewed workflow commit')
    apps=[]
    for role,(folder,bundle) in ROLES.items():
        path=root/folder/(role+'-artifact.json')
        record=json.loads(path.read_text())
        if record.get('workflow_commit',record.get('commit')) != commit:
            raise ValueError(role+': artifact is from a different workflow commit')
        rows=record['apps']
        if len(rows)!=1 or rows[0]['role']!=role or rows[0]['bundle_id']!=bundle:
            raise ValueError(role+': unexpected role or bundle identifier')
        row=dict(rows[0])
        relative=Path(row['path'])
        if relative.name!=row['path'] or relative.suffix!='.ipa':
            raise ValueError(role+': expected a simple IPA filename')
        ipa=(path.parent/relative).resolve(strict=True)
        row['path']=os.path.relpath(ipa,destination.parent.resolve())
        apps.append(row)
    return {'udid':udid,'apps':apps}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifacts',type=Path,required=True)
    p.add_argument('--commit',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.output.exists():raise ValueError('Output already exists; keep it for renewal or choose a new filename')
        udid=getpass.getpass('Phone UDID from xtool devices (kept only in the private manifest): ').strip()
        result=assemble(a.artifacts.resolve(),a.commit,udid,a.output)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        descriptor=os.open(a.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(descriptor,'w') as stream:json.dump(result,stream,indent=2);stream.write('\n')
        try:
            spec=importlib.util.spec_from_file_location('renew',Path(__file__).with_name('iphone-renew.py'))
            renew=importlib.util.module_from_spec(spec);spec.loader.exec_module(renew)
            renew.prepare(a.output.resolve())
        except Exception:
            a.output.unlink();raise
        print('PASS: three reviewed IPA hashes and identities; private renewal manifest ready')
        return 0
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(f'No signing or installation attempted: {error}',file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
