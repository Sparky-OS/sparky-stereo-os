#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the outreach-guard hook. Run: python3 hooks/tests/run.py outreach-guard"""
import json
import os
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import testkit  # noqa: E402

CONSULT = 'mcp__reference__consult_knowledge'


class Case(testkit.HookCase):
    hook = 'outreach-guard'

    def setUp(self):
        super().setUp()
        self.outreach = os.path.join(self.ws, 'repos', 'sparky-stereo-os', 'skills', 'upstream-outreach', 'SKILL.md')
        self.ffmpeg = os.path.join(self.ws, 'repos', 'sparky-stereo-os', 'skills', 'contrib-ffmpeg', 'SKILL.md')
        self.voice = self.memory('how-we-write-upstream.md')
        self.configure(own_owners=['Our-Org', 'our-user'], own_repos=['sparky-stereo-os', 'our-library'])

    def repo(self, name, **remotes):
        """A git repository in the toy workspace with the remotes given as name=address."""
        path = os.path.join(self.ws, 'repos', name)
        env = {'PATH': os.environ['PATH'], 'HOME': self.tmp, 'GIT_CONFIG_NOSYSTEM': '1'}
        subprocess.run(['git', 'init', '-q', path], check=True, env=env)
        for remote, url in remotes.items():
            subprocess.run(['git', '-C', path, 'remote', 'add', remote, url], check=True, env=env)
        return path

    def consult(self, **kw):
        return self.event('PostToolUse', CONSULT, {'query': 'x', 'collections': 'y'}, **kw)

    def do_reading(self, *paths, **kw):
        for path in paths:
            self.assertIsNone(self.run_hook(self.read(path, **kw)))

    def refused(self, command, **kw):
        out = self.run_hook(self.bash(command, **kw))
        self.assertEqual(self.decision(out), 'deny', command)
        return self.reason(out)

    def passes(self, command, **kw):
        out = self.run_hook(self.bash(command, **kw))
        self.assertIsNone(self.decision(out), command)
        return out


class Sequence(Case):
    def test_refuse_read_consult_pass(self):
        command = 'gh pr create --repo FFmpeg/FFmpeg --title "avcodec: x" --body-file body.md'
        # 1. refused, with everything that is missing
        reason = self.refused(command)
        self.assertIn('this command is a pull request, issue, comment or forge write on a repository that is not ours', reason)
        for needed in (self.outreach, self.voice, self.ffmpeg, f'Consulted the reference index for this subject ({CONSULT})',
                       'within the last 4 hours', 'Then send the same command again.'):
            self.assertIn(needed, reason)
        # 2. the files are read: only the consult is still missing
        self.do_reading(self.outreach, self.voice, self.ffmpeg)
        reason = self.refused(command)
        self.assertNotIn('Read in full', reason)
        self.assertIn('Consulted the reference index', reason)
        # 3. the consult: the same command passes, with the checklist
        self.assertIsNone(self.run_hook(self.consult()))
        out = self.passes(command)
        self.assertIn('One subject per pull or merge request', self.added_context(out))
        self.assertIn('rule by rule against the project\'s contrib skill', self.added_context(out))
        # the logs tell the same story
        self.assertEqual(self.log('refused.log').count('gh pr create'), 2)
        self.assertEqual(self.log('passed.log').count('gh pr create'), 1)

    def test_the_window_closes(self):
        command = 'gh issue comment 12 --repo mpv-player/mpv --body hello'
        self.do_reading(self.outreach, self.voice)
        self.run_hook(self.consult())
        self.passes(command)
        folder = os.path.join(self.ws, 'state', 'hooks', self.hook)
        path = [os.path.join(folder, n) for n in os.listdir(folder) if n.endswith('.json')][0]
        with open(path) as f:
            state = json.load(f)
        state['consult'] -= 14401
        state['read'] = {k: v - 14401 for k, v in state['read'].items()}
        with open(path, 'w') as f:
            json.dump(state, f)
        reason = self.refused(command)
        self.assertIn(self.outreach, reason)
        self.assertIn('Consulted the reference index', reason)

    def test_a_partial_read_and_another_session_do_not_count(self):
        command = 'gh pr comment 3 --repo HandBrake/HandBrake --body x'
        self.run_hook(self.read(self.outreach, tool_input={'limit': 40}))
        self.do_reading(self.voice)
        self.run_hook(self.consult())
        self.assertIn(self.outreach, self.refused(command))
        self.do_reading(self.outreach, session='other')
        self.assertIn(self.outreach, self.refused(command))

    def test_a_lane_has_its_own_reading(self):
        command = 'gh pr comment 3 --repo HandBrake/HandBrake --body x'
        self.do_reading(self.outreach, self.voice)
        self.run_hook(self.consult())
        self.passes(command)
        self.refused(command, agent='agent-5')

    def test_a_file_the_configuration_names_but_does_not_exist_is_not_demanded_and_is_said(self):
        self.configure(always_read=['memory/absent.md', 'memory/how-we-write-upstream.md'])
        command = 'gh issue create --repo someone/project --title t'
        absent = 'Not asked for, because the file does not exist: ' + self.memory('absent.md')
        reason = self.refused(command)
        self.assertIn(absent, reason)
        self.assertNotIn('- ' + self.memory('absent.md'), reason)
        self.do_reading(self.voice)
        self.run_hook(self.consult())
        self.assertIn(absent, self.added_context(self.passes(command)))
        self.assertEqual(self.log('errors.log').count('does not exist, so it is not demanded'), 1)

    def test_without_a_consult_tool_or_with_the_switch_off_no_consult_is_asked(self):
        self.do_reading(self.outreach, self.voice)
        command = 'gh issue create --repo someone/project --title t'
        self.assertIn('Consulted the reference index', self.refused(command))
        self.configure(require_consult=False)
        self.passes(command)
        self.configure(require_consult=True, consult_tools=[])
        self.passes(command)


class WhatGoesOut(Case):
    def test_commands_that_send_something_to_another_project(self):
        fork = self.repo('ffmpeg', origin='https://github.com/Our-Org/FFmpeg.git', upstream='https://code.ffmpeg.org/FFmpeg/FFmpeg.git')
        cases = {
            'gh pr create --title t': 'a pull request',
            'gh issue comment 5 --repo other/project --body b': 'a pull request',
            'gh pr review 9 -R other/project --approve': 'a pull request',
            'gh api repos/other/project/issues/1/comments -f body=hello': 'forge write',
            'gh api -X DELETE repos/other/project/issues/comments/9': 'forge write',
            'curl -s -X POST https://code.ffmpeg.org/api/v1/repos/FFmpeg/FFmpeg/issues/1/comments -d @body.json': "a write to another project's forge",
            'curl --json @x.json https://invent.kde.org/api/v4/projects/1/merge_requests': "a write to another project's forge",
            'git send-email --to=list@example.org 0001-x.patch': 'a mail',
            'reportbug --ui text -b somepackage': 'a bug report by mail',
            f'git -C {fork} push origin fix-branch': 'a push to a fork of another project',
            f'cd {fork} && git push --force-with-lease origin fix-branch': 'a push to a fork of another project',
            f'git -C {fork} push -o ci.skip origin fix-branch': 'a push to a fork of another project',
            f'git -C {fork} push -u -o ci.skip upstream fix-branch': "a push to another project's forge",
            f'git -C {fork} push upstream fix-branch': "a push to another project's forge",
            'git push https://github.com/Our-Org/kwin.git stereo3d': 'a push to a fork of another project',
            'git push git@invent.kde.org:someone/kwin.git work': "a push to another project's forge",
            f'GIT_SSH_COMMAND="ssh -i key" timeout 60 git -C {fork} push origin x': 'a push to a fork of another project',
            f'bash -c "git -C {fork} push origin x"': 'a push to a fork of another project',
            f'bash <<\'EOF\'\ngit -C {fork} push origin x\nEOF': 'a push to a fork of another project',
            f'echo start; git -C {fork} push origin x || echo failed': 'a push to a fork of another project',
        }
        for command, why in cases.items():
            with self.subTest(command):
                self.assertIn(why, self.refused(command))

    def test_the_contrib_skill_is_found_from_the_remote_s_address(self):
        fork = self.repo('ffmpeg', origin='https://github.com/Our-Org/FFmpeg.git', upstream='https://code.ffmpeg.org/FFmpeg/FFmpeg.git')
        self.assertIn(self.ffmpeg, self.refused(f'git -C {fork} push upstream fix'))

    def test_our_own_repositories_pass(self):
        own = self.repo('our-library', origin='git@github.com:Our-Org/our-library.git')
        local = self.repo('scratch', origin=os.path.join(self.tmp, 'bare.git'))
        for command in (
            f'git -C {own} push origin main',
            f'cd {own} && git push',
            f'cd {own} && gh pr create --title t --body b',
            'git push https://github.com/our-user/sparky-stereo-os.git lane-branch',
            'gh pr create --repo Our-Org/kwin --title "CI only"',
            'gh api repos/our-user/our-library/pulls -f title=t',
            'curl -X POST https://api.github.com/repos/Our-Org/our-library/issues -d @i.json',
            f'git -C {local} push origin main',
        ):
            with self.subTest(command):
                self.assertIsNone(self.run_hook(self.bash(command)))

    def test_reading_and_local_work_pass(self):
        fork = self.repo('ffmpeg', origin='https://github.com/Our-Org/FFmpeg.git')
        for command in (
            'gh pr view 5 --repo FFmpeg/FFmpeg', 'gh pr list -R other/project', 'gh issue view 3 --repo other/project --comments',
            'gh api repos/other/project/pulls/5', 'gh pr checks 5 --repo other/project', 'gh pr diff 5 -R other/project',
            'curl -s https://code.ffmpeg.org/api/v1/repos/FFmpeg/FFmpeg/pulls/1', 'curl -sL https://invent.kde.org/plasma/kwin/-/raw/master/README.md -o r.md',
            f'git -C {fork} fetch origin', f'git -C {fork} log --oneline origin/master..HEAD', f'git -C {fork} status',
            f'git -C {fork} commit -m "explain the push to the fork and to upstream"',
            'git format-patch -3 -o patches', 'reportbug --ui text -o report.eml -b somepackage',
            'grep -rn "git push fork" docs/', 'echo "gh pr create --repo FFmpeg/FFmpeg" >> notes.md',
        ):
            with self.subTest(command):
                self.assertIsNone(self.run_hook(self.bash(command)))

    def test_text_written_to_a_file_is_not_a_command(self):
        heredoc = "cat > notes/plan.md <<'EOF'\nThen: git push fork order-7 and gh pr create --repo FFmpeg/FFmpeg\nEOF"
        self.assertIsNone(self.run_hook(self.bash(heredoc)))
        python = "python3 - <<'PY'\nimport re\nPUSH = re.compile(r'git push fork')\nprint(\"it's fine\")\nPY"
        self.assertIsNone(self.run_hook(self.bash(python)))
        tee = "tee -a log.txt <<EOF\ngit send-email --to=x@example.org\nEOF"
        self.assertIsNone(self.run_hook(self.bash(tee)))

    def test_text_handed_to_a_shell_is_a_command(self):
        fork = self.repo('ffmpeg', origin='https://github.com/Our-Org/FFmpeg.git')
        piped = f"cat <<'EOF' | sh\ngit -C {fork} push origin x\nEOF"
        self.assertIn('a push to a fork of another project', self.refused(piped))

    def test_a_send_is_seen_in_every_form_a_shell_runs_it(self):
        fork = self.repo('ffmpeg', origin='https://github.com/Our-Org/FFmpeg.git')
        send = f'git -C {fork} push origin x'
        post = 'curl -X POST https://code.ffmpeg.org/api/v1/repos/FFmpeg/FFmpeg/issues/1/comments'
        cases = {
            'a comment line first': f'# send the branch\n{send}',
            'a comment after another command': f'cd /tmp  # elsewhere\n{send}',
            'a comment with an apostrophe first': f"# here's the reply\n{post} -d @body.json",
            'continuation lines': f'curl -sS -X POST \\\n  -H "Accept: application/json" \\\n  {post.split()[-1]} \\\n  -d @body.json',
            'a send on continuation lines': send.replace(' push', ' \\\n  push'),
            'a loop': f'for b in one two; do {send}; done',
            'a loop on lines': f'for b in one two\ndo\n  {send}\ndone',
            'a condition': f'if {send}; then echo sent; fi',
            'a then branch': f'if test -d /tmp; then {send}; fi',
            'an else branch': f'if test -d /nowhere; then echo no; else {send}; fi',
            'a while loop': f'while ! {send}; do sleep 5; done',
            'braces': f'{{ {send}; }}',
            'a negation': f'! {send}',
            'backticks': f'echo `{send}`',
            'a substitution in double quotes': f'echo "$({send})"',
            'an assignment from a substitution': f'out=$({send}) && echo "$out"',
            'a login shell': f'bash -lc "{send}"',
            'after a quoted shift sign': f'echo "1 << 3 is 8"\n{send}',
            'after arithmetic': f'echo $((1 << 3))\n{send}',
            'ANSI-C quoting': post + " --data $'it\\'s done'",
            'a hash inside a word': f'echo issue#12 && {send}',
            'a function body': f'send() {{ {send}; }}; send',
            'a here-document read by a shell, after a comment': f"# run it\nbash <<'EOF'\n{send}\nEOF",
        }
        for name, command in cases.items():
            with self.subTest(name):
                self.refused(command)

    def test_text_a_command_only_carries_is_not_a_send(self):
        cases = {
            'a comment that names a send': '# later: git push fork branch\nls',
            'a comment after a command': 'ls  # then gh pr create --repo other/project',
            'a hash inside a quoted word': 'echo "see #12: git push fork branch"',
            'a variable holding the words': "note='gh pr create --repo other/project'; echo \"$note\"",
            'continuation lines of a read': 'curl -s \\\n  https://code.ffmpeg.org/api/v1/repos/FFmpeg/FFmpeg/pulls/1',
            'a message from a here-document': "git commit -F - <<'EOF'\nexplain: don't git push fork (yet), \"quoted\"\nEOF",
            'a message from a substitution': 'git commit -m "$(cat <<\'EOF\'\nwhy we do not gh pr create --repo other/project (yet): it\'s early\nEOF\n)"',
            'a here-document piped to a file writer': "cat <<'EOF' | tee plan.md\ngit push fork branch\nEOF",
        }
        for name, command in cases.items():
            with self.subTest(name):
                self.assertIsNone(self.run_hook(self.bash(command)))

    def test_without_git_s_answer_the_remote_s_name_decides(self):
        self.configure(resolve_remotes=False)
        self.assertIn('a push to a fork remote', self.refused('git push fork branch'))
        self.assertIn('a push to a fork remote', self.refused('git push -u upstream branch'))
        self.assertIsNone(self.run_hook(self.bash('git push origin branch')))

    def test_a_line_that_cannot_be_read_as_shell_is_judged_by_its_text(self):
        self.assertIn('a pull request', self.refused('gh pr create --repo other/project --title "unbalanced'))
        self.assertIn('forge write', self.refused('gh api -X POST repos/other/project/issues -f title="cut here'))
        cut = 'curl -X POST https://code.ffmpeg.org/api/v1/repos/FFmpeg/FFmpeg/issues/1/comments -H "Authorization: token'
        self.assertIn("a write to another project's forge", self.refused(cut))
        self.assertIn('a bug report by mail', self.refused('reportbug somepackage --subject "cut here'))
        self.assertIsNone(self.run_hook(self.bash('reportbug -o report.eml somepackage --subject "cut here')))
        self.assertIsNone(self.run_hook(self.bash('curl -s https://code.ffmpeg.org/api/v1/repos/FFmpeg/FFmpeg/pulls/1 -H "cut here')))
        self.assertIsNone(self.run_hook(self.bash('curl -X POST https://api.github.com/repos/Our-Org/our-library/issues -d "cut here')))
        self.assertIsNone(self.run_hook(self.bash('echo "unbalanced quote and nothing else')))

    def test_other_tools_and_other_events_are_left_alone(self):
        self.assertIsNone(self.run_hook(self.event('PreToolUse', 'Write', {'file_path': '/x', 'content': 'gh pr create'})))
        self.assertIsNone(self.run_hook(self.event('UserPromptSubmit', prompt='gh pr create --repo a/b')))

    def test_switched_off(self):
        self.configure(enabled=False)
        self.assertIsNone(self.run_hook(self.bash('gh pr create --repo other/project --title t')))


class Codex(Case):
    dialect = 'codex'

    def test_reading_with_cat_counts(self):
        command = 'gh pr create --repo FFmpeg/FFmpeg --title t'
        self.assertEqual(self.decision(self.run_hook(self.bash(command))), 'deny')
        self.run_hook(self.bash(f'cat {self.outreach} {self.voice}', phase='PostToolUse'))
        self.run_hook(self.bash(f'cat {self.ffmpeg}', phase='PostToolUse'))
        self.run_hook(self.consult())
        self.assertIsNone(self.decision(self.run_hook(self.bash(command))))
        self.run_hook(self.bash(f'head -5 {self.outreach}', phase='PostToolUse', session='b'))
        self.assertEqual(self.decision(self.run_hook(self.bash(command, session='b'))), 'deny')


if __name__ == '__main__':
    unittest.main()
