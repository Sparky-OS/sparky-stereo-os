#!/usr/bin/env python3
"""A second reader's check: every word of each Markdown front page is in its built page, in the source's order.

It shares no code with model.py or build.py on purpose. check.py compares a built
page with the generator's own second rendering, so a generator that drops or moves
a sentence passes there; this reads the Markdown and the HTML separately and
compares their words and punctuation marks as two sequences.

Two differences are expected and named: the language row, which the site shows as
its menu, and the credit line added to the foot of a detail or guide page (it must
be found, whole, in that language's own home page). Anything else fails.
An element marked data-added is an addition the site makes on purpose (a trial
figures row, a wordless strip): it is left out of the comparison and counted.
"""
import argparse
import difflib
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAGS = {'en': '', 'pt_BR': 'pt-BR', 'pl': 'pl', 'fr': 'fr', 'de': 'de', 'es': 'es',
        'ja': 'ja', 'ko': 'ko', 'zh_CN': 'zh-CN', 'zh_TW': 'zh-TW'}
NAMES = {'English', 'Português', 'Polski', 'Français', 'Deutsch', 'Español', '日本語', '한국어', '简体中文', '繁體中文', '·'}
BLOCK = {'p', 'div', 'li', 'ul', 'ol', 'dl', 'dt', 'dd', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
         'blockquote', 'br', 'tr', 'td', 'th', 'table', 'summary', 'details', 'section'}


def tokens(text):
    return re.findall(r'\w+|[^\w\s]', text)


def pages(build):
    for lang, tag in TAGS.items():
        suffix = '.' + tag if tag else ''
        folder = tag + '/' if tag else ''
        yield lang, 'home', ROOT / f'README{suffix}.md', build / f'{folder}index.html'
        yield lang, 'detail', ROOT / f'docs/edition-in-detail{suffix}.md', build / f'{folder}edition-in-detail.html'
        yield lang, 'windows', ROOT / f'docs/guides/try-on-windows.{tag or "en"}.md', build / f'{folder}try-on-windows.html'


def markdown_words(text):
    """The words a reader sees in the Markdown, and the number of links per line."""
    words, links, row_links = [], 0, 0
    for line in text.splitlines():
        if re.fullmatch(r'\|[\s|:-]*\|?', line.strip()):
            continue
        is_row = '[English](' in line and ('[Português](' in line or '[Deutsch](' in line)
        line = re.sub(r'^\s*(#{1,6} |- |\d+\. |> ?)', '', line)
        line = re.sub(r'<img\b[^>]*?\balt="([^"]*)"[^>]*>', lambda m: ' ' + m.group(1) + ' ', line)
        found = len(re.findall(r'<a\b[^>]*?\bhref="', line))
        line = re.sub(r'<br\s*/?>', ' ', line)
        line = re.sub(r'<[^>]+>', '', line)
        previous = None
        while previous != line:
            previous = line
            def link(m):
                nonlocal found
                if not m.group(1):
                    found += 1
                return (' ' + m.group(2) + ' ') if m.group(1) else m.group(2)
            line = re.sub(r'(!?)\[([^\[\]]*)\]\(([^()\s]*(?:\([^()]*\))?[^()\s]*)\)', link, line)
        line = line.replace('**', '').replace('`', '').replace('|', ' ')
        line = re.sub(r'\*([^*\n]+)\*', r'\1', line)
        words += tokens(html.unescape(line))
        links += found
        if is_row:
            row_links += found
    return words, links, row_links


class Built(HTMLParser):
    """The words a reader sees in main and footer; decoration marked aria-hidden is not text."""
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.buffer, self.links, self.inside, self.skip, self.hidden, self.stack, self.added = [], 0, 0, 0, 0, [], []
        self.feed(text)
        self.words = tokens(''.join(self.buffer))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('main', 'footer'): self.inside += 1
        if tag in ('script', 'style'): self.skip += 1
        hidden = a.get('aria-hidden') == 'true' or 'data-added' in a  # a named addition is not the source's text
        if 'data-added' in a: self.added.append(a['data-added'])
        if tag not in ('img', 'br', 'link', 'meta', 'source', 'input', 'hr'):
            self.stack.append(hidden); self.hidden += hidden
        if self.inside and not self.skip and not self.hidden:
            if tag == 'img' and a.get('alt') and not hidden: self.buffer.append(' ' + a['alt'] + ' ')
            if tag == 'a' and 'href' in a: self.links += 1
            if tag in BLOCK: self.buffer.append('\n')

    def handle_endtag(self, tag):
        if tag in ('main', 'footer'): self.inside -= 1
        if tag in ('script', 'style'): self.skip -= 1
        if self.stack: self.hidden -= self.stack.pop()
        if tag in BLOCK: self.buffer.append('\n')

    def handle_data(self, data):
        if self.inside and not self.skip and not self.hidden: self.buffer.append(data)


def contains(haystack, needle):
    n = len(needle)
    return any(haystack[i:i + n] == needle for i in range(len(haystack) - n + 1))


def compare(kind, source_text, built_text, home_words):
    """Unexpected differences between one source and its page, as readable lines."""
    a, links, row_links = markdown_words(source_text)
    page = Built(built_text)
    b = page.words
    problems = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == 'equal':
            continue
        gone, new = a[i1:i2], b[j1:j2]
        if op == 'delete' and all(t in NAMES or 0x1F1E6 <= ord(t[0]) <= 0x1F1FF for t in gone):
            continue  # the language row: the site's menu
        if op == 'insert' and kind != 'home' and j2 == len(b) and contains(home_words, new):
            continue  # the home page's own credit line, at the foot
        problems.append(f'{op}: source {" ".join(gone)[:160]!r} built {" ".join(new)[:160]!r}')
    if page.links != links - row_links:
        problems.append(f'links: source {links} with {row_links} in the language row, built {page.links}')
    return problems, len(a), page.links, page.added


def run(build):
    failures, count, words, links, additions = [], 0, 0, 0, []
    for lang, kind, source, built in pages(build):
        if source.is_file() != built.is_file():
            failures.append(f'{lang} {kind}: source and page do not both exist'); continue
        if not source.is_file():
            continue
        home = ROOT / ('README.md' if lang == 'en' else f'README.{TAGS[lang]}.md')
        problems, n, k, added = compare(kind, source.read_text(encoding='utf-8'), built.read_text(encoding='utf-8'),
                                 markdown_words(home.read_text(encoding='utf-8'))[0])
        failures += [f'{lang} {kind}: {p}' for p in problems]
        count += 1; words += n; links += k; additions += added
    return failures, count, words, links, additions


def control(build):
    """The check must fail on a moved and on a removed paragraph."""
    source = (ROOT / 'docs/edition-in-detail.md').read_text(encoding='utf-8')
    page = (build / 'edition-in-detail.html').read_text(encoding='utf-8')
    home = markdown_words((ROOT / 'README.md').read_text(encoding='utf-8'))[0]
    paragraphs = list(re.finditer(r'<p>.*?</p>', page, re.S))
    first, late = paragraphs[2], paragraphs[len(paragraphs) // 2]
    moved = page[:first.start()] + late.group(0) + page[first.start():late.start()] + page[late.end():]
    removed = page[:late.start()] + page[late.end():]
    results = []
    for name, text in (('a paragraph moved', moved), ('a paragraph removed', removed)):
        problems = compare('detail', source, text, home)[0]
        results.append((name, bool(problems)))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--output', type=Path, default=ROOT / 'site/_build')
    parser.add_argument('--control', action='store_true', help='also show that a moved and a removed paragraph fail')
    args = parser.parse_args()
    failures, count, words, links, additions = run(args.output.resolve())
    for failure in failures:
        print('FAIL:', failure)
    if args.control:
        for name, caught in control(args.output.resolve()):
            print(('PASS' if caught else 'FAIL') + f' negative control: {name}')
            if not caught: failures.append(name)
    if failures:
        print(f'RESULT: FAIL, {len(failures)} differences'); sys.exit(1)
    named = ', '.join(f'{additions.count(n)} {n}' for n in sorted(set(additions))) or 'none'
    print(f'RESULT: PASS, {count} pages, {words} words and marks in source order, {links} links; additions not in the sources: {named}')


if __name__ == '__main__':
    main()
