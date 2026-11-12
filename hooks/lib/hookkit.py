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
WRAPPERS = {'env', 'command', 'builtin', 'exec', 'nohup', 'time', 'timeout', 'nice', 'ionice', 'stdbuf', 'setsid', 'sudo',
            'doas', 'xargs'}
WRAPPER_OPTIONS_WITH_VALUE = {'-u', '-g', '-n', '-s', '-k', '-I', '-P', '-L', '-d', '-c', '-C', '-p', '-r', '-t', '-D', '-h'}
# words of the shell's own grammar that stand in front of a simple command: `do CMD`, `then CMD`, `! CMD`, `{ CMD; }`
KEYWORDS = {'if', 'then', 'else', 'elif', 'fi', 'do', 'done', 'while', 'until', '!', '{', '}', 'coproc'}
OPERATORS = ('&&', '||', ';;', '|&', '<<<', '<<-', '<<', '&>>', '>>', '<&', '>&', '>|', '&>', '<>', ';', '&', '|', '(', ')',
             '<', '>')  # the longer ones first
REDIRECTIONS = {'<<<', '<<-', '<<', '&>>', '>>', '<&', '>&', '>|', '&>', '<>', '<', '>'}
PIPES = {'|', '|&'}
SHELL_COMMAND_OPTION = re.compile(r'-[A-Za-z]*c[A-Za-z]*')  # -c, -lc, -ec
HEREDOC = re.compile(r'<<-?[ \t]*(?:\'([\w.-]+)\'|"([\w.-]+)"|\\?([\w.-]+))([^\n]*)\n')
ASSIGNMENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')


class Unreadable(Exception):
    """A shell text with a quote or a substitution left open."""


class _Lexer:
    """Reads shell text as far as a guard needs: words with their quotes taken off, operators, comments,
    continuation lines, here-documents and command substitutions. Nothing is expanded and nothing is run.
    `drops` collects the spans of the text that a command only carries (comments, joined line ends, and later the
    here-documents no shell reads)."""

    def __init__(self, text):
        self.text = text
        self.drops = []

    def lex(self, pos, close=None, end=None):
        """The tokens from pos to `end`, or to the `)` or the backtick that closes a substitution; returns them with
        the position after. A token is ('word', value, substitutions), ('op', operator), ('newline',) or
        ['heredoc', body start, body end]."""
        text = self.text
        n = len(text) if end is None else end
        tokens, word, subs, started = [], [], [], False
        pending, depth = [], 0

        def flush():
            nonlocal word, subs, started
            if started:
                tokens.append(('word', ''.join(word), subs))
            word, subs, started = [], [], False

        while pos < n:
            c = text[pos]
            two = text[pos:pos + 2]
            if c == '\\':
                if two == '\\\n':
                    self.drops.append((pos, pos + 2))  # a continuation line: the two lines are one
                else:
                    word.append(text[pos + 1:pos + 2])
                    started = True
                pos += 2
            elif c == "'":
                stop = text.find("'", pos + 1, n)
                if stop < 0:
                    raise Unreadable
                word.append(text[pos + 1:stop])
                started, pos = True, stop + 1
            elif c == '"' or two == '$"':
                started, pos = True, self._double(pos + len(two if c == '$' else c), n, word, subs)
            elif two == "$'":
                started, pos = True, self._ansi(pos + 2, n, word)
            elif text.startswith('$((', pos) or (two == '((' and not started):
                stop = self._balanced(pos + (3 if c == '$' else 2), n, 2, '(', ')')  # arithmetic: no commands inside
                word.append(text[pos:stop])
                started, pos = True, stop
            elif two == '${':
                stop = self._balanced(pos + 2, n, 1, '{', '}')
                word.append(text[pos:stop])
                started, pos = True, stop
            elif two == '$(':
                inner, pos = self.lex(pos + 2, ')', n)
                subs.append(inner)
                word.append('$(...)')
                started = True
            elif c == '`':
                if close == '`':
                    flush()
                    return tokens, pos + 1
                inner, pos = self.lex(pos + 1, '`', n)
                subs.append(inner)
                word.append('`...`')
                started = True
            elif c == '#' and not started:
                stop = text.find('\n', pos, n)
                stop = n if stop < 0 else stop
                self.drops.append((pos, stop))  # a comment, to the end of its line
                pos = stop
            elif c == '\n':
                flush()
                tokens.append(('newline',))
                pos += 1
                for token, word_end, strip_tabs in pending:
                    token[1] = pos
                    while True:
                        stop = text.find('\n', pos, n)
                        stop = n if stop < 0 else stop
                        line = text[pos:stop].lstrip('\t') if strip_tabs else text[pos:stop]
                        if line == word_end or (close == ')' and line.startswith(word_end + ')')):
                            token[2] = pos
                            pos = min(stop + 1, n) if line == word_end else stop - len(line) + len(word_end)
                            break
                        if stop >= n:  # no closing line: the shell takes everything that is left
                            token[2] = pos = n
                            break
                        pos = stop + 1
                pending = []
            elif c in ' \t':
                flush()
                pos += 1
            else:
                op = next((o for o in OPERATORS if text.startswith(o, pos)), None)
                if op is None:
                    word.append(c)
                    started = True
                    pos += 1
                    continue
                flush()
                pos += len(op)
                if op == ')' and close == ')':
                    if depth == 0:
                        return tokens, pos
                    depth -= 1
                elif op == '(':
                    depth += 1
                tokens.append(('op', op))
                if op in ('<<', '<<-'):
                    while pos < n and text[pos] in ' \t':
                        pos += 1
                    stop = pos
                    while stop < n and text[stop] not in ' \t\n;&|()<>':
                        stop += 1
                    word_end = text[pos:stop].replace("'", '').replace('"', '').replace('\\', '')
                    if word_end:
                        token = ['heredoc', None, None]
                        tokens += [('word', word_end, []), token]
                        pending.append((token, word_end, op == '<<-'))
                        pos = stop
        flush()
        if close is not None:
            raise Unreadable
        return tokens, pos

    def _double(self, pos, n, word, subs):
        text = self.text
        while pos < n:
            c = text[pos]
            if c == '"':
                return pos + 1
            if c == '\\' and pos + 1 < n:
                following = text[pos + 1]
                if following == '\n':
                    self.drops.append((pos, pos + 2))
                else:
                    word.append(following if following in '"\\$`' else c + following)
                pos += 2
            elif text.startswith('$((', pos):
                stop = self._balanced(pos + 3, n, 2, '(', ')')
                word.append(text[pos:stop])
                pos = stop
            elif text.startswith('$(', pos):
                inner, pos = self.lex(pos + 2, ')', n)
                subs.append(inner)
                word.append('$(...)')
            elif c == '`':
                inner, pos = self.lex(pos + 1, '`', n)
                subs.append(inner)
                word.append('`...`')
            else:
                word.append(c)
                pos += 1
        raise Unreadable

    def _ansi(self, pos, n, word):
        text = self.text
        while pos < n:
            c = text[pos]
            if c == "'":
                return pos + 1
            if c == '\\' and pos + 1 < n:
                word.append(text[pos + 1])
                pos += 2
            else:
                word.append(c)
                pos += 1
        raise Unreadable

    def _balanced(self, pos, n, depth, opening, closing):
        text = self.text
        while pos < n and depth:
            depth += (text[pos] == opening) - (text[pos] == closing)
            pos += 1
        return pos


def _commands(lexer, tokens, depth):
    """The simple commands of a token list, in order, each as its words: wrappers and the shell's own keywords taken
    off, the text given to `sh -c` read too; after each, the commands of its substitutions, and after each pipeline
    the commands of the here-documents a shell of that pipeline reads. The here-documents no shell reads are added
    to the lexer's drops. None when a text handed to a shell cannot be read."""
    out, pipeline = [], []
    current, subs, heredocs, skip = [], [], [], False

    def end_command():
        nonlocal current, subs, heredocs
        words = _unwrap(current)
        pipeline.append((words, heredocs))
        found = [words] if words else []
        if words:
            name = os.path.basename(words[0])
            inner = None
            if name in SHELLS:
                at = next((i for i, w in enumerate(words[1:], 1) if SHELL_COMMAND_OPTION.fullmatch(w)), None)
                if at is not None and at + 1 < len(words):
                    inner = words[at + 1]
            elif name == 'eval':
                inner = ' '.join(words[1:])
            if inner is not None and depth < 3:
                found = shell_commands(inner, depth + 1)
        for inner_tokens in subs:
            more = _commands(lexer, inner_tokens, depth)
            found = None if found is None or more is None else found + more
        current, subs, heredocs = [], [], []
        return found

    def end_pipeline():
        found = []
        for i, (_, docs) in enumerate(pipeline):
            shell_reads = any(w and os.path.basename(w[0]) in SHELLS for w, _ in pipeline[i:])
            for _, start, stop in docs:
                if start is None:
                    continue
                if shell_reads:
                    more = _commands(lexer, lexer.lex(start, None, stop)[0], depth)
                    found = None if found is None or more is None else found + more
                else:
                    lexer.drops.append((start, stop))
        pipeline.clear()
        return found

    for token in list(tokens) + [('newline',)]:
        kind = token[0]
        if kind == 'word':
            if skip:
                skip = False  # the target of a redirection is a file, not a word of the command
            else:
                current.append(token[1])
                subs += token[2]
            continue
        skip = False
        if kind == 'heredoc':
            heredocs.append(token)
            continue
        if kind == 'op' and token[1] in REDIRECTIONS:
            skip = True
            if current and current[-1].isdigit():
                current.pop()  # the descriptor number of 2>&1
            continue
        found = end_command()
        if found is not None and not (kind == 'op' and token[1] in PIPES):
            more = end_pipeline()
            found = None if more is None else found + more
        if found is None:
            return None
        out += found
    return out


def _read(command):
    lexer = _Lexer(command)
    commands = _commands(lexer, lexer.lex(0)[0], 0)
    return commands, lexer.drops


def _acting_text_by_pattern(command):
    """acting_text for a line that cannot be read as shell: here-documents found by their look alone."""
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


def acting_text(command):
    """The command without the text it only carries: comments, and the body of a here-document unless a shell
    reads it (bash <<EOF, cat <<EOF | sh), so a file being written (cat > file <<EOF, python3 - <<EOF) is not taken
    for a command being run. Lines joined by a backslash are one line."""
    try:
        _, drops = _read(command)
    except Unreadable:
        return _acting_text_by_pattern(command)
    out, pos = [], 0
    for start, stop in sorted(drops):
        if start >= pos:
            out.append(command[pos:start])
            pos = stop
    out.append(command[pos:])
    return ''.join(out)


def shell_commands(command, depth=0):
    """The simple commands a shell line runs, each as its list of words: comments left out, continuation lines
    joined, wrappers such as env or timeout and keywords such as `do` or `then` taken off, and read as commands too:
    the text given to `sh -c`, a command substitution (also inside double quotes) and a here-document a shell reads.
    None when the line cannot be read as shell (the caller then searches the text instead). A guard built on this
    is a guard rail, not a wall: a program can still hide a command where no reader of shell text finds it."""
    try:
        return _read(command)[0]
    except Unreadable:
        return None


def _unwrap(words):
    """Drop leading VAR=value words, the shell's keywords and wrapper programs with their own options."""
    words = list(words)
    while words:
        if ASSIGNMENT.match(words[0]) or words[0] in KEYWORDS:
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


def push_places(rest):
    """The remote and the refs of a `git push`, from the words after "push": its options are left out, and so is
    the value of -o (a push option such as ci.skip)."""
    places, skip = [], False
    for word in rest:
        if skip:
            skip = False
        elif word == '-o':
            skip = True
        elif not word.startswith('-'):
            places.append(word)
    return places


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
        self._state = None
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

    def bind(self, event):
        """Name the state of the session or agent this event belongs to. Nothing is read and no lock is taken until
        the hook's logic touches `state`."""
        os.makedirs(self.state_dir, exist_ok=True)
        key = hashlib.sha1(event.session.encode()).hexdigest()[:16]
        self._state_file = os.path.join(self.state_dir, key + '.json')
        self._prune()

    @property
    def state(self):
        """What this hook remembers for the session or agent: a dictionary, read behind a lock that is held until
        the run ends, so a tool that starts the hook several times at once cannot lose an update. A hook that keeps
        no state never takes the lock, and so never waits for another run of itself."""
        if self._state is None:
            if self._state_file is None:
                raise HookError('the state was asked for before the event was read')
            self._lock = open(self._state_file[:-5] + '.lock', 'w')
            for _ in range(50):  # parallel tool calls run this hook several times at once
                try:
                    fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise HookError(f'state lock not taken after 5 s: {self._state_file}; retry after the other hook finishes')
            try:
                with open(self._state_file, encoding='utf-8') as f:
                    self._state = json.load(f)
            except (OSError, ValueError):
                self._state = {}
        return self._state

    def save_state(self):
        if self._state is not None:
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
        kit.bind(event)
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
