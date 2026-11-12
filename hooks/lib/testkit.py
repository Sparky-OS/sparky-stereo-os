# SPDX-License-Identifier: GPL-2.0-or-later
"""testkit: what the hooks' tests share.

Every test makes a toy workspace in the default layout (made by install.py's own init, so the layout the hooks
assume is the layout a person gets), writes the hook's configuration from its example, and runs the hook the way a
tool runs it: the event as JSON on stdin, the answer read from stdout. Nothing outside the temporary folder is used.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HOOKS)
import install  # noqa: E402

MEMORY = {
    'MEMORY.md': '# Memory index\n\n- [Check every default](check-every-default.md): defaults, choices, design check\n'
                 '- [One format inside](one-format-inside.md): the stereo contract\n',
    'check-every-default.md': '---\nname: check-every-default\ndescription: every default a partner sets is checked against the recorded designs\n---\n\n'
                              'A default that was asked for is a design, never a fallback.\nEvery hand-back carries a Design check.\n',
    'one-format-inside.md': '---\nname: one-format-inside\ndescription: programs hand the desktop full side by side, declared once\n---\n\n'
                            'One format inside, output only full side by side.\n',
    'display-design.md': '---\nname: display-design\ndescription: outputs are the compositor\'s filters\n---\n\nThe outputs turn full side by side into each screen\'s format.\n',
    'required-languages.md': '---\nname: required-languages\ndescription: every string ships in ten languages\n---\n\nen, pl, pt_BR, fr, de, es, ja, ko, zh_CN, zh_TW.\n',
    'how-we-write-upstream.md': '---\nname: how-we-write-upstream\ndescription: upstream texts in the sender\'s voice, one ask\n---\n\nOne subject per request.\n',
}
SKILLS = {
    'upstream-outreach/SKILL.md': '---\nname: upstream-outreach\ndescription: Contact with another project.\n---\n\n# Upstream outreach\n\nNever cold.\n',
    'contrib-ffmpeg/SKILL.md': '---\nname: contrib-ffmpeg\ndescription: Contribute to FFmpeg.\n---\n\n# FFmpeg\n\nThe series shape.\n',
}
GOOD_BRIEF = '''# ORDER 7: a demo lane

## Design
Memory one-format-inside.md: "One format inside, output only full side by side".

## Work
1. Do the thing.

## The skill to leave behind
stereo-video gains the recipe.

## Hand-back
STATUS: review first; sections: Design check, Corpus consulted, Skill changes.
'''


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path


def merge(base, changes):
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


class HookCase(unittest.TestCase):
    """A toy workspace per test and the hook under test run against it."""
    hook = None
    dialect = 'claude'

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='hook-test-')
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.ws = os.path.join(self.tmp, 'workspace')
        install.init_workspace(self.ws, say=lambda line: None)
        for name, text in MEMORY.items():
            write(os.path.join(self.ws, 'memory', name), text)
        for rel, text in SKILLS.items():
            write(os.path.join(self.ws, 'repos', 'sparky-stereo-os', 'skills', rel), text)
        write(os.path.join(self.ws, 'partners', 'queue', 'demo-lane', 'BRIEF.md'), GOOD_BRIEF)
        self.config = install.config_path(self.ws, self.hook)
        self.configure(paths={'skills': 'repos/sparky-stereo-os/skills'})

    def configure(self, **changes):
        """Change the hook's configuration for this test."""
        with open(self.config, encoding='utf-8') as f:
            cfg = json.load(f)
        merge(cfg, changes)
        with open(self.config, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
        return cfg

    def memory(self, name):
        return os.path.join(self.ws, 'memory', name)

    def event(self, name, tool=None, tool_input=None, session='session-1', agent=None, **more):
        payload = {'session_id': session, 'transcript_path': os.path.join(self.tmp, session + '.jsonl'),
                   'cwd': self.ws, 'hook_event_name': name}
        if tool:
            payload.update(tool_name=tool, tool_input=tool_input or {})
        if agent:
            payload.update(agent_id=agent, agent_type='general-purpose')
        payload.update(more)
        return payload

    def run_raw(self, stdin_text, config=None, dialect=None, env=None, args=None):
        command = [sys.executable, '-B', os.path.join(HOOKS, self.hook, 'hook.py')]
        if args is None:
            command += ['--config', config or self.config, '--dialect', dialect or self.dialect]
        else:
            command += args
        environment = {k: v for k, v in os.environ.items() if not k.startswith('SPARKY_')}
        environment.update(env or {})
        return subprocess.run(command, input=stdin_text, capture_output=True, text=True, env=environment, timeout=60)

    def run_hook(self, payload, **kw):
        """The hook's answer as a dict, or None when it said nothing. A hook always exits 0 and keeps stderr empty."""
        r = self.run_raw(json.dumps(payload), **kw)
        self.assertEqual((r.returncode, r.stderr), (0, ''), r.stdout)
        return json.loads(r.stdout) if r.stdout.strip() else None

    # reading the tool's own answer
    def decision(self, out):
        return ((out or {}).get('hookSpecificOutput') or {}).get('permissionDecision')

    def reason(self, out):
        return ((out or {}).get('hookSpecificOutput') or {}).get('permissionDecisionReason', '')

    def added_context(self, out):
        return ((out or {}).get('hookSpecificOutput') or {}).get('additionalContext', '')

    def log(self, name):
        path = os.path.join(self.ws, 'state', 'hooks', self.hook, name)
        if not os.path.exists(path):
            return ''
        with open(path, encoding='utf-8') as f:
            return f.read()

    # events a tool sends
    def bash(self, command, phase='PreToolUse', **kw):
        return self.event(phase, 'Bash', {'command': command}, **kw)

    def read(self, path, phase='PostToolUse', **kw):
        tool_input = {'file_path': path}
        tool_input.update(kw.pop('tool_input', {}))
        return self.event(phase, 'Read', tool_input, **kw)
