#!/usr/bin/env python3
"""Build and serve the preview on this machine only, in a disposable static-server container.

python3 site/preview.py          builds, serves on http://localhost:8548/ and waits; Ctrl+C stops it
python3 site/preview.py --open   the same, and opens the address in your own browser once it answers
"""
import argparse
import os
import subprocess
import time
from urllib.error import URLError
from urllib.request import urlopen
from build import build, config
from model import SITE

IMAGE='python@sha256:8c13a3f37a6a5b71498228e902c4b9f51c1f7900d49fabf71f9a650c6120e0d0'

def main():
    p=argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--port',type=int,default=8548)
    p.add_argument('--name',default='fp-548-preview')
    p.add_argument('--open',action='store_true',help='open the address with xdg-open; for a person at the desktop, never for an unattended run')
    a=p.parse_args()
    if not os.environ.get('DOCKER_HOST'): raise SystemExit('Export the authorized DOCKER_HOST socket first.')
    if not 1024 <= a.port <= 65535 or not a.name.startswith('fp-548'): raise SystemExit('Use an unprivileged port and an fp-548 container name.')
    output=SITE/'_build'; address=f'http://localhost:{a.port}/'
    build(output,config(address.rstrip('/'),'/'))
    cmd=['docker','run','--rm','-d','--name',a.name,'--platform','linux/amd64','--ulimit','core=0','--cpus','2',
         '--user',f'{os.getuid()}:{os.getgid()}','--read-only','--cap-drop','ALL',
         '-p',f'127.0.0.1:{a.port}:8000','-v',f'{output}:/site:ro',IMAGE,
         'python3','-m','http.server','8000','--bind','0.0.0.0','--directory','/site']
    subprocess.run(['docker','stop',a.name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
    try:
        deadline=time.monotonic()+20
        while True:
            try:
                with urlopen(address,timeout=2) as answer:
                    if answer.status==200: break
            except (URLError,OSError):
                if time.monotonic()>deadline: raise SystemExit('The preview did not answer on '+address)
                time.sleep(.3)
        print(f'The preview is at {address} (this machine only). Ctrl+C stops it.',flush=True)
        if a.open: subprocess.run(['xdg-open',address],check=False)
        subprocess.run(['docker','wait',a.name],stdout=subprocess.DEVNULL)
    except KeyboardInterrupt:
        pass
    finally:
        subprocess.run(['docker','stop',a.name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

if __name__=='__main__': main()
