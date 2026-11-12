#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""container-guard: on a machine where every partner shares one container daemon, a command acts only on the
containers it names as its own.

Before a shell command, refused:
  an action (kill, stop, rm, restart, pause) on a list of containers that no filter narrows
  (`docker kill $(docker ps -q)`, `docker ps -q | xargs docker stop`);
  an action that names one of the services the configuration protects;
  with "refuse_global_prune" on, a prune of everything on the daemon.
README.md beside this file has the configuration and the reasons.
"""
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import hookkit  # noqa: E402

ACTIONS = r'(?:kill|stop|rm|restart|pause)'


def reason_for(command, cfg):
    engines = '(?:' + '|'.join(re.escape(e) for e in cfg.get('engines') or ['docker', 'podman']) + ')'
    act = re.compile(r'\b' + engines + r'\s+(?:container\s+)?' + ACTIONS + r'\b')
    protected = [p for p in cfg.get('protected') or [] if p]
    if protected:
        service = re.compile(r'\b' + engines + r'\s+(?:container\s+|compose\s+)?' + ACTIONS + r'\b[^|;&\n]*(?<![\w.-])(?:'
                             + '|'.join(re.escape(p) for p in protected) + r')(?![\w.-])')
        if service.search(command):
            return ('this names a service that stays running on this machine (' + ', '.join(protected) + '). '
                    'Act only on your own containers, by name.')
    if cfg.get('refuse_unfiltered_lists', True) and act.search(command):
        listing = r'\b' + engines + r'\s+(?:container\s+)?(?:ps|ls)\b'
        lists = [m.group(1) for m in re.finditer(r'\$\(\s*' + listing + r'([^)]*)\)', command)]
        lists += [m.group(1) for m in re.finditer(r'`\s*' + listing + r'([^`]*)`', command)]
        lists += [m.group(1) for m in re.finditer(listing + r'([^|;&\n]*)\|[^;\n]*\b(?:xargs|while)\b', command)]
        if any(not re.search(r'--filter|(?:^|\s)-f[\s=]', options) for options in lists):
            return ('this would act on every container of the shared daemon, other people\'s services and other lanes\' work '
                    'included. Act only on your own containers, by name or with a filter on your own prefix '
                    '(ps -q --filter name=YOUR_PREFIX).')
    if cfg.get('refuse_global_prune', False):
        prune = re.search(r'\b' + engines + r'\s+(?:system|image|container|volume|builder|network)\s+prune\b([^|;&\n]*)', command)
        if prune and not re.search(r'--filter\s+\S*label', prune.group(1)):
            return ('a prune removes what every lane on the shared daemon left unused, bases that other lanes pinned among '
                    'them. Remove your own images and containers by name.')
    return ''


def handle(event, kit):
    if event.kind != 'before-tool' or event.tool != 'shell':
        return None
    command = event.acting_command()
    why = reason_for(command, kit.cfg)
    if not why:
        return None
    kit.log('refused.log', ' '.join(command.split())[:200])
    return kit.deny('Refused: ' + why)


if __name__ == '__main__':
    sys.exit(hookkit.main('container-guard', handle))
