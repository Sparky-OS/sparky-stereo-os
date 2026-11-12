#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check skill discovery metadata and local documentation targets, offline.

  check-skills.py                 check every skill; exit 1 with one line per problem
  check-skills.py --count [NAME]  print each description's size against its two limits, largest first
  check-skills.py --window N      another index window in tokens (0 switches that one check off, and says so)
  check-skills.py --anchors       also check that every local link with a #fragment lands on a heading of its page
  check-skills.py --root DIR      check another tree (a fixture, an unpacked snapshot)

A description has two limits: 1024 characters (agentskills.io/specification), and the window of the
index's embedding model, 256 tokens of name plus description: what is past it is not embedded.
The token count is the model's own, see tools/skill-window/README.md.
"""
import argparse
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
try:
    import yaml
except ImportError:
    sys.exit('Install python3-yaml in the checking environment to validate YAML frontmatter.')
sys.path.insert(0, str(Path(__file__).resolve().parent / 'skill-window'))
import wordpiece  # noqa: E402

NAME_MAX = 64
DESCRIPTION_MAX = 1024

ap = argparse.ArgumentParser(description='Check skill discovery metadata and local documentation targets, offline.')
ap.add_argument('--count', nargs='*', metavar='NAME', help='print the size of each description (or of the named skills) and stop')
ap.add_argument('--window', type=int, default=wordpiece.WINDOW, metavar='N',
                help='tokens of name plus description the index embeds (default %(default)s; 0 switches the check off)')
ap.add_argument('--anchors', action='store_true',
                help='also check that each local link with a #fragment lands on a heading or an <a id> of its page')
ap.add_argument('--root', default=str(Path(__file__).resolve().parent.parent), help='the tree to check (default: this checkout)')
args = ap.parse_args()
ROOT = Path(args.root).resolve()
errors = []
sizes = []
skills = sorted((ROOT / 'skills').glob('*/SKILL.md'))
for path in skills:
    text = path.read_text()
    try:
        if not text.startswith('---\n'):
            raise ValueError('missing YAML opening fence')
        front, body = text[4:].split('\n---\n', 1)
        data = yaml.safe_load(front)
        if not isinstance(data, dict) or data.get('name') != path.parent.name:
            raise ValueError('name must match folder')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', data['name']):
            raise ValueError('invalid skill name')
        if len(data['name']) > NAME_MAX:
            raise ValueError(f'name is {len(data["name"])} characters, over the format\'s {NAME_MAX}')
        if not isinstance(data.get('description'), str) or not data['description'].strip():
            raise ValueError('description must be nonempty text')
        if not body.strip():
            raise ValueError('empty skill body')
        if 'metadata' in data and not (isinstance(data['metadata'], dict)
                                       and all(isinstance(k, str) and isinstance(v, str) for k, v in data['metadata'].items())):
            raise ValueError('metadata must map text keys to text values (remove an empty "metadata:" line)')
        description = ' '.join(data['description'].split())
        embedded = wordpiece.embedded_text(data['name'], description)
        tokens = wordpiece.count(embedded)
        sizes.append((tokens, len(description), data['name']))
        if len(description) > DESCRIPTION_MAX:
            raise ValueError(f'description is {len(description)} characters, over the format\'s {DESCRIPTION_MAX}')
        if args.window and tokens > args.window:
            kept, lost = wordpiece.split_at_window(embedded, args.window)
            raise ValueError(f'name plus description is {tokens} tokens, over the index\'s window of {args.window}: '
                             f'the index never embeds its last {len(lost.split())} words ("{lost}"); '
                             'shorten it, routing words first, and count again with --count')
    except (ValueError, KeyError, yaml.YAMLError) as e:
        errors.append(f'{path.relative_to(ROOT)}: {e}')
    except wordpiece.DataError as e:
        sys.exit(f'check-skills: the description window cannot be checked: {e}')

if args.count is not None:
    unknown = sorted(set(args.count) - {name for _, _, name in sizes})
    if unknown:
        sys.exit(f'check-skills: no such skill, or its header cannot be read: {", ".join(unknown)}')
    limit = f'of {args.window} tokens' if args.window else 'tokens (window check off)'
    any_over = False
    for tokens, chars, name in sorted(sizes, reverse=True):
        if not args.count or name in args.count:
            over = (args.window and tokens > args.window) or chars > DESCRIPTION_MAX
            any_over = any_over or bool(over)
            print(f'{tokens:4d} {limit}  {chars:4d} of {DESCRIPTION_MAX} characters  {name}{"  OVER" if over else ""}')
    sys.exit(1 if any_over else 0)



def anchors_of(page, known={}):
    """The anchors a Markdown page offers: each heading as GitHub names it (lower case, punctuation dropped, spaces to
    hyphens, a second heading of the same name with -1) and each explicit <a id="...">. Text in code fences is not read."""
    if page not in known:
        found, seen, fence = set(), {}, False
        for line in page.read_text().splitlines():
            if re.match(r'\s{0,3}(```|~~~)', line):
                fence = not fence
            if fence:
                continue
            found.update(re.findall(r'<a\s+(?:id|name)="([^"]+)"', line))
            heading = re.match(r'\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$', line)
            if heading:
                text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', heading[1]).replace('`', '')
                slug = re.sub(r'[^\w\- ]', '', text.lower()).replace(' ', '-')
                found.add(slug if slug not in seen else f'{slug}-{seen[slug]}')
                seen[slug] = seen.get(slug, 0) + 1
        known[page] = found
    return known[page]


# Scope to operational instructions, their references, the pages of the hooks section and of the tools, and the
# maintainer entry pages. A snapshot without a hooks or a tools folder is checked for what it has.
paths = (sorted((ROOT / 'skills').rglob('*.md')) + sorted((ROOT / 'hooks').rglob('*.md'))
         + sorted((ROOT / 'tools').rglob('*.md')) + [ROOT / 'AGENTS.md', ROOT / 'docs/maintainer-workflow.md'])
anchors = 0
for path in paths:
    if not path.is_file():
        errors.append(f'Missing entry page: {path.relative_to(ROOT)}')
        continue
    for match in re.finditer(r'!?\[[^\]\n]*\]\(([^\s)]+)(?:\s+"[^"\n]*")?\)', path.read_text()):
        target = match[1].strip('<>')
        url = urlsplit(target)
        if url.scheme or url.netloc or not url.path:
            continue
        dest = (path.parent / unquote(url.path)).resolve()
        if not dest.is_relative_to(ROOT) or not dest.exists():
            errors.append(f'{path.relative_to(ROOT)}: missing or escaping local link {target}')
    if not args.anchors:
        continue
    fence = False
    for line in path.read_text().splitlines():
        if re.match(r'\s{0,3}(```|~~~)', line):
            fence = not fence
        if fence:
            continue
        for match in re.finditer(r'\]\(([^\s)]+)', line):
            url = urlsplit(match[1].strip('<>'))
            if url.scheme or url.netloc or not url.fragment:
                continue
            dest = (path.parent / unquote(url.path)).resolve() if url.path else path.resolve()
            if dest.suffix == '.md' and dest.is_file() and dest.is_relative_to(ROOT):
                anchors += 1
                if unquote(url.fragment) not in anchors_of(dest):
                    errors.append(f'{path.relative_to(ROOT)}: no heading or mark #{url.fragment} in {dest.relative_to(ROOT)}')
if not skills:
    errors.append('No skills found')
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
window = f'descriptions within {DESCRIPTION_MAX} characters and the index window of {args.window} tokens' if args.window \
    else f'descriptions within {DESCRIPTION_MAX} characters (index window not checked: --window 0)'
print(f'PASS: {len(skills)} skill headers, {window}, and local file targets in {len(paths)} instruction/reference pages. '
      + (f'{anchors} local anchors land on a heading. External URLs require editorial review.' if args.anchors
         else 'External URLs and anchors require editorial review.'))
