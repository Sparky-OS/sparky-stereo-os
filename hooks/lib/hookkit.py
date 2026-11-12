# SPDX-License-Identifier: GPL-2.0-or-later
"""hookkit: what every hook in this folder shares.

A hook is a program that reads one event as JSON on stdin and writes one answer as JSON on stdout.
Its logic works on a plain event and a plain answer.
This module does the rest:
- it turns a tool's own event into the plain one and the plain answer into the tool's own (a dialect per tool);
- it finds the hook's one configuration file and the folders of the workspace it names;
- it keeps the hook's state, one file per session or agent, and its logs;
- it makes every failure inside a hook fail open: the action goes ahead, the failure is written to errors.log,
  and the person is told in one line.

A hook's own file is small: it defines handle(event, kit) and calls main("its-name", handle).
"""
import fcntl
import hashlib
import json
import os
import re
import shlex
import sys
import time
import traceback

# The default folder layout, relative to the workspace. Every path is a configuration value: "paths" in a
# hook's configuration replaces any of them, with a path relative to the workspace or an absolute one.
LAYOUT = {
    'memory': 'memory',
    'memory_index': 'memory/MEMORY.md',
    'skills': 'repos/sparky-stereo-os/skills',
    'partners': 'partners',
    'queue': 'partners/queue',
    'private': 'private',
    'drafts': 'private/drafts',
    'state': 'state/hooks',
}

# What each tool calls its events and its tools. "can_ask" says whether the tool can put a question to the person
# from a hook; where it cannot, an "ask" answer becomes what the hook's configuration says ("ask_becomes").
DIALECTS = {
    'claude': {
        'events': {'SessionStart': 'session-start', 'UserPromptSubmit': 'prompt',
                   'PreToolUse': 'before-tool', 'PostToolUse': 'after-tool'},
        'tools': {'Bash': 'shell', 'Read': 'read', 'Write': 'write', 'Edit': 'edit',
                  'Agent': 'dispatch', 'Task': 'dispatch', 'SubagentHandback': 'handback'},
        'can_ask': True,
        'shell_reads': False,
    },
    'codex': {
        'events': {'SessionStart': 'session-start', 'UserPromptSubmit': 'prompt',
                   'PreToolUse': 'before-tool', 'PostToolUse': 'after-tool'},
        'tools': {'Bash': 'shell', 'apply_patch': 'write', 'spawn_agent': 'dispatch', 'Agent': 'dispatch'},
        'can_ask': False,
        'shell_reads': True,
    },
}
CONTEXT_LIMIT = 9000
SHELL_SYNTAX = re.compile(r'[|;&<>`$(){}\n]')
PATCH_FILE = re.compile(r'^\*\*\* (?:Add|Update) File: (.+)$', re.M)


SHELLS = {'sh', 'bash', 'dash', 'zsh', 'ksh'}
WRAPPERS = {'env', 'command', 'exec', 'nohup', 'time', 'timeout', 'nice', 'ionice', 'stdbuf', 'setsid', 'sudo', 'xargs'}
WRAPPER_OPTIONS_WITH_VALUE = {'-u', '-g', '-n', '-s', '-k', '-I', '-P', '-L', '-d', '-c', '-C', '-p', '-r', '-t', '-D', '-h'}
HEREDOC = re.compile(r'<<-?[ \t]*(?:\'([\w.-]+)\'|"([\w.-]+)"|\\?([\w.-]+))([^\n]*)\n')
ASSIGNMENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')


def acting_text(command):
    """The command without the text it only carries: the body of a here-document counts as commands when a shell
    reads it (bash <<EOF) and is dropped otherwise (cat > file <<EOF, python3 - <<EOF), so a file being written
    is not taken for a command being run."""
    out, pos = [], 0
    while True:
        m = HEREDOC.search(command, pos)
        if not m:
            break
        word = m.group(1) or m.group(2) or m.group(3)
        end = re.compile(r'^\t*' + re.escape(word) + r'[ \t]*$', re.M).search(command, m.end())
        body_end = end.end() if end else len(command)
        owner = re.split(r'[\n;|&(){}]', command[:m.start()])[-1].split()
        read_by_shell = any(os.path.basename(w) in SHELLS for w in owner) or '|' in m.group(4)
        out.append(command[pos:m.end()])
        if read_by_shell:
            out.append(command[m.end():body_end])
        pos = body_end
    out.append(command[pos:])
    return ''.join(out)


def shell_commands(command, depth=0):
    """The simple commands a shell line runs, each as its list of words, wrappers such as env or timeout taken off
    and the text given to sh -c read as commands too. None when the line cannot be read as shell (the caller then
    searches the text instead). A guard built on this is a guard rail, not a wall: a program can still hide a
    command where no reader of shell text finds it."""
    text = acting_text(command).replace('\n', ' ; ')
    try:
        lex = shlex.shlex(text, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        return None
    commands, current, skip = [], [], False
    for token in tokens:
        if skip:
            skip = False
            continue
        if token and all(c in '();<>|&' for c in token):
            if '<' in token or '>' in token:
                skip = True  # a redirection: its target is a file, not a word of the command
                if current and current[-1].isdigit():
                    current.pop()  # the descriptor number of 2>&1
                continue
            if current:
                commands.append(current)
            current = []
        else:
            current.append(token)
    if current:
        commands.append(current)
    out = []
    for words in commands:
        words = _unwrap(words)
        if not words:
            continue
        name = os.path.basename(words[0])
        inner = None
        if name in SHELLS and '-c' in words[1:] and words.index('-c') + 1 < len(words):
            inner = words[words.index('-c') + 1]
        elif name == 'eval':
            inner = ' '.join(words[1:])
        if inner is not None and depth < 3:
            sub = shell_commands(inner, depth + 1)
            if sub is None:
                return None
            out += sub
        else:
            out.append(words)
    return out


def _unwrap(words):
    """Drop leading VAR=value words and wrapper programs with their own options."""
    words = list(words)
    while words:
        if ASSIGNMENT.match(words[0]):
            words.pop(0)
        elif os.path.basename(words[0]) in WRAPPERS:
            wrapper = os.path.basename(words.pop(0))
            while words and (words[0].startswith('-') or (wrapper == 'env' and ASSIGNMENT.match(words[0]))):
                option = words.pop(0)
                if option in WRAPPER_OPTIONS_WITH_VALUE and words:
                    words.pop(0)
            if wrapper == 'timeout' and words:
                words.pop(0)  # the duration
        else:
            break
    return words


def git_subcommand(words):
    """("push", the words after it) for a git command line, skipping git's own options; (None, []) otherwise."""
    if not words or os.path.basename(words[0]) != 'git':
        return None, []
    i = 1
    while i < len(words) and words[i].startswith('-'):
        i += 2 if words[i] in ('-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path') else 1
    return (words[i], words[i + 1:]) if i < len(words) else (None, [])


def git_folder(words, cwd):
    """The folder a git command line acts in: its -C option, else cwd."""
    for i, word in enumerate(words[:-1]):
        if word == '-C':
            path = os.path.expanduser(words[i + 1])
            return path if os.path.isabs(path) else os.path.join(cwd, path)
    return cwd


class HookError(Exception):
    """The hook cannot do its work, and the message says what to do."""


class Event:
    """One event of a tool, in plain terms."""

    def __init__(self, payload, dialect):
        names = DIALECTS[dialect]
        self.raw = payload
        self.dialect = dialect
        self.name = str(payload.get('hook_event_name') or '')
        self.kind = names['events'].get(self.name, 'other')
        self.tool_name = str(payload.get('tool_name') or '')
        self.tool = names['tools'].get(self.tool_name, self.tool_name)
        tool_input = payload.get('tool_input')
        self.input = tool_input if isinstance(tool_input, dict) else {}
        self.agent = payload.get('agent_id') or None
        self.session = str(self.agent or payload.get('transcript_path') or payload.get('session_id') or 'unknown')
        self.cwd = str(payload.get('cwd') or os.getcwd())
        self.source = str(payload.get('source') or '')
        self.prompt = str(payload.get('prompt') or '')
        self.command = str(self.input.get('command') or '') if self.tool == 'shell' else ''
        self.path = ''
        self.paths = []
        self.text = ''
        self.whole = False
        if self.tool == 'read':
            self.path = self._absolute(self.input.get('file_path'))
            self.whole = not self.input.get('offset') and not self.input.get('limit')
        elif self.tool in ('write', 'edit'):
            if self.tool_name == 'apply_patch':
                self.text = str(self.input.get('command') or '')
                self.paths = [self._absolute(p.strip()) for p in PATCH_FILE.findall(self.text)]
                self.path = self.paths[0] if self.paths else ''
            else:
                self.path = self._absolute(self.input.get('file_path'))
                self.paths = [self.path] if self.path else []
                self.text = str(self.input.get('content') or '') if self.tool == 'write' else str(self.input.get('new_string') or '')
        elif self.tool == 'dispatch':
            prompt = self.input.get('prompt')
            self.text = prompt if isinstance(prompt, str) else json.dumps(self.input)
        elif self.tool == 'handback':
            self.text = str(self.input.get('message') or '')

    def _absolute(self, path):
        if not path:
            return ''
        path = os.path.expanduser(str(path))
        return path if os.path.isabs(path) else os.path.join(self.cwd, path)

    def acting_command(self):
        """The shell command without the text it only writes to files."""
        return acting_text(self.command)

    def commands(self):
        """The simple commands the shell line runs (see shell_commands); None when it cannot be read as shell."""
        return shell_commands(self.command)

    def working_folder(self, words=None):
        """Where a simple command of this line runs: the folder of a `cd DIR &&` before it, else the event's cwd."""
        m = re.search(r'(?:^|[;&|\n])\s*cd\s+("[^"]+"|\'[^\']+\'|\S+)\s*(?:&&|;|\n)', self.acting_command())
        if not m:
            return self.cwd
        path = os.path.expanduser(m.group(1).strip('\'"'))
        return path if os.path.isabs(path) else os.path.join(self.cwd, path)

    def reads(self, shell_reads=None):
        """The files this event read in full. A plain `cat FILE...` counts where the tool has no reading tool of
        its own, or where the hook's configuration says so ("shell_reads")."""
        if self.tool == 'read':
            return [self.path] if self.whole and self.path else []
        if shell_reads is None:
            shell_reads = DIALECTS[self.dialect]['shell_reads']
        if self.tool == 'shell' and shell_reads and not SHELL_SYNTAX.search(self.command):
            try:
                words = shlex.split(self.command)
            except ValueError:
                return []
            if len(words) > 1 and words[0] == 'cat' and not any(w.startswith('-') for w in words[1:]):
                return [self._absolute(w) for w in words[1:]]
        return []


class Kit:
    """What a hook's logic is handed besides the event: its configuration, its folders, its state and its logs."""

    def __init__(self, name, cfg, config_path):
        self.name = name
        self.cfg = cfg
        self.config_path = config_path
        self.now = time.time()
        workspace = cfg.get('workspace') or os.environ.get('SPARKY_WORKSPACE')
        if not workspace:
            raise HookError(f'no workspace: set "workspace" in {config_path}')
        self.workspace = os.path.abspath(os.path.expanduser(str(workspace)))
        self.state_dir = os.path.join(self.path('state'), name)
        self.state = {}
        self._state_file = None
        self._lock = None

    def path(self, key):
        """A folder or file of the layout: "paths" in the configuration, else the default."""
        value = (self.cfg.get('paths') or {}).get(key, LAYOUT.get(key))
        if value is None:
            raise HookError(f'no path named "{key}": add it under "paths" in {self.config_path}')
        return self.resolve(value)

    def resolve(self, value):
        """A path of the configuration: absolute, or from the workspace, or from a folder of the layout when it is
        written "memory:file.md" or "skills:name/SKILL.md"."""
        value = str(value)
        key, colon, rest = value.partition(':')
        if colon and key in LAYOUT:
            return os.path.normpath(os.path.join(self.path(key), rest))
        value = os.path.expanduser(value)
        return os.path.normpath(value if os.path.isabs(value) else os.path.join(self.workspace, value))

    def lookup_hint(self, words):
        """The command that searches the memory by content, for a refusal or a reading text: the configuration's
        own text, none when it says false, else the lookup beside this file."""
        hint = self.cfg.get('lookup_hint', True)
        if hint is True:
            return f'python3 {os.path.join(os.path.dirname(os.path.abspath(__file__)), "design_lookup.py")} --memory {self.path("memory")} {words}'
        return hint or ''

    def on(self, key, default=True):
        """A switch under "on" in the configuration: what the hook enforces is the person's choice."""
        return bool((self.cfg.get('on') or {}).get(key, default))

    def open_state(self, event):
        os.makedirs(self.state_dir, exist_ok=True)
        key = hashlib.sha1(event.session.encode()).hexdigest()[:16]
        self._state_file = os.path.join(self.state_dir, key + '.json')
        self._lock = open(os.path.join(self.state_dir, key + '.lock'), 'w')
        for _ in range(50):  # parallel tool calls run this hook several times at once
            try:
                fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                time.sleep(0.1)
        else:
            self.log('errors.log', f'state lock not taken after 5 s: {self._state_file}')
        try:
            with open(self._state_file, encoding='utf-8') as f:
                self.state = json.load(f)
        except (OSError, ValueError):
            self.state = {}
        self._prune()

    def save_state(self):
        if self._state_file:
            tmp = f'{self._state_file}.{os.getpid()}.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.state, f)
            os.replace(tmp, self._state_file)

    def _prune(self):
        """Once a day, drop the state of sessions not seen for "state_keep_days" (30) and cut logs over 1 MiB."""
        stamp = os.path.join(self.state_dir, '.pruned')
        try:
            if self.now - os.path.getmtime(stamp) < 86400:
                return
        except OSError:
            pass
        with open(stamp, 'w'):
            pass
        keep = float(self.cfg.get('state_keep_days', 30)) * 86400
        for entry in os.scandir(self.state_dir):
            try:
                if entry.name.endswith(('.json', '.lock')) and self.now - entry.stat().st_mtime > keep:
                    os.unlink(entry.path)
                elif entry.name.endswith('.log') and entry.stat().st_size > 1 << 20:
                    os.replace(entry.path, entry.path + '.1')
            except OSError:
                pass

    def log(self, filename, line):
        write_log(self.state_dir, filename, line)

    # the plain answers
    @staticmethod
    def deny(reason):
        return {'decision': 'deny', 'reason': reason}

    @staticmethod
    def ask(reason):
        return {'decision': 'ask', 'reason': reason}

    @staticmethod
    def context(text):
        return {'context': text}


def write_log(folder, filename, line):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, filename), 'a', encoding='utf-8') as f:
        f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ ', time.gmtime()) + ' '.join(str(line).split()) + '\n')


def fallback_state_dir(name):
    base = os.environ.get('XDG_STATE_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'state')
    return os.path.join(base, 'sparky-stereo-hooks', name)


def find_config(name, argv):
    """--config FILE, else SPARKY_HOOKS_CONFIG_DIR/<name>.json, else SPARKY_WORKSPACE/private/hooks/<name>.json."""
    if '--config' in argv:
        i = argv.index('--config')
        if i + 1 >= len(argv):
            raise HookError('--config needs a file')
        return argv[i + 1]
    if os.environ.get('SPARKY_HOOKS_CONFIG_DIR'):
        return os.path.join(os.environ['SPARKY_HOOKS_CONFIG_DIR'], name + '.json')
    if os.environ.get('SPARKY_WORKSPACE'):
        return os.path.join(os.environ['SPARKY_WORKSPACE'], LAYOUT['private'], 'hooks', name + '.json')
    raise HookError(f'no configuration named: wire the hook with --config /path/to/{name}.json')


def load_config(path):
    try:
        with open(path, encoding='utf-8') as f:
            cfg = json.load(f)
    except OSError as e:
        raise HookError(f'cannot read the configuration {path}: {e.strerror}') from e
    except ValueError as e:
        raise HookError(f'the configuration {path} is not valid JSON: {e}') from e
    if not isinstance(cfg, dict):
        raise HookError(f'the configuration {path} must be a JSON object')
    return cfg


def dialect_of(argv, cfg):
    name = cfg.get('dialect') or os.environ.get('SPARKY_HOOK_DIALECT') or 'claude'
    if '--dialect' in argv and argv.index('--dialect') + 1 < len(argv):
        name = argv[argv.index('--dialect') + 1]
    if name not in DIALECTS:
        raise HookError(f'unknown dialect "{name}": one of {", ".join(sorted(DIALECTS))}')
    return name


def render(event, answer, ask_becomes='deny'):
    """The plain answer in the tool's own JSON; None when there is nothing to say."""
    out = {}
    if answer.get('notice'):
        out['systemMessage'] = str(answer['notice'])
    decision, reason = answer.get('decision'), str(answer.get('reason') or '')
    context = answer.get('context')
    if decision == 'ask' and not DIALECTS[event.dialect]['can_ask']:
        if ask_becomes == 'context':
            decision, context = None, '\n'.join(x for x in (context, reason) if x)
        else:
            decision = 'deny'
            reason += '\nThis tool cannot put the question to the person from a hook, so the call is refused: fix what is named above, or let the person run it.'
    if context and len(context) > CONTEXT_LIMIT:
        context = context[:CONTEXT_LIMIT] + '\n[cut here: the rest did not fit]'
    if event.kind == 'before-tool':
        specific = {'hookEventName': event.name}
        if decision:
            specific['permissionDecision'] = decision
            specific['permissionDecisionReason'] = reason
        if context:
            specific['additionalContext'] = context
        if len(specific) > 1:
            out['hookSpecificOutput'] = specific
    else:
        if decision == 'deny' and event.kind == 'prompt':
            out['decision'], out['reason'] = 'block', reason
        if context and event.kind in ('prompt', 'session-start', 'after-tool'):
            out['hookSpecificOutput'] = {'hookEventName': event.name, 'additionalContext': context}
    return out or None


def main(name, handle, argv=None):
    """Run one hook: read the event, answer, and never let a failure of the hook stop the action."""
    argv = sys.argv[1:] if argv is None else argv
    state_dir = fallback_state_dir(name)
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise HookError('the event on stdin is not a JSON object')
        config_path = find_config(name, argv)
        cfg = load_config(config_path)
        if not cfg.get('enabled', True):
            return 0
        kit = Kit(name, cfg, config_path)
        state_dir = kit.state_dir
        event = Event(payload, dialect_of(argv, cfg))
        kit.open_state(event)
        answer = handle(event, kit)
        kit.save_state()
        if answer:
            out = render(event, answer, cfg.get('ask_becomes', 'deny'))
            if out:
                sys.stdout.write(json.dumps(out))
    except Exception as e:  # fail open, and say so
        try:
            write_log(state_dir, 'errors.log', traceback.format_exc().replace('\n', ' | '))
            where = os.path.join(state_dir, 'errors.log')
        except Exception:
            where = 'no log could be written'
        problem = str(e) if isinstance(e, HookError) else f'{type(e).__name__}: {e}'
        sys.stdout.write(json.dumps({'systemMessage': f'Hook {name} could not run and let the action through: {problem} ({where})'}))
    return 0
