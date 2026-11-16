#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""branch-keeper: few branches, and no work lost.

At session start (and after a compaction): the state of every configured repository, read from its local refs:
branches not inside main with the reason the register records for each, branches inside main that still exist,
local commits that no remote holds, stashes, uncommitted files, and how old the last fetch is.
Before a shell command that removes a place where work lives (rm -r of a clone or a worktree, git worktree remove,
git branch -D, a deletion of a remote branch, git stash drop or clear): refused when it would lose commits that are on
no remote, uncommitted or untracked files, or stashes; a remote branch not inside main goes only when the register
marks it superseded with a reason.
Before a command that makes a branch: the name rule and every branch, local or online, that carries the same number.
Before a merge into main: the branch goes, online and locally; after it, a register row whose branch is now inside
main is cleared.
From the command line: hook.py audit [--fetch] [--config FILE] [REPOSITORY...] prints the whole table.
The hook deletes, pushes and fetches nothing; only `audit --fetch` fetches. README.md beside this file has the
configuration and the reasons.
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
import hookkit  # noqa: E402

NAME = 'branch-keeper'
NAME_PATTERNS = [r'^order[0-9]+[a-z0-9]*(-[a-z0-9][a-z0-9._-]*)?$', r'^wip/', r'^lane/']
NUMBER_PATTERN = r'order([0-9]+)'
REASONED = ('kept', 'superseded')
NETWORK_URL = re.compile(r'^(?:https?|ssh|git|git\+ssh|ssh\+git)://|^[\w.-]+@[\w.-]+:')
# what git would read instead of the folder it is pointed at
DROP_ENV = ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR', 'GIT_OBJECT_DIRECTORY',
            'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_NAMESPACE', 'GIT_PREFIX')
UNRESOLVED = re.compile(r'\$|`')
GH_API_VALUE_FLAGS = {'-X', '--method', '-H', '--header', '-f', '--raw-field', '-F', '--field', '--input', '-q', '--jq',
                      '-t', '--template', '--hostname', '--cache', '-p', '--preview'}
GH_MERGE_VALUE_FLAGS = {'-R', '--repo', '-b', '--body', '-t', '--subject', '-F', '--body-file', '-A', '--author-email',
                        '--match-head-commit'}
GIT_MERGE_VALUE_FLAGS = {'-m', '-s', '--strategy', '-X', '--strategy-option', '-F', '--file', '--into-name', '--cleanup'}
GIT_PUSH_VALUE_FLAGS = {'-o', '--push-option', '--repo', '--receive-pack', '--exec'}


class GitError(Exception):
    """A git command failed or took too long; the message says which and why."""


def run_git(folder, args, timeout=15.0, stdin=None, ok=(0,), network=False):
    """(exit status, stdout) of git in folder. Without network, no transport is allowed and no lazy fetch happens, so
    a partial clone cannot download behind the hook's back; optional locks are off, so git status writes no index."""
    command = ['git', '-c', 'safe.directory=*', '-c', 'core.fsmonitor=false']
    if not network:
        command += ['-c', 'protocol.allow=never']
    command += ['-C', folder, *args]
    env = {k: v for k, v in os.environ.items() if k not in DROP_ENV}
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', LC_ALL='C')
    if not network:
        env['GIT_NO_LAZY_FETCH'] = '1'
    try:
        r = subprocess.run(command, input=stdin, capture_output=True, text=True, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise GitError(f'git {args[0]} took over {timeout:g} s') from None
    except OSError as e:
        raise GitError(f'git cannot start: {e.strerror}') from None
    if r.returncode not in ok:
        lines = (r.stderr or r.stdout).strip().splitlines()
        raise GitError(f'git {args[0]}: {lines[-1] if lines else "exit status " + str(r.returncode)}')
    return r.returncode, r.stdout


def short(ref):
    for prefix in ('refs/heads/', 'refs/remotes/', 'refs/tags/'):
        if ref.startswith(prefix):
            return ref[len(prefix):]
    return ref


def age(seconds):
    if seconds is None:
        return 'never in this clone'
    for unit, size in (('d', 86400), ('h', 3600), ('min', 60)):
        if seconds >= size:
            return f'{seconds / size:.0f} {unit} ago'
    return 'just now'


def cut(items, limit):
    items = list(items)
    if limit and len(items) > limit:
        return items[:limit] + [f'and {len(items) - limit} more']
    return items


def inside(path, top):
    path, top = os.path.normpath(path), os.path.normpath(top)
    return path == top or path.startswith(top.rstrip(os.sep) + os.sep)


def today():
    return time.strftime('%Y-%m-%d', time.gmtime())


class Repo:
    """One repository, read through its local refs: no fetch, no write."""

    def __init__(self, path, spec=None, cfg=None, exact=False):
        spec, cfg = spec or {}, cfg or {}
        self.path = path
        self.remote = spec.get('remote', 'origin')
        self.main_name = spec.get('main')
        self.deletes_merged_head = bool(spec.get('deletes_merged_head', False))
        self.online_rule = cfg.get('online_remotes', 'network')
        self.timeout = float(cfg.get('git_timeout_seconds', 15))
        if not os.path.isdir(path):
            raise GitError('no such folder')
        out = self.git('rev-parse', '--path-format=absolute', '--git-dir', '--git-common-dir', '--is-bare-repository',
                       '--is-shallow-repository').splitlines()
        self.git_dir, self.common_dir = out[0], out[1]
        self.bare, self.shallow = out[2] == 'true', out[3] == 'true'
        self.linked = os.path.realpath(self.git_dir) != os.path.realpath(self.common_dir)
        self.top = self.common_dir if self.bare else self.git('rev-parse', '--show-toplevel').strip()
        if exact and os.path.realpath(self.top) != os.path.realpath(path):
            # an unreadable .git makes git look upwards and answer for an outer repository
            raise GitError(f'git answers for {self.top} here, so this repository itself cannot be read')
        main_tree = os.path.dirname(self.common_dir) if os.path.basename(self.common_dir) == '.git' else self.common_dir
        self.main_tree = main_tree
        self.name = spec.get('name') or os.path.basename(main_tree.rstrip(os.sep))
        if self.bare and self.name.endswith('.git'):
            self.name = self.name[:-4]
        self.urls = {}
        for line in self.git('config', '--get-regexp', r'^remote\..*\.url$', ok=(0, 1)).splitlines():
            key, _, url = line.partition(' ')
            self.urls[key[len('remote.'):-len('.url')]] = url
        self.online = sorted(r for r, u in self.urls.items() if self.online_rule == 'any' or NETWORK_URL.match(u))
        self.refs = {}
        fmt = '%(refname)%00%(objectname)%00%(committerdate:short)%00%(symref)'
        for line in self.git('for-each-ref', f'--format={fmt}', 'refs/heads', 'refs/remotes', 'refs/tags').splitlines():
            ref, sha, date, sym = line.split('\0')
            self.refs[ref] = (sha, date, sym)
        self.head_ref = self.git('symbolic-ref', '-q', 'HEAD', ok=(0, 1)).strip() or None
        self.head_sha = self.git('rev-parse', '-q', '--verify', 'HEAD^{commit}', ok=(0, 1)).strip() or None
        self.main_ref = self._main()

    def git(self, *args, **kw):
        kw.setdefault('timeout', self.timeout)
        return run_git(self.path, args, **kw)[1]

    def status(self, *args, **kw):
        kw.setdefault('timeout', self.timeout)
        kw.setdefault('ok', (0, 1))
        return run_git(self.path, args, **kw)[0]

    def _main(self):
        names = [self.main_name] if self.main_name else []
        if not names:
            sym = self.refs.get(f'refs/remotes/{self.remote}/HEAD', ('', '', ''))[2]
            if sym in self.refs:
                return sym
            names = ['main', 'master']
        for name in names:
            for ref in (f'refs/remotes/{self.remote}/{name}', f'refs/heads/{name}'):
                if ref in self.refs:
                    return ref
        return None

    def need_main(self):
        if not self.main_ref:
            wanted = self.main_name or 'main or master'
            raise GitError(f'no main branch found ({wanted}, on {self.remote} or local): name it with "main" in the configuration')
        return self.main_ref

    @property
    def main_short(self):
        return self.branch_of(self.need_main())

    def main_shas(self):
        """The online main and the local main, as far as they exist."""
        name = self.main_short
        return [self.refs[r][0] for r in (f'refs/remotes/{self.remote}/{name}', f'refs/heads/{name}') if r in self.refs]

    def is_main(self, ref):
        name = self.main_short
        return ref in (f'refs/remotes/{self.remote}/{name}', f'refs/heads/{name}')

    def online_shas(self):
        return {sha for ref, (sha, _, sym) in self.refs.items()
                if not sym and any(ref.startswith(f'refs/remotes/{r}/') for r in self.online)}

    def existing(self, shas):
        """The ones of these commits this repository holds."""
        if not shas:
            return set()
        out = self.git('cat-file', '--batch-check=%(objectname) %(objecttype)', stdin=''.join(s + '\n' for s in sorted(shas)))
        return {line.split()[0] for line in out.splitlines() if line.endswith(' commit')}

    def count_not_in(self, tip, exclude):
        """How many commits of tip none of the commits in exclude reaches."""
        if tip in exclude:
            return 0
        stdin = ''.join(f'^{s}\n' for s in sorted(exclude))
        return int(self.git('rev-list', '--count', tip, '--stdin', stdin=stdin).strip() or 0)

    def is_ancestor(self, sha, of):
        return self.status('merge-base', '--is-ancestor', sha, of) == 0

    def content_in_main(self, sha):
        """True when every commit of sha that main lacks has an equivalent change in main (git cherry shows no + line):
        a branch merged by a squash of one commit, a rebase or a cherry-pick. Its commits differ, its work is in main.
        A branch whose several commits were squashed into one is not recognised this way: it needs its register row."""
        if not self.main_ref:
            return False
        for main in self.main_shas():
            try:
                out = self.git('cherry', main, sha)
            except GitError:
                continue
            marks = [line[:1] for line in out.splitlines() if line]
            if marks and '+' not in marks:
                return True
        return False

    def local_only(self, extra=()):
        """[(branch, tip, commits)] for each local branch with commits no online remote-tracking ref holds; the commits
        in extra (bundled ones) count as held."""
        held = self.online_shas() | set(extra)
        found = []
        for ref, (sha, _, sym) in sorted(self.refs.items()):
            if ref.startswith('refs/heads/') and not sym:
                n = self.count_not_in(sha, held)
                if n:
                    found.append((short(ref), sha, n))
        return found

    def detached_commits(self, extra=()):
        """Commits of a detached HEAD that no branch, tag or online ref holds."""
        if self.head_ref or not self.head_sha:
            return 0
        held = {sha for ref, (sha, _, sym) in self.refs.items() if not sym and not ref.startswith('refs/remotes/')}
        return self.count_not_in(self.head_sha, held | self.online_shas() | set(extra))

    def stashes(self):
        if self.bare:
            return []
        out = self.git('stash', 'list', '--format=%gd%x09%gs')
        return [line.split('\t', 1)[0] + (' (' + line.split('\t', 1)[1] + ')' if '\t' in line else '') for line in out.splitlines() if line]

    def dirty(self):
        """Uncommitted and untracked paths of this work tree; ignored files are not listed (git's own rule)."""
        if self.bare:
            return []
        parts = self.git('status', '--porcelain=v1', '-z', '--untracked-files=normal', '--ignore-submodules=none').split('\0')
        items, i = [], 0
        while i < len(parts):
            entry = parts[i]
            i += 1
            if len(entry) > 3:
                items.append(entry[3:])
                if entry[0] in 'RC':
                    i += 1
        return items

    def worktrees(self):
        out = self.git('worktree', 'list', '--porcelain', '-z')
        items, current = [], {}
        for field in out.split('\0'):
            if not field:
                if current:
                    items.append(current)
                current = {}
                continue
            key, _, value = field.partition(' ')
            current[key] = value or True
        if current:
            items.append(current)
        return items

    def last_fetch(self):
        try:
            return time.time() - os.path.getmtime(os.path.join(self.common_dir, 'FETCH_HEAD'))
        except OSError:
            return None

    def branches_not_in_main(self):
        """{branch: {'refs': [...], 'ahead': N, 'date': D, 'where': text}} for every branch, local or on the remote,
        that main does not contain."""
        main_sha = self.refs[self.need_main()][0]
        fmt = f'%(refname)%00%(objectname)%00%(committerdate:short)%00%(symref)%00%(ahead-behind:{main_sha})'
        found = {}
        out = self.git('for-each-ref', f'--no-merged={main_sha}', f'--format={fmt}', 'refs/heads', f'refs/remotes/{self.remote}')
        for line in out.splitlines():
            ref, _, date, sym, ahead_behind = line.split('\0')
            if sym or self.is_main(ref):
                continue
            branch = self.branch_of(ref)
            row = found.setdefault(branch, {'refs': [], 'ahead': 0, 'date': ''})
            row['refs'].append(ref)
            row['ahead'] = max(row['ahead'], int(ahead_behind.split()[0]))
            row['date'] = max(row['date'], date)
        for branch, row in found.items():
            row['where'] = self.where(branch)
        return found

    def branches_inside_main(self):
        main_sha = self.refs[self.need_main()][0]
        out = self.git('for-each-ref', f'--merged={main_sha}', '--format=%(refname)%00%(symref)', 'refs/heads', f'refs/remotes/{self.remote}')
        found = {}
        for line in out.splitlines():
            ref, sym = line.split('\0')
            if not sym and not self.is_main(ref):
                found.setdefault(self.branch_of(ref), []).append(ref)
        return {b: self.where(b) for b in found}

    def branch_of(self, ref):
        prefix = f'refs/remotes/{self.remote}/'
        return ref[len(prefix):] if ref.startswith(prefix) else short(ref)

    def where(self, branch):
        local = f'refs/heads/{branch}' in self.refs
        online = f'refs/remotes/{self.remote}/{branch}' in self.refs
        return 'local and online' if local and online else 'local' if local else 'online'

    def tips(self, branch):
        return [self.refs[r][0] for r in (f'refs/heads/{branch}', f'refs/remotes/{self.remote}/{branch}') if r in self.refs]

    def remote_for(self, address):
        """The remote this name or address is, or None."""
        if address in self.urls:
            return address
        for remote, url in self.urls.items():
            if url.rstrip('/') == address.rstrip('/'):
                return remote
        return None

    def remote_for_slug(self, owner, name):
        pattern = re.compile(r'[:/]' + re.escape(owner) + '/' + re.escape(name) + r'(?:\.git)?/?$')
        return next((r for r, url in sorted(self.urls.items()) if pattern.search(url)), None)


class Register:
    """The one private file that says why a branch not inside main stays: repository, branch, state (kept or
    superseded), reason, date, separated by tabs; lines starting with # are comments."""

    def __init__(self, path):
        self.path = path
        self.rows = {}
        self.problem = ''
        self.notes = []
        self.missing = False
        self.stamp = None
        published = repository_with_remote(os.path.dirname(path))
        if published:
            self.problem = (f'the register {path} lies inside a repository with a remote ({published}); it is private, so no '
                            'reason was read from it: move it out (the default place is private/branches.tsv of the workspace)')
            return
        try:
            with open(path, encoding='utf-8') as f:
                text = f.read()
            st = os.stat(path)
            self.stamp = (st.st_mtime_ns, st.st_size)
        except FileNotFoundError:
            self.missing = True
            return
        except (OSError, UnicodeDecodeError) as e:
            self.problem = f'the register {path} cannot be read ({getattr(e, "strerror", None) or e}); no reason was read from it'
            return
        for n, line in enumerate(text.splitlines(), 1):
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            fields = [x.strip() for x in line.split('\t')]
            if len(fields) < 3 or not fields[0] or not fields[1]:
                self.notes.append(f'line {n} of {path} is not "repository, branch, state, reason, date" separated by tabs: {line[:80]}')
                continue
            fields += [''] * (5 - len(fields))
            self.rows[(fields[0], fields[1])] = {'state': fields[2], 'reason': fields[3], 'date': fields[4], 'line': line}

    def row(self, repo, branch):
        return self.rows.get((repo, branch))

    def recorded(self, repo, branch):
        row = self.row(repo, branch)
        return bool(row and row['state'] in REASONED and row['reason'])

    def describe(self, repo, branch):
        row = self.row(repo, branch)
        if self.recorded(repo, branch):
            return f"{row['state']}: {row['reason']}"
        if row:
            said = ': '.join(x for x in (row['state'] or 'no state', row['reason']) if x)
            return f'NO REASON RECORDED (the register says "{said}"; only kept or superseded with a reason counts)'
        return 'NO REASON RECORDED'

    def line_for(self, repo, branch, state='superseded', reason='WHY'):
        return f'{repo}\t{branch}\t{state}\t{reason}\t{today()}'

    def clear(self, keys, log):
        """Take the rows of keys out of the file, after writing each whole row to log. Nothing is written when the
        file changed since it was read; returns the rows cleared."""
        keys = [k for k in keys if k in self.rows]
        if not keys or self.problem or self.missing:
            return []
        st = os.stat(self.path)
        if (st.st_mtime_ns, st.st_size) != self.stamp:
            return []
        with open(self.path, encoding='utf-8') as f:
            lines = f.read().splitlines(keepends=True)
        gone = {self.rows[k]['line'] for k in keys}
        for k in keys:
            log(self.rows[k]['line'])
        tmp = f'{self.path}.{os.getpid()}.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            f.writelines(line for line in lines if line.rstrip('\r\n') not in gone)
        os.chmod(tmp, st.st_mode & 0o777)
        os.replace(tmp, self.path)
        for k in keys:
            del self.rows[k]
        return keys


def repository_with_remote(folder):
    """The top of the repository that holds folder when that repository has a remote; '' otherwise."""
    while folder and not os.path.isdir(folder):
        parent = os.path.dirname(folder)
        if parent == folder:
            return ''
        folder = parent
    try:
        top = run_git(folder, ['rev-parse', '--show-toplevel'], timeout=10)[1].strip()
        remotes = run_git(folder, ['remote'], timeout=10)[1].split()
    except GitError:
        return ''
    return top if remotes else ''


def bundle_heads(path):
    """The commits a bundle holds at its tips, read from its header alone."""
    heads = set()
    try:
        with open(path, 'rb') as f:
            if not f.readline(200).startswith((b'# v2 git bundle', b'# v3 git bundle')):
                return heads
            for _ in range(200000):
                line = f.readline(1024)
                if not line or not line.strip():
                    break
                m = re.match(rb'([0-9a-f]{40}|[0-9a-f]{64}) ', line)
                if m:
                    heads.add(m.group(1).decode())
    except OSError:
        pass
    return heads


class Context:
    """What the checks share in one run: the configuration, the register and the bundled commits, read once."""

    def __init__(self, kit):
        self.kit = kit
        self.cfg = kit.cfg
        self._register = None
        self._bundled = None

    @property
    def register(self):
        if self._register is None:
            self._register = Register(self.kit.path('register'))
        return self._register

    def bundled(self):
        if self._bundled is None:
            folders = self.cfg.get('bundle_folders')
            folders = [self.kit.resolve(f) for f in folders] if folders is not None else [self.kit.path('queue')]
            depth, limit, heads, seen = int(self.cfg.get('bundle_depth', 3)), 20000, set(), 0
            for top in folders:
                base = top.rstrip(os.sep).count(os.sep)
                for root, dirs, files in os.walk(top):
                    seen += 1
                    if seen > limit:
                        break
                    for name in files:
                        if name.endswith('.bundle'):
                            heads |= bundle_heads(os.path.join(root, name))
                    if root.count(os.sep) - base >= depth:
                        dirs[:] = []
                    else:
                        dirs[:] = [d for d in dirs if d != '.git' and not os.path.islink(os.path.join(root, d))]
            self._bundled = heads
        return self._bundled

    def repo(self, path, exact=False):
        """A repository at path, with the settings of the configured one it is, if any; with exact, path must be the
        repository's own top folder."""
        spec = self.spec_for(path)
        return Repo(path, spec, self.cfg, exact)

    def specs(self):
        out = []
        for entry in self.cfg.get('repositories') or []:
            spec = dict(entry) if isinstance(entry, dict) else {'path': entry}
            spec['path'] = self.kit.resolve(spec['path'])
            out.append(spec)
        return out

    def spec_for(self, path):
        real = os.path.realpath(path)
        for spec in self.specs():
            if os.path.realpath(spec['path']) == real:
                return spec
        try:
            common = os.path.realpath(run_git(path, ['rev-parse', '--path-format=absolute', '--git-common-dir'], timeout=10)[1].strip())
        except GitError:
            return {}
        for spec in self.specs():
            try:
                other = run_git(spec['path'], ['rev-parse', '--path-format=absolute', '--git-common-dir'], timeout=10)[1].strip()
            except GitError:
                continue
            if os.path.realpath(other) == common:
                return spec
        return {}

    def held_by_bundles(self, repo):
        return repo.existing(self.bundled()) if self.bundled() else set()


# ---------------------------------------------------------------- the state at session start, and the audit

def read_state(repo, register, ctx):
    """Everything the session start and the audit say about one repository."""
    state = {'repo': repo, 'not_in_main': repo.branches_not_in_main(), 'inside_main': repo.branches_inside_main(),
             'local_only': repo.local_only(), 'detached': repo.detached_commits(), 'stashes': repo.stashes(),
             'last_fetch': repo.last_fetch(), 'dirty': None, 'dirty_problem': ''}
    try:
        state['dirty'] = repo.dirty()
    except GitError as e:
        state['dirty_problem'] = str(e)
    state['by_content'] = sorted(b for b, row in state['not_in_main'].items()
                                 if all(repo.content_in_main(repo.refs[r][0]) for r in row['refs']))
    state['no_reason'] = sorted(b for b in state['not_in_main']
                                if b not in state['by_content'] and not register.recorded(repo.name, b))
    return state


def settle(repo, register, ctx, out):
    """Clear the register rows of this repository whose branch is now inside main, or that marked a superseded branch
    that exists nowhere any more; a row whose branch is gone otherwise is said, never cleared. Lines go to out; returns
    how many rows have no branch any more and were not cleared."""
    if register.problem or register.missing:
        return 0
    mains = repo.main_shas() if repo.main_ref else []
    clear, gone_kept, gone_open = [], [], []
    for (name, branch), row in list(register.rows.items()):
        if name != repo.name:
            continue
        tips = repo.tips(branch)
        if not tips:
            said = f'{branch} ({row["state"] or "no state"}: {row["reason"] or "no reason"})'
            if row['state'] == 'superseded':
                clear.append(((name, branch), 'deleted'))
            elif row['state'] == 'kept':
                gone_kept.append(said)
            else:
                gone_open.append(said)
            continue
        if mains and all(any(repo.is_ancestor(t, m) for m in mains) for t in tips):
            clear.append(((name, branch), 'merged into main'))
    if clear and ctx.kit.on('clear_settled_rows'):
        done = register.clear([k for k, _ in clear], lambda line: ctx.kit.log('cleared.log', line.replace('\t', ' | ')))
        why = dict(clear)
        if done:
            out.append(f'{repo.name}: register rows cleared ({register.path}; whole rows in cleared.log): '
                       + '; '.join(f'{b} ({why[(n, b)]})' for n, b in done))
        else:
            out.append(f'{repo.name}: register rows not cleared this time, because {register.path} changed while it was read: '
                       + '; '.join(b for (_, b), _ in clear) + '. They are cleared at the next session start or audit.')
    if gone_kept:
        out.append(f'{repo.name}: KEPT WORK GONE: the register keeps these, and no local or remote-tracking branch of that name '
                   'exists here: ' + '; '.join(gone_kept) + '. Find where the work went before anything else.')
    if gone_open:
        out.append(f'{repo.name}: ROWS WITHOUT THEIR BRANCH: the register has these rows, not decided, and no local or '
                   f'remote-tracking branch of that name exists here (last fetch {age(repo.last_fetch())}): ' + '; '.join(gone_open)
                   + '. Find where the work went (a deletion since, another clone), then mark each row superseded with the '
                   'reason, or kept with the place the work now has.')
    return len(gone_kept) + len(gone_open)


def describe_state(state, register, limit):
    repo = state['repo']
    nim, inside_main, local, stashes = state['not_in_main'], state['inside_main'], state['local_only'], state['stashes']
    dirty = state['dirty']
    counts = [f'{len(nim)} branch(es) not in main ({len(state["no_reason"])} with no reason recorded)',
              f'{len(inside_main)} inside main still there',
              f'{len(local)} local branch(es) with commits on no remote',
              f'{len(stashes)} stash(es)',
              (f'{len(dirty)} uncommitted or untracked' if dirty is not None else f'uncommitted files not counted ({state["dirty_problem"]})')]
    if state['detached']:
        counts.append(f'a detached HEAD with {state["detached"]} commit(s) in no branch')
    head = (f'{repo.name} ({short(repo.need_main())} is main): ' + ', '.join(counts)
            + f'; last fetch {age(state["last_fetch"])}' + ('; shallow clone' if repo.shallow else '') + '.')
    lines = [head]
    by_content = state.get('by_content', [])
    if by_content:
        lines.append(f'  In main by content, {len(by_content)} (git cherry shows no + line; they can go): ' + '; '.join(cut(by_content, limit)))
    order = sorted((b for b in nim if b not in by_content), key=lambda b: (register.recorded(repo.name, b), b))
    if order:
        lines.append('  Not in main: ' + '; '.join(cut(
            (f'{b} ({nim[b]["where"]}, {nim[b]["ahead"]} commit(s) main lacks, last {nim[b]["date"]}): {register.describe(repo.name, b)}'
             for b in order), limit)))
    if inside_main:
        lines.append('  Inside main, still there (they can go): ' + '; '.join(cut((f'{b} ({w})' for b, w in sorted(inside_main.items())), limit)))
    if local:
        lines.append('  Commits on no remote: ' + '; '.join(cut((f'{b} ({n})' for b, _, n in local), limit)))
    if stashes:
        lines.append('  Stashes: ' + '; '.join(cut(stashes, limit)))
    if dirty:
        lines.append('  Uncommitted or untracked: ' + ', '.join(cut(dirty, limit)))
    return lines


def state_text(ctx):
    register = ctx.register
    limit = int(ctx.cfg.get('max_names', 10))
    lines = ['Branches and work on no remote, read from the local refs (branch-keeper; no network: each repository says how old '
             'its last fetch is).']
    if register.problem:
        lines.append('REGISTER NOT READ: ' + register.problem + '.')
    elif register.missing:
        lines.append(f'No register yet at {register.path}: every branch not in main counts as having no reason.')
    lines += register.notes
    specs = ctx.specs()
    if not specs:
        lines.append(f'No repository is configured: list them under "repositories" in {ctx.kit.config_path}.')
    for spec in specs:
        label = spec.get('name') or os.path.basename(spec['path'].rstrip(os.sep))
        try:
            repo = Repo(spec['path'], spec, ctx.cfg)
            settled = []
            settle(repo, register, ctx, settled)
            state = read_state(repo, register, ctx)
        except GitError as e:
            lines.append(f'{label} ({spec["path"]}): NOT READ: {e}. Nothing about its branches is known until it can be read.')
            continue
        lines += settled + describe_state(state, register, limit)
    lines.append(f'Rule: one branch per piece of work, named by its number, pushed the same day, gone at the merge; every branch '
                 f'not in main is merged, or has a row in {register.path} (repository, branch, kept or superseded, reason, date; '
                 f'tab-separated). The whole table: python3 {os.path.join(HERE, "hook.py")} audit --config {ctx.kit.config_path}')
    return '\n'.join(lines)


# ---------------------------------------------------------------- reading the commands

def options_and_words(rest, value_flags=()):
    """(options, positional words) of a command's arguments; an option in value_flags takes the next word."""
    options, words, skip, ended = [], [], False, False
    for word in rest:
        if skip:
            skip = False
            continue
        if not ended and word == '--':
            ended = True
        elif not ended and word.startswith('-') and len(word) > 1:
            options.append(word)
            skip = word in value_flags
        else:
            words.append(word)
    return options, words


def choice(cfg, key):
    """One of context, ask or deny, from the configuration; anything else is said, never guessed."""
    value = cfg.get(key, 'context')
    if value not in ('context', 'ask', 'deny'):
        raise hookkit.HookError(f'"{key}" must be context, ask or deny, not {value!r}')
    return value


class Findings:
    def __init__(self):
        self.deny, self.ask, self.context = [], [], []

    def add(self, kind, text):
        if text:
            {'deny': self.deny, 'ask': self.ask, 'context': self.context}[kind].append(text)


def repo_or_finding(ctx, folder, findings, kind, what):
    try:
        return ctx.repo(folder)
    except GitError as e:
        findings.add(kind, f'{what}: the repository at {folder} could not be read ({e}), so it was not checked. '
                           'Nothing is passed unchecked: make it readable, or the person runs the command.')
        return None


def lost_by_removal(path, top, ctx):
    """(lines, unreadable) for one repository found at path inside the folder top being removed."""
    database = os.path.basename(path) == '.git' and os.path.isdir(path)
    target = os.path.dirname(path) if database else path
    try:
        repo = ctx.repo(target, exact=True)
    except GitError as e:
        return [f'{path}: could not be read ({e})'], True
    kind = ('the repository database of ' + repo.top if database else 'bare repository' if repo.bare
            else f'worktree of {repo.main_tree}' if repo.linked else 'clone')
    parts = []
    try:
        bundled = ctx.held_by_bundles(repo)
        if not repo.linked:
            local = repo.local_only(bundled)
            if local:
                parts.append('; '.join(cut((f'branch {b}: {n} commit(s) on no remote' for b, _, n in local), 5)))
            stashes = repo.stashes()
            if stashes:
                parts.append(f'{len(stashes)} stash(es): ' + ', '.join(cut(stashes, 3)))
            for wt in repo.worktrees()[1:]:
                where = wt.get('worktree', '')
                if wt.get('prunable') or not where:
                    continue
                if database or not inside(where, top):
                    parts.append(f'its linked worktree {where} would be left without its repository')
                    continue
                if repo.bare or not inside(where, repo.top):
                    continue  # the search of the folder finds it and checks it on its own
                try:
                    dirty = Repo(where, None, ctx.cfg).dirty()
                except GitError as e:
                    return [f'{where} (worktree of {repo.top}): could not be read ({e})'], True
                if dirty:
                    parts.append(f'its worktree {where}: {len(dirty)} uncommitted or untracked: ' + ', '.join(cut(dirty, 5)))
        detached = repo.detached_commits(bundled)
        if detached:
            parts.append(f'a detached HEAD with {detached} commit(s) in no branch')
        if not database:
            dirty = repo.dirty()
            if dirty:
                parts.append(f'{len(dirty)} uncommitted or untracked: ' + ', '.join(cut(dirty, 5)))
    except GitError as e:
        return [f'{path} ({kind}): could not be read ({e})'], True
    return ([f'{path} ({kind}): ' + '; '.join(parts)] if parts else []), False


def is_git_dir(path):
    return (os.path.isfile(os.path.join(path, 'HEAD')) and os.path.isdir(os.path.join(path, 'objects'))
            and os.path.isdir(os.path.join(path, 'refs')))


def repositories_under(top, ctx):
    """(repository folders at or under top, cut short?) found without following a symbolic link; a repository's
    own folder is not searched further."""
    limit = int(ctx.cfg.get('scan_limit', 100000))
    deadline = time.monotonic() + float(ctx.cfg.get('scan_seconds', 10))
    max_depth = int(ctx.cfg.get('scan_depth', 12))
    if is_git_dir(top):
        return [top], False
    found, seen = [], 0
    base = top.rstrip(os.sep).count(os.sep)
    for root, dirs, files in os.walk(top):
        seen += 1
        if seen > limit or time.monotonic() > deadline:
            return found, True
        if '.git' in dirs or '.git' in files:
            found.append(root)
            dirs[:] = []
            continue
        if root != top and is_git_dir(root):
            found.append(root)
            dirs[:] = []
            continue
        if root.count(os.sep) - base >= max_depth:
            if dirs:
                return found, True
            continue
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
    return found, False


WHAT_TO_DO = ('What to do: push each branch to our fork (git -C CLONE push -u fork BRANCH), or bundle it into the lane folder '
              '(git -C CLONE bundle create LANE/NAME.bundle BRANCH; a bundle under {bundles} counts as kept); commit '
              'uncommitted files on a branch first (skill forks-and-online, "Uncommitted work"), turn a stash into a branch '
              '(git stash branch NAME stash@{{0}}) and push or bundle it, and remove a linked worktree before its clone. '
              'Then send the same command again: a place whose work is all online or bundled passes.')


def what_to_do(ctx):
    folders = ctx.cfg.get('bundle_folders')
    shown = ', '.join(folders) if folders else ctx.kit.path('queue')
    return WHAT_TO_DO.format(bundles=shown)


def check_rm(words, folder, ctx, findings, original):
    options, targets = options_and_words(words[1:])
    recursive = any(o == '--recursive' or (not o.startswith('--') and ('r' in o or 'R' in o)) for o in options)
    if not recursive or not ctx.kit.on('removal'):
        return
    places, lost, unreadable = [], [], []
    for word in targets:
        if UNRESOLVED.search(word):
            findings.add(choice(ctx.cfg, 'on_unresolved_path'),
                         f'branch-keeper could not see what "{word}" in `{original}` names, so it did not look inside it: if it '
                         'is or holds a clone or a worktree, check it first (hook.py audit PATH) or name the folder plainly.')
            continue
        path = os.path.expanduser(word)
        path = path if os.path.isabs(path) else os.path.join(folder, path)
        matches = sorted(glob.glob(path)) if any(c in word for c in '*?[') else [path]
        for match in matches:
            bare = match.rstrip(os.sep) or os.sep
            if os.path.islink(bare):
                if not match.endswith(os.sep):
                    continue  # only the link goes
                bare = os.path.realpath(bare)  # rm -r LINK/ empties the link's target
            if os.path.isdir(bare):
                places.append(os.path.normpath(bare))
    for top in places:
        repos, short_cut = repositories_under(top, ctx)
        if short_cut:
            findings.add('deny', f'Refused: branch-keeper could not look inside all of {top} within its limits (scan_limit '
                                 f'{ctx.cfg.get("scan_limit", 100000)} folders, scan_seconds {ctx.cfg.get("scan_seconds", 10)}, '
                                 f'scan_depth {ctx.cfg.get("scan_depth", 12)}), so it cannot say that no work is lost. Remove it in '
                                 f'parts, check it with hook.py audit, or raise the limits in {ctx.kit.config_path}.')
        for repo_path in repos:
            lines, bad = lost_by_removal(repo_path, top, ctx)
            (unreadable if bad else lost).extend(lines)
    if lost or unreadable:
        text = f'Refused: `{original}` would remove work that exists nowhere else, or that could not be read:\n'
        text += '\n'.join('- ' + line for line in lost + unreadable)
        if unreadable:
            text += '\nA repository that cannot be read is not removed by a command the hook cannot check: make it readable, or the person removes it.'
        findings.add('deny', text + '\n' + what_to_do(ctx))


def check_worktree_remove(rest, folder, ctx, findings, original):
    _, words = options_and_words(rest)
    if not words or not ctx.kit.on('removal'):
        return
    path = os.path.expanduser(words[0])
    path = os.path.normpath(path if os.path.isabs(path) else os.path.join(folder, path))
    if not os.path.isdir(path):
        return
    try:
        repo = ctx.repo(path)
        bundled = ctx.held_by_bundles(repo)
        dirty, detached = repo.dirty(), repo.detached_commits(bundled)
        local = [x for x in repo.local_only(bundled) if repo.head_ref and x[0] == short(repo.head_ref)]
    except GitError as e:
        findings.add('deny', f'Refused: the worktree {path} could not be read ({e}), so `{original}` was not checked. '
                             'Make it readable, or the person runs the command.')
        return
    parts = []
    if dirty:
        parts.append(f'{len(dirty)} uncommitted or untracked: ' + ', '.join(cut(dirty, 5)))
    if detached:
        parts.append(f'a detached HEAD with {detached} commit(s) in no branch')
    if parts:
        findings.add('deny', f'Refused: `{original}` would remove work that exists nowhere else:\n- {path} (worktree): '
                             + '; '.join(parts) + '\n' + what_to_do(ctx))
    elif local:
        findings.add('context', f'The worktree {path} goes; its branch {local[0][0]} stays in {repo.main_tree} with '
                                f'{local[0][2]} commit(s) on no remote: push it to our fork or bundle it before the clone goes.')


def check_branch(rest, folder, ctx, findings, original):
    options, words = options_and_words(rest, {'-u', '--set-upstream-to', '--contains', '--no-contains', '--merged',
                                              '--no-merged', '--points-at', '--sort', '--format', '--column'})
    flags = ''.join(o[1:] for o in options if not o.startswith('--'))
    longs = set(o.split('=', 1)[0] for o in options if o.startswith('--'))
    delete = 'd' in flags or 'D' in flags or '--delete' in longs
    force = 'D' in flags or 'f' in flags or '--force' in longs
    if delete:
        if force and 'r' not in flags and '--remotes' not in longs and ctx.kit.on('removal'):
            repo = repo_or_finding(ctx, folder, findings, 'deny', f'Refused: `{original}`')
            if repo:
                for name in words:
                    check_local_deletion(repo, name, ctx, findings)
        return
    listing = set('lamMcCvra') & set(flags) or longs & {'--list', '--all', '--move', '--copy', '--verbose', '--remotes',
                                                         '--show-current', '--edit-description', '--unset-upstream',
                                                         '--contains', '--no-contains', '--merged', '--no-merged',
                                                         '--points-at', '--set-upstream-to', '--format', '--sort'}
    if words and not listing and '-u' not in options:
        creation(words[0], folder, ctx, findings)


def check_local_deletion(repo, name, ctx, findings):
    ref = f'refs/heads/{name}'
    if ref not in repo.refs:
        return
    sha = repo.refs[ref][0]
    bundled = ctx.held_by_bundles(repo)
    on_no_remote = repo.count_not_in(sha, repo.online_shas() | bundled)
    if not on_no_remote:
        return
    others = {s for r, (s, _, sym) in repo.refs.items() if r != ref and not sym and not r.startswith('refs/remotes/')}
    lost = repo.count_not_in(sha, repo.online_shas() | bundled | others)
    if lost and repo.content_in_main(sha):
        findings.add('context', f'{repo.name}: deleting {name} loses no work: each commit it has outside main is in main by content '
                                '(git cherry shows no + line).')
        return
    if not lost:
        holders = [short(r) for r, (s, _, _) in repo.refs.items() if r != ref and r.startswith(('refs/heads/', 'refs/tags/'))
                   and repo.is_ancestor(sha, s)]
        findings.add('context', f'{repo.name}: deleting {name} loses no commit: {", ".join(cut(holders, 3)) or "another local ref"} '
                                f'still holds its {on_no_remote} commit(s), which are on no remote.')
        return
    register = ctx.register
    if register.problem:
        findings.add('deny', f'Refused: {name} has {lost} commit(s) on no remote and the register cannot be read: {register.problem}.')
        return
    row = register.row(repo.name, name)
    if row and row['state'] == 'superseded' and row['reason']:
        findings.add('context', f'{repo.name}: {name} goes with {lost} commit(s) on no remote; the register marks it superseded: {row["reason"]}.')
        return
    findings.add('deny', f'Refused: deleting the branch {name} of {repo.name} loses {lost} commit(s) that are on no remote, '
                         f'in no bundle and in no other branch ({register.describe(repo.name, name)}). Push it to our fork '
                         f'(git -C {repo.top} push -u fork {name}) or bundle it into the lane folder; if the work is superseded '
                         f'(a squash merge, a later branch), add this line to {register.path}: "'
                         f'{register.line_for(repo.name, name, "superseded", "WHY, with the commit or branch that replaces it")}" '
                         'and send the same command again.')


def check_remote_deletion(repo, remote, branch, ctx, findings, how):
    if not ctx.kit.on('remote_deletion'):
        return
    branch = branch[len('refs/heads/'):] if branch.startswith('refs/heads/') else branch
    ref = f'refs/remotes/{remote}/{branch}'
    if ref not in repo.refs:
        findings.add('deny', f'Refused: {how} deletes {remote}/{branch} of {repo.name}, which is not among the local '
                             f'remote-tracking refs (last fetch {age(repo.last_fetch())}), so it cannot be told whether it '
                             f'is inside main. Fetch first (git -C {repo.top} fetch {remote}), then send the same command again.')
        return
    try:
        main = repo.need_main()
    except GitError as e:
        findings.add('deny', f'Refused: {how}: {repo.name}: {e}.')
        return
    sha = repo.refs[ref][0]
    if repo.is_ancestor(sha, repo.refs[main][0]):
        return
    register = ctx.register
    ahead = repo.count_not_in(sha, {repo.refs[main][0]})
    if register.problem:
        findings.add('deny', f'Refused: {remote}/{branch} is not inside main and the register cannot be read: {register.problem}.')
        return
    row = register.row(repo.name, branch)
    if row and row['state'] == 'superseded' and row['reason']:
        findings.add('context', f'{repo.name}: {remote}/{branch} is not inside {short(main)} ({ahead} commit(s) it lacks); '
                                f'the register marks it superseded: {row["reason"]}.')
        return
    if row and row['state'] == 'kept' and row['reason']:
        findings.add('deny', f'Refused: {how} deletes {remote}/{branch} of {repo.name}, which the register keeps: '
                             f'{row["reason"]}. Change that row to superseded, with the reason, if the work is no longer needed.')
        return
    findings.add('deny', f'Refused: {how} deletes {remote}/{branch} of {repo.name}, which is not inside {short(main)} '
                         f'({ahead} commit(s) main lacks, last {repo.refs[ref][1]}) and has no superseded row in the register '
                         f'({register.describe(repo.name, branch)}). Merge it first, or, when its work is superseded, add this '
                         f'line to {register.path}: "{register.line_for(repo.name, branch)}" (the reason names what replaces it), '
                         'then send the same command again.')


def check_push(rest, folder, ctx, findings, original):
    options, words = options_and_words(rest, GIT_PUSH_VALUE_FLAGS)
    flags = ''.join(o[1:] for o in options if not o.startswith('--'))
    longs = set(o.split('=', 1)[0] for o in options if o.startswith('--'))
    delete = 'd' in flags or '--delete' in longs
    mirror = '--mirror' in longs or '--prune' in longs
    deleting = delete or mirror or any(w.lstrip('+').startswith(':') for w in words[1:])
    if not deleting and not ctx.kit.on('branch_creation'):
        return
    repo = repo_or_finding(ctx, folder, findings, 'deny' if deleting else 'context', f'`{original}`')
    if not repo:
        return
    address = words[0] if words else repo.remote
    remote = repo.remote_for(address)
    if remote is None:
        if deleting:
            findings.add('deny', f'Refused: `{original}`: "{address}" is no remote of {repo.name} ({", ".join(sorted(repo.urls)) or "none"}), '
                                 'so the branches it deletes cannot be checked. Name the remote instead of its address.')
        return
    specs = words[1:]
    if delete:
        for spec in specs:
            check_remote_deletion(repo, remote, spec, ctx, findings, f'`{original}`')
        return
    if mirror:
        local = {short(r) for r in repo.refs if r.startswith('refs/heads/')}
        for ref in sorted(repo.refs):
            branch = repo.branch_of(ref)
            if ref.startswith(f'refs/remotes/{remote}/') and not repo.refs[ref][2] and branch not in local and branch != 'HEAD':
                check_remote_deletion(repo, remote, branch, ctx, findings, f'`{original}` (no local branch of that name)')
    for spec in specs:
        spec = spec.lstrip('+')
        if spec.startswith(':'):
            check_remote_deletion(repo, remote, spec[1:], ctx, findings, f'`{original}`')
            continue
        src, _, dst = spec.partition(':')
        name = dst or src
        if name == 'HEAD':
            name = short(repo.head_ref) if repo.head_ref else ''
        name = name[len('refs/heads/'):] if name.startswith('refs/heads/') else name
        if name and not name.startswith('refs/') and f'refs/remotes/{remote}/{name}' not in repo.refs:
            creation(name, folder, ctx, findings, first_push=True)
    if not specs and repo.head_ref and ('u' in flags or '--set-upstream' in longs):
        name = short(repo.head_ref)
        if f'refs/remotes/{remote}/{name}' not in repo.refs:
            creation(name, folder, ctx, findings, first_push=True)


def check_stash(rest, folder, ctx, findings, original):
    if not rest or rest[0] not in ('drop', 'clear') or not ctx.kit.on('stash'):
        return
    repo = repo_or_finding(ctx, folder, findings, 'deny', f'Refused: `{original}`')
    if not repo:
        return
    try:
        stashes = repo.stashes()
    except GitError as e:
        findings.add('deny', f'Refused: the stashes of {repo.top} could not be read ({e}), so `{original}` was not checked.')
        return
    if not stashes:
        return
    if rest[0] == 'drop':
        _, words = options_and_words(rest[1:])
        want = words[0] if words else 'stash@{0}'
        want = f'stash@{{{want}}}' if want.isdigit() else want.replace('refs/stash@{', 'stash@{')
        stashes = [s for s in stashes if s.split(' ', 1)[0] == want]
        if not stashes:
            return  # no such stash: git says so itself
    findings.add('deny', f'Refused: `{original}` drops work that exists only in this clone ({repo.top}): '
                         + ', '.join(cut(stashes, 5)) + '. Keep it instead: git stash branch NAME STASH makes it a branch '
                         '(and takes it off the stash list), then push it to our fork or bundle it; a stash that is truly not '
                         'needed is dropped by the person.')


def creation(name, folder, ctx, findings, first_push=False):
    if not ctx.kit.on('branch_creation'):
        return
    patterns = ctx.cfg.get('name_patterns', NAME_PATTERNS)
    m = re.search(ctx.cfg.get('number_pattern', NUMBER_PATTERN), name)
    lines = [f'{"First push of the new branch" if first_push else "New branch"} {name}. The rule: one branch per piece of work, '
             'named by its number first (order612-branch-keeper), pushed to our fork the same day, gone at the merge.']
    fits = any(re.search(p, name) for p in patterns)
    if m:
        number = m.group(1)
        same, unread = [], []
        seen_paths, paths = set(), [spec['path'] for spec in ctx.specs()] + [folder]
        for path in paths:
            try:
                repo = ctx.repo(path)
            except GitError as e:
                if path != folder:
                    unread.append(f'{os.path.basename(path.rstrip(os.sep))} ({e})')
                continue
            key = os.path.realpath(repo.common_dir)
            if key in seen_paths:
                continue
            seen_paths.add(key)
            found = {}
            for ref, (sha, date, sym) in repo.refs.items():
                branch = short(ref) if ref.startswith('refs/heads/') else repo.branch_of(ref)
                if sym or not ref.startswith(('refs/heads/', f'refs/remotes/{repo.remote}/')):
                    continue
                if re.search(r'(?<![0-9])' + re.escape(number) + r'(?![0-9])', branch) and not (branch == name and first_push):
                    found.setdefault(branch, (date, repo.where(branch)))
            for branch, (date, where) in sorted(found.items()):
                same.append(f'{repo.name}: {branch} ({where}, last {date})')
        if same:
            lines.append(f'Branches that already carry {number}: ' + '; '.join(cut(same, 12))
                         + '. Build on them instead of starting over, or say in the report why they do not apply.')
        else:
            lines.append(f'No branch, local or online, carries {number} in the repositories read (as of each one\'s last fetch).')
        if unread:
            lines.append('Not read: ' + '; '.join(unread) + '.')
    else:
        lines.append('This name carries no work number, so no existing work could be looked for.')
    if fits:
        findings.add('context', ' '.join(lines))
    else:
        lines.insert(1, f'The name {name} does not follow the rule here ({" or ".join(patterns)}).')
        kind = choice(ctx.cfg, 'name_rule_outside')
        findings.add(kind, ('Refused: ' if kind == 'deny' else '') + ' '.join(lines))


def merge_reminder(repo, branch, ctx, findings, squash=False, deletes=False, label=None):
    if not ctx.kit.on('merge_reminder'):
        return
    register = ctx.register
    label = label or branch
    online = ('the repository deletes a merged pull request\'s branch by itself' if repo.deletes_merged_head
              else '--delete-branch deletes it' if deletes
              else f'git -C {repo.top} push {repo.remote} --delete {branch or "BRANCH"} (it passes once the branch is inside main)')
    text = (f'After this merge, {label} goes, online and locally: work not in main is merged, superseded with its reason, '
            f'or kept with its reason. Online: {online}. Locally: git branch -d {branch or "BRANCH"} in every clone that has it, '
            'after a fetch with --prune.')
    if squash:
        text += (f' A squash or rebase merge leaves the branch outside main by ancestry: before deleting it, add '
                 f'"{register.line_for(repo.name, branch or "BRANCH", "superseded", "squash-merged as COMMIT")}" to {register.path}.')
    row = register.row(repo.name, branch) if branch else None
    if row:
        text += f' Its register row ({row["state"]}: {row["reason"]}) is cleared once the merge shows in main.'
    findings.add('context', text)


def check_merge(rest, folder, ctx, findings, original):
    options, words = options_and_words(rest, GIT_MERGE_VALUE_FLAGS)
    if any(o in ('--abort', '--continue', '--quit', '--skip') for o in options) or not words:
        return
    try:
        repo = ctx.repo(folder)
        main = repo.need_main()
    except GitError:
        return
    if repo.head_ref != f'refs/heads/{repo.main_short}':
        return
    for word in words:
        branch = repo.branch_of(f'refs/remotes/{word}') if f'refs/remotes/{word}' in repo.refs else word
        if branch != repo.main_short and short(main) != word:
            merge_reminder(repo, branch, ctx, findings, squash='--squash' in options)


def repo_for_slug(ctx, folder, slug):
    """The repository and remote that OWNER/NAME is: the working folder's own when no slug is given (as gh does),
    else the first of the working folder and the configured repositories with such a remote."""
    owner, _, name = slug.partition('/')
    for path in [folder] + ([spec['path'] for spec in ctx.specs()] if slug else []):
        try:
            repo = ctx.repo(path)
        except GitError:
            continue
        remote = repo.remote_for_slug(owner, name) if slug else repo.remote
        if remote:
            return repo, remote
    return None, None


def check_gh(words, folder, ctx, findings, original):
    if words[1:3] == ['pr', 'merge']:
        options, rest = options_and_words(words[3:], GH_MERGE_VALUE_FLAGS)
        slug = next((words[i + 1] for i, w in enumerate(words[:-1]) if w in ('-R', '--repo')), '')
        slug = slug or next((o.split('=', 1)[1] for o in options if o.startswith('--repo=')), '')
        repo, _ = repo_for_slug(ctx, folder, slug)
        if repo is None:
            findings.add('context', f'After this merge, the branch goes, online and locally (branch-keeper could not find the '
                                    f'repository {slug or "of " + folder} here to say more).')
            return
        selector = rest[0] if rest else ''
        branch = '' if re.fullmatch(r'#?[0-9]+|https?://\S+', selector) else selector
        if not selector and repo.head_ref:
            branch = short(repo.head_ref)
        label = branch or f'the branch of pull request {selector}'
        flags = ''.join(o[1:] for o in options if not o.startswith('--'))
        squash = 's' in flags or 'r' in flags or '--squash' in options or '--rebase' in options
        deletes = 'd' in flags or '--delete-branch' in options
        merge_reminder(repo, branch, ctx, findings, squash=squash, deletes=deletes, label=label)
        return
    if words[1:2] == ['api']:
        options, rest = options_and_words(words[2:], GH_API_VALUE_FLAGS)
        method = ''
        for i, w in enumerate(words):
            if w in ('-X', '--method') and i + 1 < len(words):
                method = words[i + 1]
            elif w.startswith('--method='):
                method = w.split('=', 1)[1]
        m = re.match(r'^/?repos/([^/]+)/([^/]+)/git/refs/heads/(.+)$', rest[0]) if rest else None
        if method.upper() != 'DELETE' or not m:
            return
        owner, name, branch = m.groups()
        slug = '' if owner in ('{owner}', ':owner') else f'{owner}/{name}'
        repo, remote = repo_for_slug(ctx, folder, slug)
        if repo is None or remote is None:
            findings.add('deny', f'Refused: `{original}` deletes the branch {branch} of {owner}/{name}, and no repository here has '
                                 'that remote, so the deletion cannot be checked against main and the register. Run it from a '
                                 'clone of that repository, after a fetch.')
            return
        check_remote_deletion(repo, remote, branch, ctx, findings, f'`{original}`')


def before(event, ctx, commands):
    findings = Findings()
    working = event.working_folder()
    for words in commands:
        if not words:
            continue
        program = os.path.basename(words[0])
        original = ' '.join(words)
        if program == 'rm':
            check_rm(words, working, ctx, findings, original)
        elif program == 'gh':
            check_gh(words, working, ctx, findings, original)
        elif program == 'git':
            sub, rest = hookkit.git_subcommand(words)
            folder = hookkit.git_folder(words, working)
            if sub == 'branch':
                check_branch(rest, folder, ctx, findings, original)
            elif sub in ('switch', 'checkout'):
                names = {'switch': ('-c', '-C', '--create', '--force-create'), 'checkout': ('-b', '-B', '--orphan')}[sub]
                for i, w in enumerate(rest):
                    if w in names and i + 1 < len(rest):
                        creation(rest[i + 1], folder, ctx, findings)
                    elif w.startswith(tuple(n + '=' for n in names if n.startswith('--'))):
                        creation(w.split('=', 1)[1], folder, ctx, findings)
            elif sub == 'worktree' and rest[:1] == ['remove']:
                check_worktree_remove(rest[1:], folder, ctx, findings, original)
            elif sub == 'worktree' and rest[:1] == ['add']:
                for i, w in enumerate(rest):
                    if w in ('-b', '-B') and i + 1 < len(rest):
                        creation(rest[i + 1], folder, ctx, findings)
            elif sub == 'push':
                check_push(rest, folder, ctx, findings, original)
            elif sub == 'stash':
                check_stash(rest, folder, ctx, findings, original)
            elif sub == 'merge':
                check_merge(rest, folder, ctx, findings, original)
    return findings


def after(event, ctx, commands):
    """After a merge or a deletion, clear the register rows that are now settled."""
    if not ctx.kit.on('clear_settled_rows'):
        return None
    working, folders = event.working_folder(), []
    for words in commands:
        if not words:
            continue
        program = os.path.basename(words[0])
        sub, rest = hookkit.git_subcommand(words) if program == 'git' else (None, [])
        if program == 'gh' and words[1:3] == ['pr', 'merge']:
            folders.append(working)
        elif sub in ('merge', 'push', 'branch', 'fetch', 'pull'):
            folders.append(hookkit.git_folder(words, working))
    out, seen = [], set()
    for folder in folders:
        try:
            repo = ctx.repo(folder)
        except GitError:
            continue
        if repo.common_dir in seen:
            continue
        seen.add(repo.common_dir)
        settle(repo, ctx.register, ctx, out)
    return '\n'.join(out)


TRIGGERS = re.compile(r'\brm\b|\bgit\b.*\b(?:branch|push|stash|worktree|merge|switch|checkout)\b|\bgh\b.*\b(?:merge|api)\b')


def handle(event, kit):
    if event.kind == 'session-start':
        if not kit.on('session_start'):
            return None
        return kit.context(state_text(Context(kit)))
    if event.tool != 'shell' or event.kind not in ('before-tool', 'after-tool'):
        return None
    if not TRIGGERS.search(event.acting_command()):
        return None
    commands = event.commands()
    if commands is None:
        if event.kind == 'before-tool':
            return kit.context('branch-keeper could not read this command as shell (a quote or a substitution left open), so it '
                               'did not check what it removes, deletes or creates.')
        return None
    ctx = Context(kit)
    if event.kind == 'after-tool':
        text = after(event, ctx, commands)
        return kit.context(text) if text else None
    findings = before(event, ctx, commands)
    if findings.deny:
        kit.log('refused.log', ' '.join(event.command.split())[:200])
        return kit.deny('\n\n'.join(findings.deny + findings.ask + findings.context))
    if findings.ask:
        kit.log('asked.log', ' '.join(event.command.split())[:200])
        return kit.ask('\n\n'.join(findings.ask + findings.context))
    if findings.context:
        return kit.context('\n\n'.join(findings.context))
    return None


# ---------------------------------------------------------------- the audit, from the command line

def audit(argv):
    ap = argparse.ArgumentParser(prog='hook.py audit', description='Print the branches of every configured repository: '
                                 'not in main with their reason, inside main still there, work on no remote. Exit status 0 when '
                                 'nothing is owed, 1 when a branch not in main has no reason or work is on no remote, 2 when '
                                 'something could not be read.')
    ap.add_argument('--fetch', action='store_true', help='fetch each repository\'s remote first (with --prune); the only network use')
    ap.add_argument('--config', help='the configuration file (default: SPARKY_HOOKS_CONFIG_DIR or SPARKY_WORKSPACE, as the hook)')
    ap.add_argument('repositories', nargs='*', metavar='REPOSITORY', help='names or folders; a folder not configured is read with the defaults')
    a = ap.parse_args(argv)
    try:
        config_path = a.config or hookkit.find_config(NAME, [])
        cfg = hookkit.load_config(config_path)
        kit = hookkit.Kit(NAME, cfg, config_path)
    except hookkit.HookError as e:
        print(f'audit: {e}', file=sys.stderr)
        return 2
    ctx = Context(kit)
    specs = ctx.specs()
    if a.repositories:
        chosen = []
        for want in a.repositories:
            match = [s for s in specs if want in (s.get('name'), os.path.basename(s['path'].rstrip(os.sep)))
                     or os.path.realpath(s['path']) == os.path.realpath(want)]
            chosen += match or [{'path': os.path.abspath(want)}]
        specs = chosen
    register = ctx.register
    unreadable, no_reason, local_only, stashes, dirty, notin, gone = 0, 0, 0, 0, 0, 0, 0
    print(f'register: {register.path}' + (' (none yet)' if register.missing else ''))
    if register.problem:
        print(f'REGISTER NOT READ: {register.problem}')
        unreadable += 1
    for note in register.notes:
        print(f'REGISTER: {note}')
        unreadable += 1
    if not specs:
        print(f'No repository is configured: list them under "repositories" in {config_path}.')
        unreadable += 1
    for spec in specs:
        label = spec.get('name') or os.path.basename(spec['path'].rstrip(os.sep))
        print(f'\n== {label}  {spec["path"]}')
        if a.fetch:
            remote = spec.get('remote', 'origin')
            try:
                run_git(spec['path'], ['fetch', '--prune', remote], timeout=600, network=True)
                print(f'fetched {remote}')
            except GitError as e:
                print(f'FETCH FAILED: {e}; what follows is as of the last fetch')
                unreadable += 1
        try:
            repo = Repo(spec['path'], spec, cfg)
            out = []
            gone += settle(repo, register, ctx, out)
            state = read_state(repo, register, ctx)
        except GitError as e:
            print(f'NOT READ: {e}')
            unreadable += 1
            continue
        for line in out:
            print(line)
        nim = state['not_in_main']
        print(f'main {short(repo.need_main())}; last fetch {age(state["last_fetch"])}' + ('; shallow clone' if repo.shallow else ''))
        print(f'not in main: {len(nim)} ({len(state["no_reason"])} with no reason recorded)')
        for b in sorted(nim, key=lambda b: (register.recorded(repo.name, b), b)):
            r = nim[b]
            print(f'  {b:<44} {r["where"]:<16} {r["ahead"]:>4} ahead  {r["date"]}  {register.describe(repo.name, b)}')
        print(f'inside main, still there: {len(state["inside_main"])}')
        for b, where in sorted(state['inside_main'].items()):
            print(f'  {b:<44} {where}')
        print(f'commits on no remote: {len(state["local_only"])} branch(es)' + (f', and a detached HEAD with {state["detached"]} commit(s) in no branch' if state['detached'] else ''))
        for b, sha, n in state['local_only']:
            print(f'  {b:<44} {n} commit(s), tip {sha[:12]}')
        print(f'stashes: {len(state["stashes"])}')
        for s in state['stashes']:
            print(f'  {s}')
        if state['dirty'] is None:
            print(f'uncommitted or untracked: NOT COUNTED ({state["dirty_problem"]})')
            unreadable += 1
        else:
            print(f'uncommitted or untracked: {len(state["dirty"])}')
            for d in state['dirty']:
                print(f'  {d}')
        notin += len(nim)
        no_reason += len(state['no_reason'])
        local_only += len(state['local_only']) + bool(state['detached'])
        stashes += len(state['stashes'])
        dirty += len(state['dirty'] or [])
    status = 2 if unreadable else 1 if (no_reason or local_only or stashes or dirty or gone) else 0
    print(f'\naudit: {len(specs)} repositories, {unreadable} thing(s) not read; {notin} branch(es) not in main, {no_reason} with '
          f'no reason recorded; {local_only} with commits on no remote; {stashes} stash(es); {dirty} uncommitted or untracked; '
          f'{gone} register row(s) whose branch is gone; exit {status}')
    return status


if __name__ == '__main__':
    if 'audit' in sys.argv[1:]:  # anywhere: `hook.py --config FILE audit` must not wait for an event on stdin
        arguments = sys.argv[1:]
        arguments.remove('audit')
        sys.exit(audit(arguments))
    sys.exit(hookkit.main(NAME, handle))
