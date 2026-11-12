#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of tools/check-skills.py and of the token counter behind its window check.

  python3 tools/tests/test_check_skills.py        (add -v for one line per test)

They need python3 and python3-yaml, no network and no model.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent.parent
CHECK = ROOT / 'tools' / 'check-skills.py'
WINDOW_DIR = ROOT / 'tools' / 'skill-window'
sys.path.insert(0, str(WINDOW_DIR))
import wordpiece  # noqa: E402


def check(root, *options):
    return subprocess.run([sys.executable, '-B', str(CHECK), '--root', str(root), *options], capture_output=True, text=True)


def make_tree(base, skills):
    """A tree with the two entry pages and one folder per skill; skills maps a folder to its SKILL.md text."""
    (base / 'docs').mkdir(parents=True)
    (base / 'AGENTS.md').write_text('# Entry\n')
    (base / 'docs' / 'maintainer-workflow.md').write_text('# Workflow\n')
    for folder, text in skills.items():
        (base / 'skills' / folder).mkdir(parents=True)
        (base / 'skills' / folder / 'SKILL.md').write_text(text)
    return base


def skill(name, description, extra='', body='# Title\n\nBody.\n'):
    return f'---\nname: {name}\ndescription: {description}\n{extra}---\n\n{body}'


class Counter(unittest.TestCase):
    def test_counts_equal_the_model_tokenizer(self):
        rows = (WINDOW_DIR / 'window-goldens.tsv').read_text(encoding='ascii').splitlines()
        self.assertGreater(len(rows), 250)
        wrong = []
        for row in rows:
            want, text = row.split('\t', 1)
            got = wordpiece.count(json.loads(text))
            if got != int(want):
                wrong.append((want, got, text[:60]))
        self.assertEqual(wrong, [])

    def test_two_special_tokens_are_counted(self):
        self.assertEqual(wordpiece.count(''), 2)
        self.assertEqual(wordpiece.count('stereo'), 3)

    def test_embedded_text_is_name_blank_line_description_on_one_line(self):
        self.assertEqual(wordpiece.embedded_text('a-b', 'x  y\n z'), 'a-b\n\nx y z')

    def test_a_changed_vocabulary_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / 'vocab.txt'
            copy.write_bytes(wordpiece.VOCAB.read_bytes().replace(b'\nstereo\n', b'\n', 1))
            with self.assertRaises(wordpiece.DataError):
                wordpiece.load_vocab(copy)

    def test_a_missing_vocabulary_is_refused(self):
        with self.assertRaises(wordpiece.DataError):
            wordpiece.load_vocab(Path('/nonexistent/vocab.txt'))

    def test_split_at_window_names_the_words_lost(self):
        kept, lost = wordpiece.split_at_window('one two three four', window=5)
        self.assertEqual((kept, lost), ('one two three', 'four'))
        self.assertEqual(wordpiece.split_at_window('one two', window=256), ('one two', ''))


class CheckSkills(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='check-skills-test-'))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_this_repository_passes(self):
        r = check(ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('the index window of 256 tokens', r.stdout)

    def test_a_small_valid_tree_passes(self):
        r = check(make_tree(self.tmp, {'demo': skill('demo', 'A demo skill. Load it when a test needs one.')}))
        self.assertEqual((r.returncode, r.stderr), (0, ''))

    def test_description_at_the_window_passes_and_one_token_more_fails(self):
        # "demo" is one token and "a" is one token: 1 + 253 + [CLS] + [SEP] = 256
        at = make_tree(self.tmp / 'at', {'demo': skill('demo', ' '.join(['a'] * 253))})
        r = check(at)
        self.assertEqual(r.returncode, 0, r.stderr)
        over = make_tree(self.tmp / 'over', {'demo': skill('demo', ' '.join(['a'] * 253 + ['tail']))})
        r = check(over)
        self.assertEqual(r.returncode, 1)
        self.assertIn('skills/demo/SKILL.md: name plus description is 257 tokens, over the index\'s window of 256', r.stderr)
        self.assertIn('never embeds its last 1 words ("tail")', r.stderr)

    def test_count_prints_the_size_and_exits_1_when_over(self):
        over = make_tree(self.tmp, {'demo': skill('demo', ' '.join(['a'] * 254)), 'small': skill('small', 'Short.')})
        r = check(over, '--count')
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout.splitlines()[0], ' 257 of 256 tokens   507 of 1024 characters  demo  OVER')
        r = check(over, '--count', 'small')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, '   5 of 256 tokens     6 of 1024 characters  small\n')
        r = check(over, '--count', 'absent')
        self.assertEqual(r.returncode, 1)
        self.assertIn('no such skill', r.stderr)

    def test_another_window_and_no_window(self):
        tree = make_tree(self.tmp, {'demo': skill('demo', ' '.join(['a'] * 254))})
        self.assertEqual(check(tree).returncode, 1)
        self.assertEqual(check(tree, '--window', '300').returncode, 0)
        r = check(tree, '--window', '0')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('index window not checked: --window 0', r.stdout)

    def test_description_over_1024_characters_fails(self):
        # "international" is one token, so 79 of them are 1105 characters and only 82 tokens
        r = check(make_tree(self.tmp, {'demo': skill('demo', ' '.join(['international'] * 79))}))
        self.assertEqual(r.returncode, 1)
        self.assertIn('description is 1105 characters, over the format\'s 1024', r.stderr)

    def test_header_mistakes_fail(self):
        cases = {
            'name-not-folder': (skill('other', 'Text.'), 'name must match folder'),
            'Bad_Name': (skill('Bad_Name', 'Text.'), 'invalid skill name'),
            'no-description': ('---\nname: no-description\n---\n\nBody.\n', 'description must be nonempty text'),
            'empty-metadata': (skill('empty-metadata', 'Text.', 'metadata:\n'), 'metadata must map text keys to text values'),
            'no-body': (skill('no-body', 'Text.', body=''), 'empty skill body'),
            'no-fence': ('name: no-fence\n', 'missing YAML opening fence'),
        }
        for folder, (text, message) in cases.items():
            with self.subTest(folder):
                r = check(make_tree(self.tmp / folder, {folder: text}))
                self.assertEqual(r.returncode, 1)
                self.assertIn(message, r.stderr)

    def test_requires_packages_metadata_passes(self):
        r = check(make_tree(self.tmp, {'demo': skill('demo', 'Text.', 'metadata:\n  requires-packages: git | make\n')}))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_broken_local_link_fails(self):
        tree = make_tree(self.tmp, {'demo': skill('demo', 'Text.', body='See [the page](references/absent.md).\n')})
        r = check(tree)
        self.assertEqual(r.returncode, 1)
        self.assertIn('skills/demo/SKILL.md: missing or escaping local link references/absent.md', r.stderr)

    def test_a_broken_local_link_in_a_hooks_page_or_a_tools_page_fails(self):
        tree = make_tree(self.tmp, {'demo': skill('demo', 'Text.')})
        for folder, page, target in (('hooks/demo', 'README.md', '../lib/kit.py'), ('tools/counter', 'README.md', 'data.txt')):
            with self.subTest(folder):
                (tree / folder).mkdir(parents=True)
                (tree / folder / page).write_text(f'See [the file]({target}).\n')
                r = check(tree)
                self.assertEqual(r.returncode, 1)
                self.assertIn(f'{folder}/{page}: missing or escaping local link {target}', r.stderr)
                there = (tree / folder / target).resolve()
                there.parent.mkdir(parents=True, exist_ok=True)
                there.write_text('')
                self.assertEqual(check(tree).returncode, 0)

    def test_anchors_are_checked_on_request(self):
        body = ('# Title\n\n## The first part\n\nSee [below](#the-second-part-with-code) and [the page](references/more.md#a-heading).\n\n'
                '## The second part, with `code`\n\nText.\n\n```sh\necho "[not a link](#nowhere)"\n```\n')
        tree = make_tree(self.tmp, {'demo': skill('demo', 'Text.', body=body)})
        more = tree / 'skills/demo/references/more.md'
        more.parent.mkdir()
        more.write_text('# More\n\n## A heading\n\n<a id="kept-name"></a>\nBack to [the skill](../SKILL.md#the-first-part), [the mark](#kept-name) '
                        'and [the second of two](#again-1).\n\n## Again\n\n## Again\n')
        r = check(tree, '--anchors')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('5 local anchors land on a heading', r.stdout)
        more.write_text('# More\n\n## Another heading\n')
        self.assertEqual(check(tree).returncode, 0)  # without the option, the file being there is enough
        r = check(tree, '--anchors')
        self.assertEqual(r.returncode, 1)
        self.assertIn('skills/demo/SKILL.md: no heading or mark #a-heading in skills/demo/references/more.md', r.stderr)

    def test_an_empty_tree_fails(self):
        (self.tmp / 'skills').mkdir()
        r = check(self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn('No skills found', r.stderr)


if __name__ == '__main__':
    unittest.main()
