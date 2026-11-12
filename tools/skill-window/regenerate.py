#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Rebuild char-classes.txt and window-goldens.tsv from the model's own tokenizer.

Needed only when the index changes its embedding model. It is the one script here that
needs more than Python: the tokenizers library and the model's tokenizer.json.

  python3 regenerate.py --tokenizer-json PATH [--repo DIR]

char-classes.txt: for every code point c, the tokenizer is given "a" + c + "b" and the
answer says how it treats c: it vanishes, it splits the words like a space, it becomes a
token of its own, or it is an ordinary character of a word.
window-goldens.tsv: the tokenizer's token count ([CLS] and [SEP] included) for the twelve
longest skill descriptions, a list of hard cases, sampled lines of the repository's
Markdown and seeded random strings; tools/tests/test_check_skills.py compares
wordpiece.count() with each.
Both files are written the same way on every run, so their SHA-256 can be compared.
"""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARD_CASES = [
    '', ' ', 'a', 'A\tB\nC\rD', 'x\x0by\x0cz', 'a\x00b�c', 'a​b­c‍d',
    'a b c　d e f\u0085g',
    'café naïve Ångström İstanbul ΣΟΦΟΣ ẞ straße',
    'é ö ñ', '中文abc日本語', '한국어 테스트',
    'a\U0002b820b', 'a\U0002b81fb', 'a\U0002b920b', 'a\U0002b91fb', 'a\U0002ceafb', 'a\U0002ceb0b',
    'a㐀b䶿c䷀d', 'a豈b﫿cﬀd', 'a\U0002f800b\U0002fa1fc\U0002fa20d',
    'a\U00020000b\U0002a6dfc\U0002a6e0d\U0002a700e',
    '[CLS] x [SEP] y [MASK] z [UNK] w [PAD]', 'x[UNK]y', '[unk] [Cls]', '[[UNK]]', '[UN[UNK]K]',
    'w' * 100, 'w' * 101, 'a' * 99 + '-' + 'b' * 150, 'é' * 100, 'é' * 101, 'é' * 100,
    'HDMI® 3D™ 20°C 5×3 a→b €5 $5 a+b a=b a<b a|b a~b a^b a`b',
    'it\'s “quoted” ‘x’ — – … « » ¿? ¡!',
    'foo_bar.baz/qux-1.2.3:4@5#6%7&8*9(0)', '\U0001f600 emoji \U0001f468‍\U0001f469‍\U0001f467',
    'العربية עברית हिन्दी ไทย',
    '́abc', 'á̂̃b', 'ＡＢＣ １２', '①② ½ ²',
    'x᠎y', 'x﻿y', 'ẛ̣', 'ǅ ǆ Ǆ', 'ß ẞ ﬁ ﬃ',
    'Å Ω µ', 'a͸b a΢c', 'ab a\U000f0000c', '; ` ̀ ̈́ ῭',
    'Show Screen Contents says the process is not authorized to take a screenshot',
    'dpkg-stereo --verify --deep exits 1 with OLDFORM rows', 'RPATH_SET could not write new RPATH',
    'kunit.py exits 0 with failed tests',
]
RANDOM_POOL = ([chr(c) for c in range(1, 0x250)] + [chr(c) for c in range(0x370, 0x400)]
               + [chr(c) for c in range(0x2000, 0x2070)] + [chr(c) for c in range(0x3000, 0x3040)]
               + [chr(c) for c in (0x4e00, 0x9fff, 0xac00, 0xd7a3, 0xfffd, 0x1f600, 0x2b820, 0xe000, 0x10ffff, 0xfdd0, 0x378)])


def classes(tok):
    found = {'vanish': [], 'space': [], 'alone': []}
    joined = tok.encode('ab').tokens[1:-1]
    points = [c for c in range(0x110000) if not 0xD800 <= c <= 0xDFFF]
    for i in range(0, len(points), 20000):
        chunk = points[i:i + 20000]
        for c, enc in zip(chunk, tok.encode_batch(['a' + chr(c) + 'b' for c in chunk])):
            t = enc.tokens[1:-1]
            if t == joined:
                found['vanish'].append(c)
            elif t == ['a', 'b']:
                found['space'].append(c)
            elif len(t) >= 3 and t[0] == 'a' and t[-1] == 'b':
                found['alone'].append(c)
    lines = []
    for name in ('vanish', 'space', 'alone'):
        spans = []
        for c in found[name]:
            if spans and c == spans[-1][1] + 1:
                spans[-1][1] = c
            else:
                spans.append([c, c])
        lines.append(name + ' ' + ' '.join(f'{a:x}' if a == b else f'{a:x}-{b:x}' for a, b in spans))
    return '\n'.join(lines) + '\n'


def golden_texts(repo):
    import yaml
    described = []
    for f in sorted(repo.glob('skills/*/SKILL.md')):
        text = f.read_text(encoding='utf-8')
        data = yaml.safe_load(text[4:text.find('\n---', 4)])
        described.append(f"{' '.join(str(data['name']).split())}\n\n{' '.join(str(data['description']).split())}")
    described.sort(key=len, reverse=True)
    lines = []
    for f in sorted(repo.rglob('*.md')):
        if '.git' not in f.parts:
            lines += [ln for ln in f.read_text(encoding='utf-8', errors='replace').split('\n') if 0 < len(ln.strip()) <= 240]
    rng = random.Random(531)
    rand = [''.join(rng.choice(RANDOM_POOL) for _ in range(rng.randint(1, 40))) for _ in range(100)]
    return described[:12] + HARD_CASES + lines[::max(1, len(lines) // 120)][:120] + rand


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--tokenizer-json', required=True, help="the model's tokenizer.json")
    ap.add_argument('--repo', default=str(HERE.parent.parent), help='the checkout whose Markdown is sampled')
    a = ap.parse_args()
    try:
        from tokenizers import Tokenizer
    except ImportError:
        sys.exit('regenerate.py needs the tokenizers library (pip install tokenizers, in a virtual environment)')
    tok = Tokenizer.from_file(a.tokenizer_json)
    tok.no_truncation()
    tok.no_padding()
    table = classes(tok)
    (HERE / 'char-classes.txt').write_text(table, encoding='ascii')
    rows = ''.join(f'{len(tok.encode(t).ids)}\t{json.dumps(t, ensure_ascii=True)}\n' for t in golden_texts(Path(a.repo)))
    (HERE / 'window-goldens.tsv').write_text(rows, encoding='ascii')
    for name, text in (('char-classes.txt', table), ('window-goldens.tsv', rows)):
        print(hashlib.sha256(text.encode('ascii')).hexdigest(), name)
    print('Put the SHA-256 of char-classes.txt into CLASSES_SHA256 of wordpiece.py, then run tools/tests/test_check_skills.py.')


if __name__ == '__main__':
    main()
