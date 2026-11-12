#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the publish check: the checker, the tool hook and the two git hooks.
Run: python3 hooks/tests/run.py publish-check

The planted secrets and addresses are put together while the test runs, so this file itself passes the check.
"""
import os
import shutil
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import testkit  # noqa: E402

FOLDER = os.path.join(testkit.HOOKS, 'publish-check')
CHECKER = os.path.join(FOLDER, 'publish_check.py')
TOKEN = 'gh' + 'p_' + 'a1B2' * 9                     # shaped like a forge token
STRANGER = 'jane.roe' + '@' + 'not-reserved.zz'      # an address outside the domains reserved for examples
OURS = 'you' + '@' + 'example.org'
NAMED = 'project' + '-codename'                      # the example configuration's name that is never published
DASH = 'It works — on every screen.'
TINY_JPEG = bytes.fromhex(
    'ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d'
    '1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffc0000b080001000101011100ffc4001f000001050101'
    '0101010100000000000000000102030405060708090a0bffc400b5100002010303020403050504040000017d010203000411051221314106'
    '13516107227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455'
    '565758595a636465666768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9ba'
    'c2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda0008010100003f00fbfcffd9')


class Case(testkit.HookCase):
    hook = 'publish-check'

    def setUp(self):
        super().setUp()
        self.env = {'PATH': os.environ['PATH'], 'HOME': self.tmp, 'GIT_CONFIG_NOSYSTEM': '1',
                    'GIT_AUTHOR_NAME': 'You', 'GIT_AUTHOR_EMAIL': OURS, 'GIT_COMMITTER_NAME': 'You', 'GIT_COMMITTER_EMAIL': OURS}

    def git(self, repo, *args, check=True, **env):
        return subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True, check=check, env={**self.env, **env})

    def repo(self, name='project'):
        """A repository with one commit already on its remote."""
        path = os.path.join(self.ws, 'repos', name)
        bare = os.path.join(self.tmp, name + '.git')
        subprocess.run(['git', 'init', '-q', '--bare', bare], check=True, env=self.env)
        subprocess.run(['git', 'init', '-q', '-b', 'main', path], check=True, env=self.env)
        self.git(path, 'remote', 'add', 'origin', bare)
        testkit.write(os.path.join(path, 'README.md'), '# Project\n')
        self.git(path, 'add', 'README.md')
        self.git(path, 'commit', '-q', '-m', 'Start')
        self.git(path, 'push', '-q', 'origin', 'main')
        return path

    def commit(self, repo, name, text, message='Add a file', **env):
        testkit.write(os.path.join(repo, name), text)
        self.git(repo, 'add', name)
        return self.git(repo, 'commit', '-q', '-m', message, check=False, **env)

    def checker(self, *args, stdin=None):
        return subprocess.run([sys.executable, '-B', CHECKER, '--config', self.config, *args],
                              input=stdin, capture_output=True, text=True, env=self.env)


class Checker(Case):
    def test_clean_text_is_clean(self):
        r = self.checker('--text', stdin='One sentence per line.\nNothing to hide.\n')
        self.assertEqual((r.returncode, r.stdout), (0, 'publish-check: clean\n'))

    def test_hard_findings_stop(self):
        cases = {
            'looks like a GitHub token': f'token in a log: {TOKEN}\n',
            f"another person's email address {STRANGER}": f'Write to {STRANGER} for access.\n',
            'names a name that is never published': f'It builds on {NAMED} internally.\n',
            'looks like a private key': '-----BEGIN ' + 'OPENSSH PRIVATE KEY-----\n',
            'looks like a password or key written as a literal': 'pass' + 'word = "hunter2hunter2"\n',
        }
        for finding, text in cases.items():
            with self.subTest(finding):
                r = self.checker('--text', stdin=text)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn('STOP  stdin:1: ' + finding, r.stdout)

    def test_addresses_that_are_not_a_person_s_contact_pass(self):
        text = (f'Our own: {OURS}.\nAn example: list@lists.example.net and ' + 'x' + '@' + 'host.invalid.\n'
                'Signed-off-by: A Maintainer <maintainer' + '@' + 'kernel-like.zz>\n'
                'https://lore.example.zz/r/20261112.abc' + '@' + 'mail.zz/\n'
                'A file: logo@2x.png, a unit: getty@tty1.service\n'
                'A remote: git@github.com:some/project.git\n'
                'noreply: 1234+someone' + '@' + 'users.noreply.github.com\n')
        r = self.checker('--text', stdin=text)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn('email', r.stdout)

    def test_style_notes_do_not_stop(self):
        text = DASH + '\nAsk the owner first.\nThis line is wrapped in the\nmiddle of its sentence.\n'
        path = testkit.write(os.path.join(self.tmp, 'draft.md'), text)
        r = self.checker('--files', path)
        self.assertEqual(r.returncode, 0)
        for note in ('dash in the middle of a sentence', '"the owner": name the person', 'hard-wrapped line'):
            self.assertIn(note, r.stdout)
        self.assertNotIn('STOP', r.stdout)

    def test_code_and_quotes_are_not_judged_as_prose(self):
        text = 'Text.\n\n```\nresult — the owner\n```\n\n> a quoted line — as it was written\n\nThe phrase "the owner" in quotes names the phrase.\n'
        path = testkit.write(os.path.join(self.tmp, 'page.md'), text)
        self.assertEqual(self.checker('--files', path).stdout, 'publish-check: clean\n')

    def test_each_check_has_a_switch(self):
        self.configure(checks={'secrets': False, 'emails': False, 'never_name': False, 'style': False})
        r = self.checker('--text', stdin=f'{TOKEN} {STRANGER} {NAMED} {DASH}\n')
        self.assertEqual((r.returncode, r.stdout), (0, 'publish-check: clean\n'))

    def test_location_data_in_a_picture(self):
        picture = os.path.join(self.tmp, 'photo.jpg')
        with open(picture, 'wb') as f:
            f.write(TINY_JPEG)
        if not shutil.which('exiftool'):
            r = self.checker('--files', picture)
            self.assertEqual(r.returncode, 1)
            self.assertIn('location data NOT checked: exiftool is not installed', r.stdout)
            self.skipTest('exiftool is not installed: the GPS case was not run, only the refusal to pass unchecked')
        self.assertEqual(self.checker('--files', picture).stdout, 'publish-check: clean\n')
        subprocess.run(['exiftool', '-q', '-overwrite_original', '-GPSLatitude=10.5', '-GPSLatitudeRef=N',
                        '-GPSLongitude=20.25', '-GPSLongitudeRef=E', picture], check=True, capture_output=True)
        r = self.checker('--files', picture)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('location data (', r.stdout)
        self.assertIn('strip it: exiftool -gps:all=', r.stdout)
        self.configure(checks={'location_data': False})
        self.assertEqual(self.checker('--files', picture).returncode, 0)

    def test_commits_no_remote_has_are_checked_and_pushed_ones_are_not(self):
        repo = self.repo()
        self.commit(repo, 'old.txt', f'{TOKEN}\n')
        self.git(repo, 'push', '-q', 'origin', 'main')
        self.assertEqual(self.checker('--repo', repo).stdout, 'publish-check: clean\n')
        self.commit(repo, 'notes.txt', f'key: {TOKEN}\n', message=f'Add notes for {STRANGER}')
        r = self.checker('--repo', repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn('notes.txt:1: looks like a GitHub token', r.stdout)
        self.assertIn(f"message: another person's email address {STRANGER}", r.stdout)
        self.assertIn('old.txt', self.checker('--repo', repo, '--audit', '5').stdout)

    def test_only_our_own_commits_are_checked(self):
        repo = self.repo()
        self.commit(repo, 'theirs.txt', f'{TOKEN}\n', GIT_AUTHOR_EMAIL='upstream' + '@' + 'other-project.zz')
        self.assertEqual(self.checker('--repo', repo).stdout, 'publish-check: clean\n')

    def test_setup_errors_exit_2_with_what_to_do(self):
        r = subprocess.run([sys.executable, '-B', CHECKER, '--text'], input='x', capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 2)
        self.assertIn('no configuration: give --config FILE or set SPARKY_PUBLISH_CHECK_CONFIG', r.stderr)
        self.configure(never_name=[{'regex': '(unclosed', 'why': 'x'}])
        r = self.checker('--text', stdin='x')
        self.assertEqual(r.returncode, 2)
        self.assertIn('a list is not in the shape config.example.json shows', r.stderr)
        self.configure(never_name=[], our_identities=[])
        r = self.checker('--repo', self.repo())
        self.assertEqual(r.returncode, 2)
        self.assertIn('"our_identities" is empty', r.stderr)


class ToolHook(Case):
    def test_a_push_with_a_secret_asks_the_person(self):
        repo = self.repo()
        self.commit(repo, 'notes.txt', f'key: {TOKEN}\n')
        for command in (f'git -C {repo} push origin main', f'cd {repo} && git push', f'cd {repo} && git push origin HEAD:refs/heads/lane'):
            with self.subTest(command):
                out = self.run_hook(self.bash(command))
                self.assertEqual(self.decision(out), 'ask')
                self.assertIn('notes.txt:1: looks like a GitHub token', self.reason(out))
                self.assertIn('Fix it first, or let the person decide', self.reason(out))
        self.assertIn('looks like a GitHub token', self.log('findings.log'))

    def test_a_clean_push_and_other_git_commands_pass(self):
        repo = self.repo()
        self.commit(repo, 'notes.txt', 'Plain notes.\n')
        self.assertIsNone(self.run_hook(self.bash(f'git -C {repo} push origin main')))
        self.commit(repo, 'more.txt', f'{TOKEN}\n')
        for command in (f'git -C {repo} status', f'git -C {repo} log -p', f'git -C {repo} commit -m "about the push"',
                        f'cat > {self.tmp}/x.md <<\'EOF\'\ngit push origin main\nEOF'):
            with self.subTest(command):
                self.assertIsNone(self.run_hook(self.bash(command)))

    def test_a_push_to_a_private_remote_is_not_checked(self):
        repo = self.repo()
        self.commit(repo, 'notes.txt', f'{TOKEN}\n')
        self.git(repo, 'remote', 'add', 'vault', os.path.join(self.tmp, 'records.private.git'))
        self.assertIsNone(self.run_hook(self.bash(f'git -C {repo} push vault main')))

    def test_text_and_files_of_a_publishing_command_are_checked(self):
        body = testkit.write(os.path.join(self.ws, 'private', 'drafts', 'body.md'), f'Thanks.\nContact {STRANGER}.\n')
        out = self.run_hook(self.bash(f'gh issue comment 5 --repo some/project --body-file {body}'))
        self.assertEqual(self.decision(out), 'ask')
        self.assertIn(f"body.md:2: another person's email address {STRANGER}", self.reason(out))
        heredoc = f'gh pr create --repo some/project --title t --body "$(cat <<\'EOF\'\nA fix.\nIt names {NAMED} here.\nEOF\n)"'
        out = self.run_hook(self.bash(heredoc))
        self.assertEqual(self.decision(out), 'ask')
        self.assertIn('command line 3: names a name that is never published', self.reason(out))

    def test_style_notes_come_back_as_context(self):
        body = testkit.write(os.path.join(self.ws, 'private', 'drafts', 'body.md'), DASH + '\n')
        out = self.run_hook(self.bash(f'gh pr comment 5 --repo some/project --body-file {body}'))
        self.assertIsNone(self.decision(out))
        self.assertIn('Publish check, style notes', self.added_context(out))
        self.assertIn('dash in the middle of a sentence', self.added_context(out))

    def test_a_mail_may_name_its_recipients_in_the_command(self):
        patch = testkit.write(os.path.join(self.tmp, '0001-fix.patch'), 'Subject: fix\n\n+a line\n')
        self.assertIsNone(self.run_hook(self.bash(f'git send-email --to={STRANGER} {patch}')))
        bad = testkit.write(os.path.join(self.tmp, '0002-fix.patch'), f'Subject: fix\n\n+token {TOKEN}\n')
        self.assertEqual(self.decision(self.run_hook(self.bash(f'git send-email --to={STRANGER} {bad}'))), 'ask')

    def test_reading_and_local_commands_are_left_alone(self):
        body = testkit.write(os.path.join(self.tmp, 'body.md'), f'{TOKEN}\n')
        for command in (f'cat {body}', f'gh pr view 5 --repo some/project', f'gh api repos/some/project/pulls/5',
                        f'grep -n token {body}', f'echo "gh pr create" >> {body}'):
            with self.subTest(command):
                self.assertIsNone(self.run_hook(self.bash(command)))

    def test_deny_instead_of_ask_by_configuration_or_where_the_tool_cannot_ask(self):
        body = testkit.write(os.path.join(self.tmp, 'body.md'), f'{TOKEN}\n')
        command = f'gh issue create --repo some/project --title t --body-file {body}'
        self.configure(on_hard_finding='deny')
        self.assertEqual(self.decision(self.run_hook(self.bash(command))), 'deny')
        self.configure(on_hard_finding='ask')
        out = self.run_hook(self.bash(command), dialect='codex')
        self.assertEqual(self.decision(out), 'deny')
        self.assertIn('This tool cannot put the question to the person from a hook', self.reason(out))
        self.configure(ask_becomes='context')
        out = self.run_hook(self.bash(command), dialect='codex')
        self.assertIsNone(self.decision(out))
        self.assertIn('looks like a GitHub token', self.added_context(out))

    def test_a_configured_publishing_command(self):
        self.configure(publish_commands=['\\bpost-note\\b'])
        note = testkit.write(os.path.join(self.tmp, 'note.txt'), f'{TOKEN}\n')
        self.assertEqual(self.decision(self.run_hook(self.bash(f'post-note --file {note}'))), 'ask')


class GitHooks(Case):
    def hooked(self, configured=True):
        repo = self.repo()
        self.git(repo, 'config', 'core.hooksPath', os.path.join(FOLDER, 'git'))
        if configured:
            self.git(repo, 'config', 'sparky.publishCheckConfig', self.config)
        return repo

    def test_a_clean_commit_passes(self):
        r = self.commit(self.hooked(), 'page.md', 'A clean page.\n')
        self.assertEqual((r.returncode, r.stderr), (0, ''))

    def test_private_record_is_refused_even_without_a_configuration(self):
        repo = self.hooked(configured=False)
        for name in ('evidence/run1.log', 'captures/left.png', 'REPORT.md', 'docs/REPORT-round2.md'):
            with self.subTest(name):
                r = self.commit(repo, name, 'x\n')
                self.assertEqual(r.returncode, 1)
                self.assertIn('private record staged', r.stderr)
                self.assertIn('git restore --staged', r.stderr)
                self.git(repo, 'reset', '-q', 'HEAD', '--', name)

    def test_a_staged_secret_is_refused_and_no_verify_passes(self):
        repo = self.hooked()
        r = self.commit(repo, 'notes.txt', f'key: {TOKEN}\n')
        self.assertEqual(r.returncode, 1)
        self.assertIn('STOP  notes.txt:1: looks like a GitHub token', r.stderr)
        self.assertEqual(self.git(repo, 'commit', '-q', '--no-verify', '-m', 'looked at').returncode, 0)

    def test_the_staged_version_is_what_is_checked(self):
        repo = self.hooked()
        testkit.write(os.path.join(repo, 'notes.txt'), 'clean\n')
        self.git(repo, 'add', 'notes.txt')
        testkit.write(os.path.join(repo, 'notes.txt'), f'{TOKEN}\n')  # the working copy changed after staging
        self.assertEqual(self.git(repo, 'commit', '-q', '-m', 'staged clean', check=False).returncode, 0)

    def test_addresses_in_provenance_files_stay(self):
        repo = self.hooked()
        r = self.commit(repo, 'debian/copyright', f'Files: *\nCopyright: 2020 Jane Roe <{STRANGER}>\n')
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.commit(repo, 'README.txt', f'Ask {STRANGER}.\n')
        self.assertEqual(r.returncode, 1)

    def test_the_message_is_checked(self):
        repo = self.hooked()
        r = self.commit(repo, 'a.txt', 'a\n', message=f'Fix it\n\nAs asked by {STRANGER}')
        self.assertEqual(r.returncode, 1)
        self.assertIn('commit-msg: the publish check found', r.stderr)
        r = self.git(repo, 'commit', '-q', '-m', 'Fix it\n\nReviewed-by: Jane Roe <' + STRANGER + '>', check=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_without_a_configuration_the_commit_goes_ahead_and_says_so(self):
        r = self.commit(self.hooked(configured=False), 'notes.txt', f'{TOKEN}\n')
        self.assertEqual(r.returncode, 0)
        self.assertIn('pre-commit: the publish check did not run: no configuration', r.stderr)
        self.assertIn('commit-msg: the publish check did not run: no configuration', r.stderr)
        self.assertIn('The commit goes ahead unchecked', r.stderr)

    def test_a_broken_configuration_lets_the_commit_through_and_says_so(self):
        repo = self.hooked()
        with open(self.config, 'w') as f:
            f.write('{broken')
        r = self.commit(repo, 'notes.txt', 'clean\n')
        self.assertEqual(r.returncode, 0)
        self.assertIn('cannot be read', r.stderr)
        self.assertIn('The commit goes ahead unchecked', r.stderr)

    def test_switched_off(self):
        repo = self.hooked()
        self.configure(enabled=False)
        r = self.commit(repo, 'notes.txt', f'{TOKEN}\n', message=f'for {STRANGER}')
        self.assertEqual((r.returncode, r.stderr), (0, ''))


if __name__ == '__main__':
    unittest.main()
