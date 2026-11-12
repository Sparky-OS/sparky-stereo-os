#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""design-reading: the recorded designs are read before work, and again whenever the context was read cold.

Events: session start (new, resumed, cleared, after a compaction), every prompt, before every tool, after a read.
While a required file is unread, every tool but the reading ones is refused with the list.
A file read in full is crossed off. README.md beside this file has the configuration and the reasons.
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import hookkit  # noqa: E402

READ_TOOLS = ['Read', 'Glob', 'Grep', 'ToolSearch', 'TaskOutput']
BRIEF = r'(?:BRIEF[^/\s"\'`]*|AGENTS)\.md'


def reading_text(kit, pending, why):
    memory = kit.path('memory')
    lines = [f'[Required reading ({why}). These files hold the recorded designs. Each one is read in full, with the '
             'file-reading tool, before any other tool runs; until then other tools are refused.]']
    lines += [f'- {os.path.join(memory, name)}' for name in pending]
    hint = kit.lookup_hint('WORD...')
    if hint:
        lines.append('Before a brief, an acceptance or a report of a default or a choice: search the memory by content '
                     f'for the package and the feature words ({hint}), read what it names and quote the lines that govern.')
    subjects = kit.cfg.get('also_on_subject') or []
    if subjects:
        lines.append('Read in full before work on their subject: ' + '; '.join(subjects) + '.')
    return '\n'.join(lines)


def agent_prompt(event):
    """The prompt an agent was started with, from the tool's own record of it; empty when it cannot be found."""
    transcript = str(event.raw.get('transcript_path') or '')
    path = event.raw.get('agent_transcript_path')
    if not path and event.agent and transcript.endswith('.jsonl'):
        path = os.path.join(transcript[:-6], 'subagents', f'agent-{event.agent}.jsonl')
    if not path:
        return ''
    with open(path, encoding='utf-8', errors='replace') as f:
        content = (json.loads(f.readline()).get('message') or {}).get('content')
    if isinstance(content, str):
        return content
    return ' '.join(b.get('text', '') for b in content or [] if isinstance(b, dict))


def lane_named(event, kit):
    """The memory files an agent's prompt or its brief names, and those its subject calls for."""
    memory = kit.path('memory')
    queue = kit.path('queue')
    texts = [agent_prompt(event)]
    brief = re.compile(re.escape(queue) + r'/[^\s"\'`]+?/' + (kit.cfg.get('brief_pattern') or BRIEF))
    for path in brief.findall(texts[0]):
        try:
            with open(path, encoding='utf-8', errors='replace') as f:
                texts.append(f.read(400_000))
        except OSError as e:
            kit.log('errors.log', f'lane brief {path}: {e.strerror}')
    text = '\n'.join(texts)
    index = os.path.basename(kit.path('memory_index'))
    names = []
    for name in re.findall(r'\b([a-z0-9][a-z0-9-]*\.md)\b', text):
        if name not in names and name != index and os.path.exists(os.path.join(memory, name)):
            names.append(name)
    for rule in kit.cfg.get('subject_rules') or []:
        if re.search(rule['pattern'], text, re.I):
            names += [n for n in rule.get('read', []) if n not in names and os.path.exists(os.path.join(memory, n))]
    return names[:int(kit.cfg.get('lane_named_max', 16))]


def start_reading(kit, why):
    memory = kit.path('memory')
    kit.state['pending'] = [n for n in kit.cfg.get('core') or [] if os.path.exists(os.path.join(memory, n))]
    kit.state['why'] = why
    kit.state['since'] = kit.now


def handle(event, kit):
    state = kit.state
    gap = kit.now - state.get('last_seen', 0)
    state['last_seen'] = kit.now

    if event.kind == 'session-start':
        if not kit.on('session_start'):
            return None
        start_reading(kit, f'session {event.source or "start"}')
        return kit.context(reading_text(kit, state['pending'], state['why'])) if state['pending'] else None

    if event.kind in ('before-tool', 'prompt') and gap >= float(kit.cfg.get('gap_seconds', 3300)) and not state.get('pending'):
        first = 'since' not in state
        if (first and kit.on('first_call')) or (not first and kit.on('gap')):
            start_reading(kit, 'first call in this context' if first
                          else f'{int(gap // 60)} minutes since the last call: the context is read cold again')
            if first and event.agent and kit.on('lane_named'):
                try:
                    state['pending'] += [n for n in lane_named(event, kit) if n not in state['pending']]
                except Exception as e:  # the tool's record of the agent is not a stable interface
                    kit.log('errors.log', f'lane_named: {e!r}')

    if event.kind == 'after-tool':
        memory = os.path.realpath(kit.path('memory'))
        for path in event.reads(kit.cfg.get('shell_reads')):
            real = os.path.realpath(path)
            if os.path.dirname(real) == memory and os.path.basename(real) in state.get('pending', []):
                state['pending'].remove(os.path.basename(real))
                if not state['pending']:
                    kit.log('reads.log', f'{event.session[-24:]} read all ({state.get("why")})')
        return None

    pending = state.get('pending')
    if not pending:
        return None
    text = reading_text(kit, pending, state.get('why', ''))
    if event.kind == 'prompt':
        return kit.context(text)
    if event.kind == 'before-tool':
        free = kit.cfg.get('read_tools', READ_TOOLS)
        prefixes = tuple(kit.cfg.get('free_tool_prefixes', ['mcp__']))
        if event.tool_name in free or (prefixes and event.tool_name.startswith(prefixes)):
            return None
        if event.tool == 'shell' and event.reads(kit.cfg.get('shell_reads')):
            return None  # where reading is a shell command, a plain cat is the reading tool
        kit.log('refused.log', f'{event.tool_name} while {len(pending)} unread ({state.get("why")})')
        return kit.deny(text)
    return None


if __name__ == '__main__':
    sys.exit(hookkit.main('design-reading', handle))
