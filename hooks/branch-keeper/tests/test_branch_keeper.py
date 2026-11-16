#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the branch-keeper hook. Run: python3 hooks/tests/run.py branch-keeper

Every repository here is made in the test's temporary folder: a bare repository plays the remote, and the clones,
worktrees, stashes and bundles are made with git itself. No test reads or changes a repository outside that folder.
The bare remotes live on disk, so most tests count every remote as online ("online_remotes": "any"); one test proves
the default, where only a network address counts.
"""
import json
import os
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import testkit  # noqa: E402

GIT_ENV = {'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_AUTHOR_NAME': 'Test',
           'GIT_AUTHOR_EMAIL': 'test@example.org', 'GIT_COMMITTER_NAME': 'Test', 'GIT_COMMITTER_EMAIL': 'test@example.org'}
HOOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'hook.py')


class BranchKeeper(testkit.HookCase):
    hook = 'branch-keeper'

    def setUp(self):
        super().setUp()
        self.remote = self.bare('o/proj.git')
        self.clone = self.clone_of(self.remote, os.path.join(self.ws, 'repos', 'proj'))
        self.commit(self.clone, 'a.txt')
        self.git(self.clone, 'push', '-q', 'origin', 'main')
        self.git(self.clone, 'fetch', '-q', 'origin')
        self.configure(repositories=[{'path': self.clone, 'name': 'proj', 'main': 'main', 'deletes_merged_head': True}],
                       online_remotes='any')
        self.register = os.path.join(self.ws, 'private', 'branches.tsv')

    # making repositories
    def git(self, folder, *args):
        r = subprocess.run(['git', '-C', folder, *args], capture_output=True, text=True, env={**os.environ, **GIT_ENV})
        self.assertEqual(r.returncode, 0, f'git {" ".join(args)}: {r.stderr}')
        return r.stdout

    def bare(self, rel):
        path = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.git(self.tmp, 'init', '-q', '--bare', '-b', 'main', path)
        return path

    def clone_of(self, remote, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.git(self.tmp, 'clone', '-q', remote, path)
        self.git(path, 'symbolic-ref', 'HEAD', 'refs/heads/main')
        return path

    def commit(self, folder, name, text='x\n'):
        testkit.write(os.path.join(folder, name), text)
        self.git(folder, 'add', name)
        self.git(folder, 'commit', '-q', '-m', name)
        return self.git(folder, 'rev-parse', 'HEAD').strip()

    def branch_with_commit(self, name, push=False, folder=None):
        folder = folder or self.clone
        self.git(folder, 'switch', '-q', '-c', name)
        self.commit(folder, name.replace('/', '-') + '.txt')
        if push:
            self.git(folder, 'push', '-q', 'origin', name)
        self.git(folder, 'switch', '-q', 'main')

    def rows(self, *lines):
        with open(self.register, 'a', encoding='utf-8') as f:
            for line in lines:
                f.write('\t'.join(line) + '\n')

    def unreadable(self, path):
        os.chmod(path, 0)
        self.addCleanup(os.chmod, path, 0o755)

    # running the hook
    def answer(self, command, phase='PreToolUse', cwd=None, **kw):
        payload = self.bash(command, phase=phase, **kw)
        if cwd:
            payload['cwd'] = cwd
        return self.run_hook(payload, env=GIT_ENV)

    def refused(self, command, *words, **kw):
        out = self.answer(command, **kw)
        self.assertEqual(self.decision(out), 'deny', f'{command}: {out}')
        for word in words:
            self.assertIn(word, self.reason(out))
        return self.reason(out)

    def told(self, command, *words, **kw):
        out = self.answer(command, **kw)
        self.assertIsNone(self.decision(out), f'{command}: {out}')
        text = self.added_context(out)
        for word in words:
            self.assertIn(word, text)
        return text

    def passes(self, command, **kw):
        out = self.answer(command, **kw)
        self.assertIsNone(out, f'{command}: {out}')

    def session_start(self):
        out = self.run_hook(self.event('SessionStart', source='startup'), env=GIT_ENV)
        return self.added_context(out)

    def audit(self, *args):
        command = [sys.executable, '-B', HOOK, 'audit', '--config', self.config, *args]
        env = {k: v for k, v in os.environ.items() if not k.startswith('SPARKY_')}
        env.update(GIT_ENV)
        return subprocess.run(command, capture_output=True, text=True, env=env, timeout=120)

    # 1. the state at session start
    def test_the_session_start_counts_first_and_names_each_branch_with_its_reason(self):
        self.branch_with_commit('order7-x')                       # local only, no row
        self.branch_with_commit('order8-y', push=True)            # online, a kept row
        self.branch_with_commit('order10-w', push=True)           # online, a row that is no reason
        self.branch_with_commit('order9-z', push=True)
        self.git(self.clone, 'merge', '-q', '--no-edit', 'order9-z')
        self.git(self.clone, 'push', '-q', 'origin', 'main')       # order9-z is inside main, still there
        testkit.write(os.path.join(self.clone, 'a.txt'), 'changed\n')
        self.git(self.clone, 'stash', '-q')
        testkit.write(os.path.join(self.clone, 'new.txt'), 'untracked\n')
        self.rows(('proj', 'order8-y', 'kept', 'input for the next rebase', '2026-11-16'),
                  ('proj', 'order10-w', 'check', 'compare with main first', '2026-11-16'))
        text = self.session_start()
        self.assertIn('proj (origin/main is main): 3 branch(es) not in main (2 with no reason recorded), 1 inside main still there, '
                      '1 local branch(es) with commits on no remote, 1 stash(es), 1 uncommitted or untracked; last fetch', text)
        self.assertIn('order7-x (local, 1 commit(s) main lacks', text)
        self.assertIn('order8-y (local and online, 1 commit(s) main lacks', text)
        self.assertIn('kept: input for the next rebase', text)
        self.assertIn('order10-w (local and online, 1 commit(s) main lacks', text)
        self.assertIn('NO REASON RECORDED (the register says "check: compare with main first"', text)
        self.assertLess(text.index('order10-w ('), text.index('order8-y ('))   # the ones without a reason come first
        self.assertIn('Inside main, still there (they can go): order9-z (local and online)', text)
        self.assertIn('Commits on no remote: order7-x (1)', text)
        self.assertIn('Stashes: stash@{0}', text)
        self.assertIn('Uncommitted or untracked: new.txt', text)
        self.assertIn('audit --config', text)

    def test_the_names_are_cut_after_max_names(self):
        for n in (21, 22, 23):
            self.branch_with_commit(f'order{n}-x')
        self.configure(max_names=1)
        self.assertIn('; and 2 more', self.session_start())

    def test_a_repository_that_cannot_be_read_is_said_never_left_out(self):
        other = self.clone_of(self.remote, os.path.join(self.tmp, 'other'))
        self.configure(repositories=[{'path': os.path.join(self.tmp, 'absent'), 'name': 'absent'},
                                     {'path': other, 'name': 'locked'},
                                     {'path': self.clone, 'name': 'nomain', 'main': 'trunk'},
                                     {'path': self.clone, 'name': 'proj'}])
        self.unreadable(os.path.join(other, '.git'))
        text = self.session_start()
        self.assertIn('absent (' + os.path.join(self.tmp, 'absent') + '): NOT READ: no such folder', text)
        self.assertIn('locked (' + other + '): NOT READ: git rev-parse', text)
        self.assertIn('nomain (' + self.clone + '): NOT READ: no main branch found (trunk', text)
        self.assertIn('proj (origin/main is main)', text)
        r = self.audit()
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn('NOT READ', r.stdout)

    def test_a_register_inside_a_repository_with_a_remote_is_not_read(self):
        self.configure(paths={'register': os.path.join(self.clone, 'branches.tsv')})
        self.assertIn('REGISTER NOT READ: the register ' + os.path.join(self.clone, 'branches.tsv')
                      + ' lies inside a repository with a remote', self.session_start())
        self.assertEqual(self.audit().returncode, 2)

    def test_settled_rows_are_cleared_and_kept_work_that_is_gone_is_said(self):
        self.branch_with_commit('order9-z', push=True)
        self.git(self.clone, 'merge', '-q', '--no-edit', 'order9-z')
        self.git(self.clone, 'push', '-q', 'origin', 'main')
        self.rows(('proj', 'order9-z', 'kept', 'was waiting', '2026-11-16'),
                  ('proj', 'order30-gone', 'superseded', 'replaced by order31', '2026-11-16'),
                  ('proj', 'order32-gone', 'kept', 'the only copy of the kit', '2026-11-16'),
                  ('proj', 'order33-gone', 'check', 'compare first', '2026-11-16'),
                  ('other', 'order9-z', 'kept', 'another repository', '2026-11-16'))
        text = self.session_start()
        self.assertIn('proj: register rows cleared', text)
        self.assertIn('order9-z (merged into main); order30-gone (deleted)', text)
        self.assertIn('proj: KEPT WORK GONE', text)
        self.assertIn('order32-gone (kept: the only copy of the kit)', text)
        self.assertIn('proj: ROWS WITHOUT THEIR BRANCH', text)
        self.assertIn('order33-gone (check: compare first)', text)
        self.assertNotIn('order33-gone (check', text.split('ROWS WITHOUT')[0])
        r = self.audit()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('2 register row(s) whose branch is gone', r.stdout)
        with open(self.register) as f:
            left = f.read()
        self.assertNotIn('order9-z\tkept\twas waiting', left)
        self.assertNotIn('order30-gone', left)
        self.assertIn('order32-gone', left)
        self.assertIn('other\torder9-z', left)
        self.assertIn('proj | order9-z | kept | was waiting', self.log('cleared.log'))
        self.configure(on={'clear_settled_rows': False})
        self.rows(('proj', 'order9-z', 'kept', 'again', '2026-11-16'))
        self.assertNotIn('register rows cleared', self.session_start())

    def test_reading_writes_nothing_in_the_repository(self):
        self.branch_with_commit('order7-x')
        index = os.path.join(self.clone, '.git', 'index')
        refs = self.git(self.clone, 'for-each-ref')
        os.utime(os.path.join(self.clone, 'a.txt'))          # git status would refresh the index if it were allowed to
        before = os.stat(index).st_mtime_ns
        self.session_start()
        self.refused('rm -rf repos/proj')
        self.assertEqual(os.stat(index).st_mtime_ns, before)
        self.assertEqual(self.git(self.clone, 'for-each-ref'), refs)

    def test_switched_off_and_disabled(self):
        self.branch_with_commit('order7-x')
        self.configure(on={'session_start': False, 'removal': False})
        self.assertIsNone(self.run_hook(self.event('SessionStart', source='startup'), env=GIT_ENV))
        self.passes('rm -rf repos/proj')
        self.configure(on={'removal': True}, enabled=False)
        self.passes('rm -rf repos/proj')

    # 2. refusing to lose work: rm -r
    def test_rm_of_a_clone_with_commits_on_no_remote_is_refused_in_every_form(self):
        self.branch_with_commit('order7-x')
        for command in ('rm -rf repos/proj', f'rm -r {self.clone}', 'cd repos && rm -r proj', 'rm -r -- "repos/proj"',
                        "bash -c 'rm -rf repos/proj'", 'sudo rm -fr repos/proj', 'rm --recursive repos/proj',
                        'rm -rf repos', 'rm -rf repos/*', f'timeout 60 rm -Rf {self.ws}/repos/proj',
                        '# a note\nrm -rf \\\n  repos/proj', 'for d in x; do rm -rf repos/proj; done'):
            with self.subTest(command):
                self.refused(command, f'- {self.clone} (clone): branch order7-x: 1 commit(s) on no remote', 'What to do')
        self.assertIn('rm -rf repos/proj', self.log('refused.log'))

    def test_each_kind_of_work_is_named(self):
        cases = {'uncommitted': ('a.txt', '1 uncommitted or untracked: a.txt'),
                 'untracked': ('new.txt', '1 uncommitted or untracked: new.txt')}
        for case, (name, words) in cases.items():
            with self.subTest(case):
                clone = self.clone_of(self.remote, os.path.join(self.ws, 'repos', case))
                testkit.write(os.path.join(clone, name), 'work\n')
                self.refused(f'rm -rf repos/{case}', words)
        stash = self.clone_of(self.remote, os.path.join(self.ws, 'repos', 'stash'))
        testkit.write(os.path.join(stash, 'a.txt'), 'work\n')
        self.git(stash, 'stash', '-q')
        self.refused('rm -rf repos/stash', '1 stash(es): stash@{0}')
        detached = self.clone_of(self.remote, os.path.join(self.ws, 'repos', 'detached'))
        self.git(detached, 'switch', '-q', '--detach')
        self.commit(detached, 'loose.txt')
        self.refused('rm -rf repos/detached', 'a detached HEAD with 1 commit(s) in no branch')

    def test_rm_passes_when_nothing_would_be_lost(self):
        testkit.write(os.path.join(self.clone, '.gitignore'), 'build/\n')
        self.git(self.clone, 'add', '.gitignore')
        self.git(self.clone, 'commit', '-q', '-m', 'ignore')
        self.git(self.clone, 'push', '-q', 'origin', 'main')
        testkit.write(os.path.join(self.clone, 'build', 'out.o'), 'ignored\n')
        testkit.write(os.path.join(self.ws, 'scratch', 'notes.txt'), 'not a clone\n')
        for command in ('rm -rf repos/proj', 'rm -rf scratch', 'rm repos/proj/a.txt', 'rm -rf repos/proj/build',
                        'ls repos', 'git status', 'rm -rf absent-folder'):
            with self.subTest(command):
                self.passes(command)

    def test_a_link_is_never_followed_except_the_one_rm_follows(self):
        self.branch_with_commit('order7-x')
        os.symlink(self.clone, os.path.join(self.ws, 'link'))
        testkit.write(os.path.join(self.ws, 'lane', 'notes.txt'), 'x\n')
        os.symlink(os.path.join(self.ws, 'repos'), os.path.join(self.ws, 'lane', 'into-repos'))
        self.passes('rm -rf link')              # only the link goes
        self.passes('rm -rf lane')              # the link inside goes, not what it points to
        self.refused('rm -r link/', f'- {self.clone} (clone)')   # GNU rm empties the target of LINK/

    def test_a_path_with_spaces(self):
        clone = self.clone_of(self.remote, os.path.join(self.ws, 'repos', 'my proj'))
        self.branch_with_commit('order7-x', folder=clone)
        self.refused('rm -rf "repos/my proj"', 'branch order7-x')
        self.refused("rm -rf repos/my\\ proj", 'branch order7-x')
        self.refused('git -C "repos/my proj" branch -D order7-x', 'loses 1 commit(s)')

    def test_linked_worktrees(self):
        self.branch_with_commit('order7-x', push=True)
        outside = os.path.join(self.tmp, 'wt-outside')
        self.git(self.clone, 'worktree', 'add', '-q', outside, 'order7-x')
        self.refused('rm -rf repos/proj', f'its linked worktree {outside} would be left without its repository')
        inner = os.path.join(self.ws, 'lane', 'wt')
        self.git(self.clone, 'worktree', 'add', '-q', '-b', 'order8-wt', inner, 'main')
        self.passes('rm -rf lane/wt')            # its branch stays in the clone, nothing else is in it
        testkit.write(os.path.join(inner, 'draft.txt'), 'work\n')
        self.refused('rm -rf lane', f'- {inner} (worktree of {self.clone}): 1 uncommitted or untracked: draft.txt')

    def test_a_bundle_in_the_queue_counts_as_kept(self):
        self.branch_with_commit('order7-x')
        reason = self.refused('rm -rf repos/proj', 'branch order7-x')
        self.assertIn(os.path.join(self.ws, 'partners', 'queue'), reason)
        os.makedirs(os.path.join(self.ws, 'partners', 'queue', 'lane-7'), exist_ok=True)
        self.git(self.clone, 'bundle', 'create', '-q', os.path.join(self.ws, 'partners', 'queue', 'lane-7', 'proj.bundle'), 'order7-x')
        self.passes('rm -rf repos/proj')
        self.configure(bundle_folders=[os.path.join(self.tmp, 'elsewhere')])
        self.refused('rm -rf repos/proj', 'branch order7-x')

    def test_by_default_only_a_network_remote_is_online(self):
        self.configure(online_remotes='network')
        self.refused('rm -rf repos/proj', 'branch main: 1 commit(s) on no remote')
        self.git(self.clone, 'remote', 'set-url', 'origin', 'https://example.org/o/proj.git')
        self.passes('rm -rf repos/proj')

    def test_a_repository_that_cannot_be_read_is_not_removed_unchecked(self):
        self.unreadable(os.path.join(self.clone, '.git'))
        self.refused('rm -rf repos', f'- {self.clone}: could not be read', 'the person removes it')

    def test_an_unreadable_clone_inside_another_repository_is_not_taken_for_the_outer_one(self):
        outer = os.path.join(self.ws, 'outer')
        self.git(self.tmp, 'init', '-q', '-b', 'main', outer)
        inner = self.clone_of(self.remote, os.path.join(outer, 'inner'))
        self.branch_with_commit('order7-x', folder=inner)
        self.unreadable(os.path.join(inner, '.git'))
        self.refused('rm -rf outer/inner', f'- {inner}: could not be read (git answers for {outer} here')

    def test_a_folder_too_big_to_look_inside_is_refused(self):
        self.configure(scan_limit=1)
        self.refused('rm -rf repos', 'could not look inside all of ' + os.path.join(self.ws, 'repos'), 'scan_limit 1')

    def test_a_path_the_hook_cannot_see_is_said(self):
        self.told('rm -rf "$DIR/x"', 'could not see what "$DIR/x"')
        self.told('rm -rf $(cat list)', 'could not see what')
        self.configure(on_unresolved_path='deny')
        self.refused('rm -rf "$DIR"', 'could not see what')
        self.configure(on_unresolved_path='sometimes')
        out = self.answer('rm -rf "$DIR"')
        self.assertIn('"on_unresolved_path" must be context, ask or deny', out['systemMessage'])

    def test_text_that_is_only_written_is_not_a_command(self):
        self.branch_with_commit('order7-x')
        self.passes("cat > notes.md <<'EOF'\nrm -rf repos/proj\ngit branch -D order7-x\nEOF")
        self.passes('git commit -m "rm -rf repos/proj"')
        self.refused("bash <<'EOF'\nrm -rf repos/proj\nEOF", 'branch order7-x')

    def test_a_bare_repository_and_a_repository_database(self):
        self.branch_with_commit('order7-x')
        bare = self.bare(os.path.join(os.path.basename(self.ws), 'mirror.git'))
        self.git(self.clone, 'push', '-q', bare, 'main')
        self.refused('rm -rf mirror.git', f'- {bare} (bare repository): branch main: 1 commit(s) on no remote')
        self.refused('rm -rf repos/proj/.git', 'the repository database of', 'branch order7-x')

    # 2. git worktree remove
    def test_worktree_remove(self):
        self.branch_with_commit('order7-x')
        wt = os.path.join(self.tmp, 'wt')
        self.git(self.clone, 'worktree', 'add', '-q', wt, 'order7-x')
        self.told(f'git -C repos/proj worktree remove {wt}', f'its branch order7-x stays in {self.clone} with 1 commit(s) on no remote')
        testkit.write(os.path.join(wt, 'draft.txt'), 'work\n')
        self.refused(f'git -C repos/proj worktree remove --force {wt}', '1 uncommitted or untracked: draft.txt')
        os.unlink(os.path.join(wt, 'draft.txt'))
        self.git(wt, 'switch', '-q', '--detach')
        self.commit(wt, 'loose.txt')
        self.refused(f'git -C repos/proj worktree remove {wt}', 'a detached HEAD with 1 commit(s) in no branch')
        clean = os.path.join(self.tmp, 'wt-clean')
        self.git(self.clone, 'worktree', 'add', '-q', '--detach', clean, 'main')
        self.passes(f'git -C repos/proj worktree remove {clean}')

    # 2. git branch -D
    def test_deleting_a_local_branch_that_holds_the_only_copy_is_refused(self):
        self.branch_with_commit('order7-x')
        for command in ('git -C repos/proj branch -D order7-x', 'cd repos/proj && git branch -D order7-x',
                        'git -C repos/proj branch --delete --force order7-x', 'git -C repos/proj branch -df order7-x'):
            with self.subTest(command):
                reason = self.refused(command, 'deleting the branch order7-x of proj loses 1 commit(s)', 'NO REASON RECORDED')
                self.assertIn('proj\torder7-x\tsuperseded\t', reason)
        self.passes('git -C repos/proj branch -d order7-x')      # git refuses an unmerged -d itself
        self.passes('git -C repos/proj branch -D no-such-branch')
        self.rows(('proj', 'order7-x', 'superseded', 'squash-merged as abc123', '2026-11-16'))
        self.told('git -C repos/proj branch -D order7-x', 'the register marks it superseded: squash-merged as abc123')

    def test_a_branch_whose_commits_another_branch_holds_loses_nothing(self):
        self.branch_with_commit('order7-x')
        self.git(self.clone, 'branch', 'order7-copy', 'order7-x')
        self.told('git -C repos/proj branch -D order7-x', 'deleting order7-x loses no commit: order7-copy still holds its 1 commit(s)')
        self.branch_with_commit('order8-y', push=True)
        self.passes('git -C repos/proj branch -D order8-y')

    # 2. deleting a remote branch
    def test_a_remote_branch_not_inside_main_goes_only_with_a_superseded_row(self):
        self.branch_with_commit('order8-y', push=True)
        for command in ('git -C repos/proj push origin --delete order8-y', 'git -C repos/proj push origin :order8-y',
                        'git -C repos/proj push -d origin order8-y', 'git -C repos/proj push origin +:refs/heads/order8-y',
                        'gh api -X DELETE repos/o/proj/git/refs/heads/order8-y', 'gh api --method DELETE /repos/o/proj/git/refs/heads/order8-y'):
            with self.subTest(command):
                cwd = self.clone if command.startswith('gh') else None
                self.refused(command, 'deletes origin/order8-y of proj, which is not inside origin/main', 'proj\torder8-y\tsuperseded\t', cwd=cwd)
        self.rows(('proj', 'order8-y', 'kept', 'input for 609', '2026-11-16'))
        self.refused('git -C repos/proj push origin --delete order8-y', 'which the register keeps: input for 609')
        with open(self.register, 'w') as f:
            f.write('proj\torder8-y\tsuperseded\treplaced by order9\t2026-11-16\n')
        self.told('git -C repos/proj push origin --delete order8-y', 'the register marks it superseded: replaced by order9')

    def test_a_remote_branch_inside_main_goes_without_a_word(self):
        self.branch_with_commit('order9-z', push=True)
        self.git(self.clone, 'merge', '-q', '--no-edit', 'order9-z')
        self.git(self.clone, 'push', '-q', 'origin', 'main')
        self.passes('git -C repos/proj push origin --delete order9-z')
        self.passes('gh api -X DELETE repos/o/proj/git/refs/heads/order9-z', cwd=self.clone)

    def test_a_remote_branch_the_clone_has_not_fetched_cannot_be_judged(self):
        other = self.clone_of(self.remote, os.path.join(self.tmp, 'other'))
        self.branch_with_commit('order12-new', push=True, folder=other)
        self.refused('git -C repos/proj push origin --delete order12-new', 'not among the local remote-tracking refs', 'Fetch first')

    def test_other_ways_of_deleting_remote_branches(self):
        self.branch_with_commit('order8-y', push=True)
        self.git(self.clone, 'branch', '-D', 'order8-y')
        self.refused('git -C repos/proj push --mirror origin', 'origin/order8-y', '(no local branch of that name)')
        self.refused('git -C repos/proj push --delete https://example.org/elsewhere.git order8-y', 'is no remote of proj')
        self.refused('gh api -X DELETE repos/someone/else/git/refs/heads/x', 'no repository here has that remote', cwd=self.clone)
        self.passes('gh api repos/o/proj/git/refs/heads/order8-y', cwd=self.clone)
        self.configure(on={'remote_deletion': False})
        self.passes('git -C repos/proj push origin --delete order8-y')

    def test_a_register_that_cannot_be_read_refuses_a_deletion(self):
        self.branch_with_commit('order8-y', push=True)
        self.rows(('proj', 'order8-y', 'superseded', 'replaced', '2026-11-16'))
        self.unreadable(self.register)
        self.refused('git -C repos/proj push origin --delete order8-y', 'the register cannot be read')

    # 2. stashes
    def test_dropping_a_stash_is_refused_while_one_exists(self):
        self.passes('git -C repos/proj stash drop')
        for n in (1, 2):
            testkit.write(os.path.join(self.clone, 'a.txt'), f'work {n}\n')
            self.git(self.clone, 'stash', 'push', '-q', '-m', f'draft {n}')
        self.refused('git -C repos/proj stash drop', 'stash@{0} (On main: draft 2)', 'git stash branch NAME STASH')
        self.refused('git -C repos/proj stash drop 1', 'stash@{1} (On main: draft 1)')
        self.refused('git -C repos/proj stash drop stash@{1}', 'stash@{1}')
        self.refused('git -C repos/proj stash clear', 'stash@{0}', 'stash@{1}')
        self.passes('git -C repos/proj stash drop stash@{7}')
        self.passes('git -C repos/proj stash list')
        self.passes('git -C repos/proj stash pop')

    # 3. a new branch
    def test_a_new_branch_is_told_the_rule_and_every_branch_with_its_number(self):
        self.branch_with_commit('order7-x')
        other_remote = self.bare('o/other.git')
        other = self.clone_of(other_remote, os.path.join(self.ws, 'repos', 'other'))
        self.commit(other, 'b.txt')
        self.git(other, 'push', '-q', 'origin', 'main')
        self.branch_with_commit('order7-elsewhere', push=True, folder=other)
        self.git(other, 'branch', '-D', 'order7-elsewhere')
        self.branch_with_commit('order77-not-the-same', folder=other)
        self.configure(repositories=[{'path': self.clone, 'name': 'proj', 'main': 'main'}, {'path': other, 'name': 'other', 'main': 'main'}])
        for command in ('git -C repos/proj switch -c order7-again', 'git -C repos/proj checkout -b order7-again',
                        'git -C repos/proj branch order7-again', 'git -C repos/proj branch order7-again main',
                        'git -C repos/proj worktree add -b order7-again ../wt7', 'git -C repos/proj switch --create=order7-again'):
            with self.subTest(command):
                text = self.told(command, 'New branch order7-again. The rule: one branch per piece of work',
                                 'Branches that already carry 7: proj: order7-x (local, last', 'other: order7-elsewhere (online, last')
                self.assertNotIn('order77', text)

    def test_a_first_push_is_a_new_branch_too(self):
        self.branch_with_commit('order7-x', push=True)
        self.git(self.clone, 'switch', '-q', '-c', 'order11-new')
        self.told('git -C repos/proj push -u origin order11-new', 'First push of the new branch order11-new', 'No branch, local or online, carries 11')
        self.told('git -C repos/proj push origin HEAD:order12-new', 'First push of the new branch order12-new')
        self.told('git -C repos/proj push -u origin', 'First push of the new branch order11-new')
        self.passes('git -C repos/proj push origin order7-x')   # it exists online already

    def test_listing_and_other_branch_commands_are_not_a_new_branch(self):
        for command in ('git -C repos/proj branch', 'git -C repos/proj branch -a', "git -C repos/proj branch --list 'order*'",
                        'git -C repos/proj branch -m order1-a order1-b', 'git -C repos/proj checkout main',
                        'git -C repos/proj switch main', 'git -C repos/proj branch --contains HEAD',
                        'git -C repos/proj branch -u origin/main'):
            with self.subTest(command):
                self.passes(command)

    def test_a_name_outside_the_rule_is_told_asked_or_refused(self):
        self.told('git -C repos/proj switch -c my-idea', 'The name my-idea does not follow the rule here',
                  'This name carries no work number')
        self.told('git -C repos/proj switch -c wip/draft-2026-11-16', 'This name carries no work number')
        self.configure(name_rule_outside='ask')
        self.assertEqual(self.decision(self.answer('git -C repos/proj switch -c my-idea')), 'ask')
        self.configure(name_rule_outside='deny')
        self.refused('git -C repos/proj switch -c my-idea', 'does not follow the rule')
        self.told('git -C repos/proj switch -c order5-fine', 'New branch order5-fine')
        self.configure(on={'branch_creation': False})
        self.passes('git -C repos/proj switch -c my-idea')

    # 4. the merge
    def test_the_merge_reminds_that_the_branch_goes(self):
        self.branch_with_commit('order8-y', push=True)
        self.rows(('proj', 'order8-y', 'kept', 'waiting for review', '2026-11-16'))
        text = self.told('gh pr merge 12 --squash', 'After this merge, the branch of pull request 12 goes, online and locally',
                         "the repository deletes a merged pull request's branch by itself", 'squash-merged as COMMIT', cwd=self.clone)
        self.told('gh pr merge order8-y --merge', 'Its register row (kept: waiting for review) is cleared once the merge shows in main', cwd=self.clone)
        self.told('git -C repos/proj merge --no-ff order8-y', 'git branch -d order8-y', 'Its register row')
        self.assertNotIn('Its register row', text)
        self.git(self.clone, 'switch', '-q', 'order8-y')
        self.passes('git -C repos/proj merge main')            # bringing main into a lane branch is not the merge
        self.git(self.clone, 'switch', '-q', 'main')
        self.passes('git -C repos/proj merge --abort')
        self.configure(repositories=[{'path': self.clone, 'name': 'proj', 'main': 'main'}])
        self.told('git -C repos/proj merge order8-y', 'git -C ' + self.clone + ' push origin --delete order8-y')

    def test_after_the_merge_its_row_is_cleared(self):
        self.branch_with_commit('order8-y', push=True)
        self.rows(('proj', 'order8-y', 'kept', 'waiting for review', '2026-11-16'))
        self.passes('git -C repos/proj merge order7-nothing', phase='PostToolUse')   # nothing settled yet
        self.git(self.clone, 'merge', '-q', '--no-edit', 'order8-y')
        self.told('git -C repos/proj merge order8-y', 'proj: register rows cleared', 'order8-y (merged into main)', phase='PostToolUse')
        with open(self.register) as f:
            self.assertNotIn('order8-y', f.read())
        self.assertIn('proj | order8-y | kept | waiting for review', self.log('cleared.log'))

    # the audit, from the command line
    def test_the_audit_and_its_exit_status(self):
        r = self.audit()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('audit: 1 repositories, 0 thing(s) not read; 0 branch(es) not in main', r.stdout)
        self.branch_with_commit('order8-y', push=True)
        r = self.audit()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertRegex(r.stdout, r'order8-y +local and online +1 ahead  \d{4}-\d\d-\d\d  NO REASON RECORDED')
        self.rows(('proj', 'order8-y', 'kept', 'input for 609', '2026-11-16'))
        self.assertEqual(self.audit().returncode, 0)
        self.branch_with_commit('order7-x')
        r = self.audit()
        self.assertEqual(r.returncode, 1)
        self.assertIn('commits on no remote: 1 branch(es)', r.stdout)
        with open(self.register, 'a') as f:
            f.write('a line with no tabs\n')
        r = self.audit()
        self.assertEqual(r.returncode, 2)
        self.assertIn('REGISTER: line 4 of', r.stdout)

    def test_the_audit_fetches_only_when_asked_and_takes_names_or_folders(self):
        other = self.clone_of(self.remote, os.path.join(self.tmp, 'other'))
        self.branch_with_commit('order13-remote', push=True, folder=other)
        self.assertNotIn('order13-remote', self.audit().stdout)
        r = self.audit('--fetch')
        self.assertIn('fetched origin', r.stdout)
        self.assertIn('order13-remote', r.stdout)
        self.assertEqual(r.returncode, 1)
        r = self.audit('proj')
        self.assertIn('== proj', r.stdout)
        r = self.audit(other)
        self.assertIn('== other  ' + other, r.stdout)
        self.configure(repositories=[{'path': self.clone, 'name': 'proj', 'remote': 'nowhere'}])
        r = self.audit('--fetch')
        self.assertIn('FETCH FAILED', r.stdout)
        self.assertEqual(r.returncode, 2)

    def test_the_audit_finds_its_configuration_after_its_options_too(self):
        r = subprocess.run([sys.executable, '-B', HOOK, '--config', self.config, 'audit'], capture_output=True, text=True,
                           env={**os.environ, **GIT_ENV}, timeout=60, stdin=subprocess.DEVNULL)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('audit: 1 repositories', r.stdout)

    # tools
    def test_under_codex_a_refusal_is_a_refusal(self):
        self.branch_with_commit('order7-x')
        out = self.run_hook(self.bash('rm -rf repos/proj'), dialect='codex', env=GIT_ENV)
        self.assertEqual(self.decision(out), 'deny')
        self.configure(name_rule_outside='ask')
        out = self.run_hook(self.bash('git -C repos/proj switch -c my-idea'), dialect='codex', env=GIT_ENV)
        self.assertEqual(self.decision(out), 'deny')
        self.assertIn('cannot put the question to the person', self.reason(out))

    def test_the_example_configuration_is_what_init_wrote(self):
        with open(self.config) as f:
            cfg = json.load(f)
        self.assertEqual(cfg['paths']['register'], 'private/branches.tsv')
        self.assertTrue(os.path.isfile(self.register))


if __name__ == '__main__':
    unittest.main()
