#!/usr/bin/env python3
"""Build and serve the preview on loopback in a disposable static-server container."""
import argparse
import os
from pathlib import Path
import subprocess
from build import build, config
from model import SITE

IMAGE='python@sha256:8c13a3f37a6a5b71498228e902c4b9f51c1f7900d49fabf71f9a650c6120e0d0'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',type=int,default=8548)
    p.add_argument('--name',default='fp-548-preview')
    a=p.parse_args()
    if not os.environ.get('DOCKER_HOST'): raise SystemExit('Export the authorized DOCKER_HOST socket first.')
    if not 1024 <= a.port <= 65535 or not a.name.startswith('fp-548-'): raise SystemExit('Use an unprivileged port and an fp-548- container name.')
    output=SITE/'_build'
    build(output,config(f'http://localhost:{a.port}','/'))
    print(f'Open http://localhost:{a.port}/ ; Ctrl+C stops the container.',flush=True)
    cmd=['docker','run','--rm','--name',a.name,'--platform','linux/amd64','--ulimit','core=0','--cpus','2',
         '--user',f'{os.getuid()}:{os.getgid()}','--read-only','--cap-drop','ALL',
         '-p',f'127.0.0.1:{a.port}:8000','-v',f'{output}:/site:ro',IMAGE,
         'python3','-m','http.server','8000','--bind','0.0.0.0','--directory','/site']
    try:
        subprocess.run(cmd,check=True)
    except KeyboardInterrupt:
        pass
    finally:
        subprocess.run(['docker','stop',a.name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

if __name__=='__main__': main()
