#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the shared code: how a shell line is read, how an answer is written for each tool, and the design lookup.
Run: python3 hooks/tests/run.py hookkit"""
import os
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib')
sys.path.insert(0, LIB)
import design_lookup  # noqa: E402
import hookkit  # noqa: E402

PUSH = ['git', 'push', 'fork', 'branch']


class ReadingShell(unittest.TestCase):
    def test_simple_commands_are_split_and_unwrapped(self):
        cases = {
            'cd repo && git push fork branch': [['cd', 'repo'], PUSH],
            'git status; git push fork branch || echo failed': [['git', 'status'], PUSH, ['echo', 'failed']],
            'A=1 B="two words" git push fork branch': [PUSH],
            'timeout 60 env X=1 git push fork branch': [PUSH],
            'sudo -u builder nice -n 5 git push fork branch': [PUSH],
            'ls | xargs -n 1 git push fork branch': [['ls'], PUSH],
            'bash -c "git push fork branch"': [PUSH],
            "sh -c 'cd repo && git push fork branch'": [['cd', 'repo'], PUSH],
            'eval git push fork branch': [PUSH],
            'echo start\ngit push fork branch': [['echo', 'start'], PUSH],
            'git push fork branch > log.txt 2>&1': [PUSH],
            '(cd repo; git push fork branch)': [['cd', 'repo'], PUSH],
            'echo $(git push fork branch)': [['echo', '$(...)'], PUSH],
        }
        for line, want in cases.items():
            with self.subTest(line):
                self.assertEqual(hookkit.shell_commands(line), want)

    def test_valid_shell_that_a_word_splitter_gets_wrong(self):
        message = 'git commit -m "$(cat <<\'EOF\'\nit\'s (a message) with "quotes"\nEOF\n)" && git push fork branch'
        cases = {
            '# a comment first\ngit push fork branch': [PUSH],
            "# here's a comment with an apostrophe\ngit push fork branch": [PUSH],
            'cd repo  # a comment after a command\ngit push fork branch': [['cd', 'repo'], PUSH],
            'ls  # only named in a comment: git push fork branch': [['ls']],
            'git push \\\n  fork branch': [PUSH],
            'for b in one two; do git push fork branch; done': [['for', 'b', 'in', 'one', 'two'], PUSH],
            'for b in one two\ndo\n  git push fork branch\ndone': [['for', 'b', 'in', 'one', 'two'], PUSH],
            'if git push fork branch; then echo ok; fi': [PUSH, ['echo', 'ok']],
            'if test -d repo; then echo no; else git push fork branch; fi': [['test', '-d', 'repo'], ['echo', 'no'], PUSH],
            'while ! git push fork branch; do sleep 5; done': [PUSH, ['sleep', '5']],
            '{ git push fork branch; }': [PUSH],
            'send() { git push fork branch; }; send': [['send'], PUSH, ['send']],
            'echo `git push fork branch`': [['echo', '`...`'], PUSH],
            'echo "$(git push fork branch)"': [['echo', '$(...)'], PUSH],
            'echo "`git push fork branch`"': [['echo', '`...`'], PUSH],
            'out=$(git push fork branch) && echo "$out"': [PUSH, ['echo', '$out']],
            'bash -lc "git push fork branch"': [PUSH],
            "bash -ec 'cd repo && git push fork branch'": [['cd', 'repo'], PUSH],
            'echo "1 << 3 is 8"\ngit push fork branch': [['echo', '1 << 3 is 8'], PUSH],
            'echo $((1 << 3))\ngit push fork branch': [['echo', '$((1 << 3))'], PUSH],
            "python3 -c 'print(1 << 3)'\ngit push fork branch": [['python3', '-c', 'print(1 << 3)'], PUSH],
            "echo $'it\\'s' && git push fork branch": [['echo', "it's"], PUSH],
            'echo issue#12 ${x#prefix} $# && git push fork branch': [['echo', 'issue#12', '${x#prefix}', '$#'], PUSH],
            'diff <(git push fork branch) notes.txt': [['diff'], PUSH, ['notes.txt']],
            message: [['git', 'commit', '-m', '$(...)'], ['cat'], PUSH],
            'echo "see #12: git push fork branch"': [['echo', 'see #12: git push fork branch']],
            "note='git push fork branch'; echo \"$note\"": [['echo', '$note']],
        }
        for line, want in cases.items():
            with self.subTest(line):
                self.assertEqual(hookkit.shell_commands(line), want)
        for line in ('echo $(git push fork branch', 'echo `git push fork branch', "echo $'unclosed"):
            with self.subTest(line):
                self.assertIsNone(hookkit.shell_commands(line))

    def test_what_begins_a_comment(self):
        # the six lines of the Advanced Bash-Scripting Guide, chapter 3 "Special Characters", on the # character
        cases = {
            'echo "The # here does not begin a comment."': [['echo', 'The # here does not begin a comment.']],
            "echo 'The # here does not begin a comment.'": [['echo', 'The # here does not begin a comment.']],
            'echo The \\# here does not begin a comment.': [['echo', 'The', '#', 'here', 'does', 'not', 'begin', 'a', 'comment.']],
            'echo The # here begins a comment.': [['echo', 'The']],
            'echo ${PATH#*:}       # Parameter substitution, not a comment.': [['echo', '${PATH#*:}']],
            'echo $(( 2#101011 ))  # Base conversion, not a comment.': [['echo', '$(( 2#101011 ))']],
        }
        for line, want in cases.items():
            with self.subTest(line):
                self.assertEqual(hookkit.shell_commands(line), want)

    def test_the_text_a_command_only_carries_is_left_out(self):
        line = ("ls  # a comment: git push fork branch\ncat > plan.md <<'EOF'\ngit push fork branch\nEOF\n"
                "curl -s \\\n  example.org\nbash <<'SH'\necho kept  # dropped\nSH")
        self.assertEqual(hookkit.acting_text(line),
                         "ls  \ncat > plan.md <<'EOF'\nEOF\ncurl -s   example.org\nbash <<'SH'\necho kept  \nSH")
        self.assertEqual(hookkit.acting_text('echo "unclosed # not a comment'), 'echo "unclosed # not a comment')

    def test_text_in_quotes_is_one_word_not_a_command(self):
        got = hookkit.shell_commands('git commit -m "explain the git push to the fork" && echo ok')
        self.assertEqual(got, [['git', 'commit', '-m', 'explain the git push to the fork'], ['echo', 'ok']])

    def test_a_here_document_is_commands_only_when_a_shell_reads_it(self):
        written = "cat > plan.md <<'EOF'\ngit push fork branch\nEOF\necho done"
        self.assertEqual(hookkit.shell_commands(written), [['cat'], ['echo', 'done']])
        python = "python3 - <<'PY'\nprint(\"it's a git push fork\")\nPY"
        self.assertEqual(hookkit.shell_commands(python), [['python3', '-']])
        for line in ("bash <<'EOF'\ngit push fork branch\nEOF", "bash -s <<EOF\ngit push fork branch\nEOF",
                     "cat <<'EOF' | sh\ngit push fork branch\nEOF", "sudo sh <<-EOF\n\tgit push fork branch\n\tEOF"):
            with self.subTest(line):
                self.assertIn(PUSH, hookkit.shell_commands(line))

    def test_a_line_that_is_not_shell_gives_none(self):
        self.assertIsNone(hookkit.shell_commands('echo "unbalanced'))

    def test_git_subcommand_skips_git_s_own_options(self):
        self.assertEqual(hookkit.git_subcommand(['git', '-C', '/x', '-c', 'a=b', 'push', 'origin'])[0], 'push')
        self.assertEqual(hookkit.git_subcommand(['git', '--no-pager', 'log', '-p']), ('log', ['-p']))
        self.assertEqual(hookkit.git_subcommand(['git']), (None, []))
        self.assertEqual(hookkit.git_subcommand(['echo', 'git', 'push']), (None, []))
        self.assertEqual(hookkit.push_places(['-u', '-o', 'ci.skip', '--force-with-lease', 'origin', 'HEAD:refs/heads/x']),
                         ['origin', 'HEAD:refs/heads/x'])
        self.assertEqual(hookkit.push_places(['--all']), [])
        self.assertEqual(hookkit.git_folder(['git', '-C', 'sub', 'push'], '/work'), '/work/sub')
        self.assertEqual(hookkit.git_folder(['git', 'push'], '/work'), '/work')


class Events(unittest.TestCase):
    def event(self, dialect='claude', **payload):
        payload.setdefault('cwd', '/work')
        return hookkit.Event(payload, dialect)

    def test_claude_s_tools_in_plain_terms(self):
        e = self.event(hook_event_name='PreToolUse', tool_name='Bash', tool_input={'command': 'ls'})
        self.assertEqual((e.kind, e.tool, e.command), ('before-tool', 'shell', 'ls'))
        e = self.event(hook_event_name='PostToolUse', tool_name='Read', tool_input={'file_path': '/m/a.md'})
        self.assertEqual((e.kind, e.tool, e.reads()), ('after-tool', 'read', ['/m/a.md']))
        e = self.event(hook_event_name='PostToolUse', tool_name='Read', tool_input={'file_path': '/m/a.md', 'limit': 10})
        self.assertEqual(e.reads(), [])
        e = self.event(hook_event_name='PreToolUse', tool_name='Edit', tool_input={'file_path': 'notes.md', 'new_string': 'text'})
        self.assertEqual((e.tool, e.path, e.text), ('edit', '/work/notes.md', 'text'))
        e = self.event(hook_event_name='PreToolUse', tool_name='Agent', tool_input={'prompt': 'go', 'description': 'd'})
        self.assertEqual((e.tool, e.text), ('dispatch', 'go'))
        e = self.event(hook_event_name='PreToolUse', tool_name='SubagentHandback', tool_input={'message': 'done'})
        self.assertEqual((e.tool, e.text), ('handback', 'done'))
        e = self.event(hook_event_name='SessionStart', source='compact')
        self.assertEqual((e.kind, e.source), ('session-start', 'compact'))

    def test_the_session_is_the_agent_then_the_transcript_then_the_id(self):
        self.assertEqual(self.event(agent_id='a1', transcript_path='/t.jsonl', session_id='s').session, 'a1')
        self.assertEqual(self.event(transcript_path='/t.jsonl', session_id='s').session, '/t.jsonl')
        self.assertEqual(self.event(session_id='s').session, 's')
        self.assertEqual(self.event().session, 'unknown')

    def test_codex_s_tools_in_plain_terms(self):
        patch = '*** Begin Patch\n*** Update File: src/a.c\n@@\n-x\n+y\n*** Add File: docs/b.md\n+text\n*** End Patch\n'
        e = self.event('codex', hook_event_name='PreToolUse', tool_name='apply_patch', tool_input={'command': patch})
        self.assertEqual((e.tool, e.paths, e.text), ('write', ['/work/src/a.c', '/work/docs/b.md'], patch))
        e = self.event('codex', hook_event_name='PostToolUse', tool_name='Bash', tool_input={'command': 'cat /m/a.md b.md'})
        self.assertEqual(e.reads(), ['/m/a.md', '/work/b.md'])
        for command in ('cat /m/a.md | head', 'head -5 /m/a.md', 'cat -n /m/a.md', 'cat /m/a.md > copy', 'cat $FILE'):
            with self.subTest(command):
                e = self.event('codex', hook_event_name='PostToolUse', tool_name='Bash', tool_input={'command': command})
                self.assertEqual(e.reads(), [])
        e = self.event(hook_event_name='PostToolUse', tool_name='Bash', tool_input={'command': 'cat /m/a.md'})
        self.assertEqual((e.reads(), e.reads(True)), ([], ['/m/a.md']))  # claude has a reading tool of its own


class Answers(unittest.TestCase):
    def event(self, name, dialect='claude'):
        return hookkit.Event({'hook_event_name': name, 'tool_name': 'Bash', 'tool_input': {'command': 'x'}}, dialect)

    def test_before_a_tool(self):
        e = self.event('PreToolUse')
        self.assertEqual(hookkit.render(e, {'decision': 'deny', 'reason': 'why'}),
                         {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny', 'permissionDecisionReason': 'why'}})
        self.assertEqual(hookkit.render(e, {'decision': 'ask', 'reason': 'why'})['hookSpecificOutput']['permissionDecision'], 'ask')
        self.assertEqual(hookkit.render(e, {'context': 'note'}),
                         {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'additionalContext': 'note'}})
        self.assertEqual(hookkit.render(e, {'notice': 'told'}), {'systemMessage': 'told'})
        self.assertIsNone(hookkit.render(e, {}))

    def test_other_events(self):
        for name in ('SessionStart', 'UserPromptSubmit', 'PostToolUse'):
            with self.subTest(name):
                self.assertEqual(hookkit.render(self.event(name), {'context': 'note'}),
                                 {'hookSpecificOutput': {'hookEventName': name, 'additionalContext': 'note'}})
        self.assertEqual(hookkit.render(self.event('UserPromptSubmit'), {'decision': 'deny', 'reason': 'why'}),
                         {'decision': 'block', 'reason': 'why'})
        self.assertIsNone(hookkit.render(self.event('Stop'), {'context': 'note'}))

    def test_a_tool_that_cannot_ask(self):
        e = self.event('PreToolUse', 'codex')
        out = hookkit.render(e, {'decision': 'ask', 'reason': 'why'})['hookSpecificOutput']
        self.assertEqual(out['permissionDecision'], 'deny')
        self.assertTrue(out['permissionDecisionReason'].startswith('why\nThis tool cannot put the question to the person'))
        out = hookkit.render(e, {'decision': 'ask', 'reason': 'why'}, ask_becomes='context')['hookSpecificOutput']
        self.assertEqual(out, {'hookEventName': 'PreToolUse', 'additionalContext': 'why'})

    def test_a_long_context_is_cut_and_says_so(self):
        out = hookkit.render(self.event('PreToolUse'), {'context': 'x' * 20000})['hookSpecificOutput']['additionalContext']
        self.assertEqual(len(out), hookkit.CONTEXT_LIMIT + len('\n[cut here: the rest did not fit]'))


class Lookup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        notes = {
            'MEMORY.md': '- [GPU](defaults.md): decoding\n',
            'defaults.md': '---\nname: defaults\ndescription: decided defaults out of the box\n---\n\nEvery player decodes on the GPU that can.\nDecoding on another GPU is on by default.\n',
            'power.md': '---\nname: power\ndescription: power profiles\n---\n\nThe power profile steers the GPU for browsers.\n',
            'colours.md': 'Deep colour, 16 bits.\n',
        }
        for name, text in notes.items():
            with open(os.path.join(self.tmp.name, name), 'w') as f:
                f.write(text)

    def test_a_design_is_found_by_its_content_and_ranked_by_the_words_it_holds(self):
        found = design_lookup.search(self.tmp.name, ['decod', 'GPU', 'default'])
        self.assertEqual([os.path.basename(r[2]) for r in found], ['defaults.md', 'power.md'])
        self.assertEqual(found[0][0], 3)
        text = design_lookup.report(self.tmp.name, ['decod', 'GPU'])
        self.assertIn('decided defaults out of the box', text)
        self.assertIn('> Every player decodes on the GPU that can.', text)
        self.assertNotIn('MEMORY.md', text)
        self.assertEqual(design_lookup.report(self.tmp.name, ['quaternion']), '')

    def test_the_command_line(self):
        run = lambda *args: subprocess.run([sys.executable, '-B', os.path.join(LIB, 'design_lookup.py'), *args], capture_output=True, text=True)
        r = run('--memory', self.tmp.name, 'power profile')
        self.assertEqual(r.returncode, 0)
        self.assertIn('power.md', r.stdout)
        r = run('--memory', self.tmp.name, 'quaternion')
        self.assertEqual(r.returncode, 1)
        self.assertIn('no design found is an answer to report', r.stdout)
        r = run('--memory', os.path.join(self.tmp.name, 'absent'), 'x')
        self.assertEqual(r.returncode, 2)
        self.assertIn('cannot list the memory folder', r.stderr)


if __name__ == '__main__':
    unittest.main()
