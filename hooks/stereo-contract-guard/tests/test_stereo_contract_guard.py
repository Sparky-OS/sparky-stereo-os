#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the stereo-contract-guard hook. Run: python3 hooks/tests/run.py stereo-contract-guard

The sentences that break the contract are put together while the test runs from the word lists below, so that this
file holds no sentence a contract check would stop: the guard would otherwise refuse its own tests.
"""
import os
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import testkit  # noqa: E402

FORMAT = 'ana' + 'glyph'
PLURAL = 'mo' + 'des'
SAID = 'decl' + 'ared'
SAYS = 'decl' + 'ares'
BROKEN = {
    'program_output_modes': [
        f'The player gets a red and cyan {FORMAT} view in its View menu.',
        f'Add an {FORMAT} preview button to the editor.',
        f'An {FORMAT} option is offered in the settings of the player.',
    ],
    'keeping_own_modes': [
        f'The player keeps its own output {PLURAL} beside the pair.',
        f'The player leaves its other stereo {PLURAL} in the menu.',
    ],
    'declaration': [
        f'The surface is {SAID} as half side by side.',
        f'The player {SAYS} top and bottom to the compositor.',
        f'The window is {SAID} right eye first.',
    ],
}
ALLOWED = [
    f'The player detects an {FORMAT} picture and rebuilds the pair.',
    f'{FORMAT.capitalize()} is input only in a program.',
    f'Stereo KWin makes the {FORMAT} output for any monitor.',
    f'The virtual {FORMAT} monitor is the compositor\'s.',
    f'A program never offers an {FORMAT} view.',
    f'There is no {FORMAT} mode in the player.',
    f'The player\'s own output {PLURAL} go in the edition\'s build.',
    f'Its own {PLURAL} are removed, and the desktop gives every output.',
    'A half side by side file is unpacked and the pair is declared as full side by side.',
    'The declaration is never half or top and bottom.',
    'The file declares top and bottom, which the reader converts.',
    'Dark mode follows the system.',
]
NAMES = {'program_output_modes': 'a program offering an output format', 'keeping_own_modes': 'a program keeping its own output modes',
         'declaration': 'a declaration other than full side by side'}


class Case(testkit.HookCase):
    hook = 'stereo-contract-guard'

    def write_brief(self, text, lane='some-lane', name='BRIEF.md', tool='Write'):
        path = os.path.join(self.ws, 'partners', 'queue', lane, name)
        key = 'content' if tool == 'Write' else 'new_string'
        return self.event('PreToolUse', tool, {'file_path': path, key: text})


class Text(Case):
    def test_each_broken_sentence_is_put_to_the_person_with_its_rule_and_fix(self):
        for check, sentences in BROKEN.items():
            for sentence in sentences:
                with self.subTest(sentence):
                    out = self.run_hook(self.write_brief(f'# Brief\n\nSome context.\n{sentence}\nMore text.\n'))
                    self.assertEqual(self.decision(out), 'ask')
                    reason = self.reason(out)
                    self.assertIn(NAMES[check], reason)
                    self.assertIn(sentence[:60], reason)
                    self.assertIn('Not compliant:', reason)
                    self.assertIn('Fix:', reason)

    def test_sentences_within_the_contract_pass(self):
        for sentence in ALLOWED:
            with self.subTest(sentence):
                self.assertIsNone(self.run_hook(self.write_brief(f'# Brief\n\n{sentence}\n')))

    def test_an_edit_and_a_draft_are_checked_too(self):
        self.assertEqual(self.decision(self.run_hook(self.write_brief(BROKEN['declaration'][0], tool='Edit'))), 'ask')
        draft = os.path.join(self.ws, 'private', 'drafts', 'issue.md')
        out = self.run_hook(self.event('PreToolUse', 'Write', {'file_path': draft, 'content': BROKEN['keeping_own_modes'][0]}))
        self.assertEqual(self.decision(out), 'ask')

    def test_files_elsewhere_are_not_this_guard_s_business(self):
        for path in (os.path.join(self.ws, 'repos', 'project', 'README.md'), os.path.join(self.ws, 'memory', 'note.md')):
            with self.subTest(path):
                self.assertIsNone(self.run_hook(self.event('PreToolUse', 'Write', {'file_path': path, 'content': BROKEN['program_output_modes'][0]})))

    def test_a_brief_written_by_the_shell_is_checked(self):
        path = os.path.join(self.ws, 'partners', 'queue', 'some-lane', 'BRIEF.md')
        command = f"cat >> {path} <<'EOF'\n{BROKEN['program_output_modes'][0]}\nEOF"
        self.assertEqual(self.decision(self.run_hook(self.bash(command))), 'ask')
        elsewhere = f"cat >> {self.tmp}/notes.md <<'EOF'\n{BROKEN['program_output_modes'][0]}\nEOF"
        self.assertIsNone(self.run_hook(self.bash(elsewhere)))

    def test_text_about_to_be_published_is_checked_with_the_files_it_sends(self):
        body = testkit.write(os.path.join(self.tmp, 'body.md'), f'Thanks for the review.\n{BROKEN["keeping_own_modes"][1]}\n')
        out = self.run_hook(self.bash(f'gh issue comment 4 --repo some/project --body-file {body}'))
        self.assertEqual(self.decision(out), 'ask')
        self.assertIn('Stereo contract guard, publishing', self.reason(out))
        inline = f'gh pr create --repo some/project --title t --body "{BROKEN["declaration"][1]}"'
        self.assertEqual(self.decision(self.run_hook(self.bash(inline))), 'ask')
        self.assertIsNone(self.run_hook(self.bash(f'gh pr view 4 --repo some/project && cat {body}')))

    def test_each_check_has_a_switch_and_deny_is_a_choice(self):
        for check, sentences in BROKEN.items():
            with self.subTest(check):
                self.configure(checks={'program_output_modes': True, 'keeping_own_modes': True, 'declaration': True, check: False})
                self.assertIsNone(self.run_hook(self.write_brief(sentences[0])))
        self.configure(checks={'program_output_modes': True, 'keeping_own_modes': True, 'declaration': True}, on_finding='deny')
        self.assertEqual(self.decision(self.run_hook(self.write_brief(BROKEN['declaration'][0]))), 'deny')

    def test_words_the_workspace_allows(self):
        sentence = f'The headset bridge shows an {FORMAT} view of its own.'
        self.assertEqual(self.decision(self.run_hook(self.write_brief(sentence))), 'ask')
        self.configure(allow_words=['headset bridge'])
        self.assertIsNone(self.run_hook(self.write_brief(sentence)))


class Push(Case):
    def setUp(self):
        super().setUp()
        self.env = {'PATH': os.environ['PATH'], 'HOME': self.tmp, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_AUTHOR_NAME': 'You',
                    'GIT_AUTHOR_EMAIL': 'you@example.org', 'GIT_COMMITTER_NAME': 'You', 'GIT_COMMITTER_EMAIL': 'you@example.org'}

    def repo(self, name):
        path = os.path.join(self.ws, 'repos', name)
        bare = os.path.join(self.tmp, name + '.git')
        subprocess.run(['git', 'init', '-q', '--bare', bare], check=True, env=self.env)
        subprocess.run(['git', 'init', '-q', '-b', 'main', path], check=True, env=self.env)
        self.git(path, 'remote', 'add', 'origin', bare)
        self.commit(path, 'README.md', '# Project\n')
        self.git(path, 'push', '-q', 'origin', 'main')
        return path

    def git(self, repo, *args):
        subprocess.run(['git', '-C', repo, *args], check=True, capture_output=True, env=self.env)

    def commit(self, repo, name, text):
        testkit.write(os.path.join(repo, name), text)
        self.git(repo, 'add', name)
        self.git(repo, 'commit', '-q', '-m', 'Add ' + name)

    def test_output_mode_code_in_a_program_is_stopped(self):
        repo = self.repo('player')
        self.commit(repo, 'menu.cpp', 'void setup() {\n    menu->addAction("Side by side");\n    ' + f'set_{FORMAT}_mode(true);\n' + '}\n')
        out = self.run_hook(self.bash(f'git -C {repo} push origin main'))
        self.assertEqual(self.decision(out), 'ask')
        self.assertIn('output-mode code in commit', self.reason(out))
        self.assertIn('Stereo contract guard, a git push', self.reason(out))

    def test_the_display_stack_may_carry_output_code(self):
        repo = self.repo('kwin')
        self.commit(repo, 'output.cpp', f'void {FORMAT}_output() {{}}\n')
        self.assertIsNone(self.run_hook(self.bash(f'git -C {repo} push origin main')))

    def test_input_code_and_pushed_commits_pass(self):
        repo = self.repo('player')
        self.commit(repo, 'reader.cpp', f'bool detect_{FORMAT}_picture(const Image &);\n')
        self.assertIsNone(self.run_hook(self.bash(f'cd {repo} && git push')))
        self.commit(repo, 'menu.cpp', f'{FORMAT}_enabled = true;\n')
        self.git(repo, 'push', '-q', 'origin', 'main')
        self.assertIsNone(self.run_hook(self.bash(f'git -C {repo} push origin main')))

    def test_lane_notes_in_the_tip_are_stopped_and_removed_ones_are_not(self):
        repo = self.repo('library')
        self.commit(repo, 'REPORT.md', 'STATUS: review\n')
        self.commit(repo, 'evidence/run.log', 'ok\n')
        out = self.run_hook(self.bash(f'git -C {repo} push origin main'))
        self.assertEqual(self.decision(out), 'ask')
        self.assertIn('lane notes in the pushed tip: REPORT.md, evidence/run.log', self.reason(out))
        for command in (f'# send it\ngit -C {repo} push origin main', f'git -C {repo} \\\n  push origin main',
                        f'for b in main; do git -C {repo} push origin $b; done', f'bash -lc "git -C {repo} push origin main"'):
            with self.subTest(command):
                self.assertEqual(self.decision(self.run_hook(self.bash(command))), 'ask')
        self.git(repo, 'rm', '-q', 'REPORT.md', 'evidence/run.log')
        self.git(repo, 'commit', '-q', '-m', 'Remove the lane notes')
        self.assertIsNone(self.run_hook(self.bash(f'git -C {repo} push origin main')))

    def test_other_git_commands_and_text_that_only_names_a_push_pass(self):
        repo = self.repo('player')
        self.commit(repo, 'menu.cpp', f'set_{FORMAT}_mode(true);\n')
        for command in (f'git -C {repo} log -p', f'git -C {repo} commit --amend -m "before the push"',
                        f"cat > {self.tmp}/plan.md <<'EOF'\ncd {repo} && git push origin main\nEOF"):
            with self.subTest(command):
                self.assertIsNone(self.run_hook(self.bash(command)))


if __name__ == '__main__':
    unittest.main()
