#!/usr/bin/env python3
"""Read the limited Markdown vocabulary used by the edition's front pages.

This is deliberately not a general Markdown implementation. Unsupported syntax
fails the import. Catalogues retain source paragraphs, links and image attributes
as separate keys; the original Markdown remains the editorial authority.
"""
from collections import Counter
from html import unescape
from pathlib import Path
import hashlib
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
LANGUAGES = {
    'en': ('en', '🇨🇦', 'English'),
    'pt_BR': ('pt-BR', '🇧🇷', 'Português'),
    'pl': ('pl', '🇵🇱', 'Polski'),
    'fr': ('fr', '🇫🇷', 'Français'),
    'de': ('de', '🇩🇪', 'Deutsch'),
    'es': ('es', '🇲🇽', 'Español'),
    'ja': ('ja', '🇯🇵', '日本語'),
    'ko': ('ko', '🇰🇷', '한국어'),
    'zh_CN': ('zh-CN', '🇨🇳', '简体中文'),
    'zh_TW': ('zh-TW', '🇭🇰', '繁體中文'),
}
KINDS = {'home': 'index.html', 'detail': 'edition-in-detail.html',
         'windows': 'try-on-windows.html'}
SOURCE = {}
for lang, (tag, _, _) in LANGUAGES.items():
    SOURCE[lang] = {'home': 'README' + ('' if lang == 'en' else '.' + tag) + '.md'}
    detail = 'docs/edition-in-detail' + ('' if lang == 'en' else '.' + tag) + '.md'
    if (ROOT / detail).is_file():
        SOURCE[lang]['detail'] = detail
    windows = f'docs/guides/try-on-windows.{tag}.md'
    if (ROOT / windows).is_file():
        SOURCE[lang]['windows'] = windows


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def slug(text):
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'!?\[([^]]*)\]\([^)]*\)', r'\1', text)
    text = text.replace('*', '').replace('`', '').strip().lower()
    return ''.join(c if c != ' ' else '-' for c in text
                   if c in '-_ ' or unicodedata.category(c)[0] in 'LN'
                   or unicodedata.category(c) in ('Mn', 'Mc'))


def source_anchors(text):
    found = [(m.start(), m.group(1), 'explicit') for m in
             re.finditer(r'<a\s+(?:id|name)="([^"]+)"[^>]*>\s*</a>', text)]
    counts = Counter()
    for m in re.finditer(r'^#{1,6} (.+)$', text, re.M):
        value = slug(m.group(1)); n = counts[value]; counts[value] += 1
        found.append((m.start(), value + (f'-{n}' if n else ''), m.group(1)))
    return sorted(found)


def blocks(text):
    """Parse blocks, retaining all content and source line numbers."""
    lines = text.splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1; continue
        start = i + 1
        if re.fullmatch(r'(?:<a\s+(?:id|name)="[^"]+"[^>]*></a>\s*)+', line):
            result.append({'type': 'anchors', 'raw': line, 'line': start})
            i += 1; continue
        if re.match(r'^#{1,6} ', line):
            hashes, value = line.split(' ', 1)
            result.append({'type': 'heading', 'level': len(hashes), 'raw': value, 'line': start})
            i += 1; continue
        if '[English](' in line and ('[Português](' in line or '[Deutsch](' in line):
            result.append({'type': 'languages', 'raw': line, 'line': start})
            i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(lines[i]); i += 1
            result.append({'type': 'table', 'raw': '\n'.join(rows), 'line': start})
            continue
        if line.startswith('>'):
            value = []
            while i < len(lines) and lines[i].startswith('>'):
                value.append(lines[i][1:].lstrip()); i += 1
            result.append({'type': 'quote', 'raw': '\n'.join(value), 'line': start})
            continue
        match = re.match(r'^(- |\d+\. )(.*)', line)
        if match:
            prefix, value = match.groups()
            ordered = prefix != '- '
            gathered = [value]; i += 1
            while i < len(lines):
                # Continuations of one item, including its indented screenshots.
                if lines[i].startswith(' '):
                    gathered.append(lines[i].lstrip()); i += 1
                elif not lines[i].strip() and i + 1 < len(lines) and lines[i + 1].startswith(' '):
                    gathered.append(''); i += 1
                else:
                    break
            result.append({'type': 'step' if ordered else 'item', 'raw': '\n'.join(gathered),
                           'line': start})
            continue
        value = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,6} |[-|>] |\d+\. |<a (?:id|name)=)', lines[i]):
            value.append(lines[i]); i += 1
        result.append({'type': 'paragraph', 'raw': '\n'.join(value), 'line': start})
    return result


def bracket_end(text, start, opening='[', closing=']'):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == opening: depth += 1
        if text[i] == closing:
            depth -= 1
            if depth == 0: return i
    raise ValueError('Unclosed bracket: ' + text[start:start + 80])


def tokenize(raw, key, strings):
    """Pull every URL and image alt out of a block without changing its words."""
    counts = Counter()
    def save(kind, value):
        counts[kind] += 1
        k = f'{key}.{kind}{counts[kind]:02}'
        strings[k] = unescape(value)
        return '{{' + k + '}}'
    def scan(value):
        out = []; i = 0
        while i < len(value):
            if value[i] == '<':
                end = value.find('>', i)
                if end < 0: raise ValueError('Unclosed HTML tag')
                tag = value[i:end + 1]
                def attr(m):
                    name, val = m.groups()
                    kind = 'alt' if name == 'alt' else ('image' if name in ('src','srcset') else 'link')
                    return name + '="' + save(kind, val) + '"'
                tag = re.sub(r'(href|src|srcset|alt)="([^"]*)"', attr, tag)
                out.append(tag); i = end + 1; continue
            is_image = value.startswith('![', i)
            start = i + 1 if is_image else i
            if value[start:start + 1] == '[':
                end = bracket_end(value, start)
                if value[end + 1:end + 2] == '(':
                    close = bracket_end(value, end + 1, '(', ')')
                    label = value[start + 1:end]
                    target = value[end + 2:close]
                    if is_image:
                        out.append('![' + save('alt', label) + '](' + save('image', target) + ')')
                    else:
                        out.append('[' + scan(label) + '](' + save('link', target) + ')')
                    i = close + 1; continue
            out.append(value[i]); i += 1
        return ''.join(out)
    return scan(raw)


def extract():
    english_headings = {}
    for kind, source in SOURCE['en'].items():
        english_headings[kind] = [slug(b['raw']) for b in blocks((ROOT/source).read_text()) if b['type']=='heading']
    result = {}
    for lang, sources in SOURCE.items():
        catalog = {'language': lang, 'pages': {}, 'strings': {}}
        for kind, source in sources.items():
            text = (ROOT/source).read_text(encoding='utf-8')
            doc = {'source': source, 'sha256': hashlib.sha256(text.encode()).hexdigest(), 'blocks': []}
            section = 'intro'; counts = Counter(); heading = 0
            source_blocks = blocks(text)
            if kind == 'detail' and lang == 'en':
                # These later English additions have not reached the other
                # detail pages. Give each its own key, instead of hiding a
                # partial translation inside an otherwise translated paragraph.
                expanded = []
                additions = [('2026-10-30-tpac-2026-report/README.md', 'tpac-report'),
                             ('stereo-3d-closed-stacks-open-standards.html', 'after-tpac-report'),
                             ('[The glossary](glossary.md)', 'glossary')]
                for b in source_blocks:
                    if b['type'] != 'paragraph':
                        expanded.append(b); continue
                    kept, added = [], []
                    for offset, line in enumerate(b['raw'].splitlines()):
                        named = next((name for marker, name in additions if marker in line), None)
                        if named:
                            added.append(dict(b, raw=line, semantic=named, line=b['line'] + offset))
                        else:
                            kept.append(line)
                    if kept: expanded.append(dict(b, raw='\n'.join(kept)))
                    expanded.extend(added)
                source_blocks = expanded
            for b in source_blocks:
                if b['type'] == 'languages':
                    doc['language_row'] = b['raw']; continue
                if b['type'] == 'anchors':
                    doc['blocks'].append(b); continue
                if b['type'] == 'heading':
                    if heading >= len(english_headings[kind]):
                        raise ValueError(f'{source}: extra heading requires an explicit mapping')
                    section = english_headings[kind][heading] if heading else 'intro'
                    heading += 1; counts = Counter()
                if 'semantic' in b:
                    key = f'{kind}.{section}.{b.pop("semantic")}'
                else:
                    counts[b['type']] += 1
                    key = f'{kind}.{section}.{b["type"]}{counts[b["type"]]:02}'
                raw = b.pop('raw')
                catalog['strings'][key] = tokenize(raw, key, catalog['strings'])
                b['key'] = key
                if b['type'] == 'heading':
                    b['id'] = slug(raw)
                    b['english_id'] = english_headings[kind][heading - 1]
                    # The original detail's initial h3 skips h2. Promote that one
                    # to h2; preserve its original slug and its English alias.
                    if kind == 'detail' and heading == 2 and b['level'] == 3:
                        b['level'] = 2
                doc['blocks'].append(b)
            if heading != len(english_headings[kind]):
                raise ValueError(f'{source}: missing heading requires an explicit mapping')
            catalog['pages'][kind] = doc
        result[lang] = catalog
    return result


def missing_report(catalogs):
    source = catalogs['en']['strings']
    result = {}
    for lang, catalog in catalogs.items():
        missing_pages = sorted(set(KINDS) - set(catalog['pages']))
        missing = sorted(k for k in source if k.split('.')[0] in catalog['pages'] and k not in catalog['strings'])
        extra = sorted(k for k in catalog['strings'] if k not in source)
        result[lang] = {'missing_pages': missing_pages, 'missing_keys': missing, 'additional_keys': extra}
    return result


def load_catalogs():
    return {lang: json.loads((SITE/'strings'/f'{lang}.json').read_text()) for lang in LANGUAGES}


def page_path(lang, kind):
    return ('' if lang == 'en' else LANGUAGES[lang][0] + '/') + KINDS[kind]
