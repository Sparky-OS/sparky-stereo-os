#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check skill discovery metadata and local documentation targets, offline."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError:
    sys.exit('Install python3-yaml in the checking environment to validate YAML frontmatter.')

ROOT = Path(__file__).resolve().parent.parent
errors = []
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
        if not isinstance(data.get('description'), str) or not data['description'].strip():
            raise ValueError('description must be nonempty text')
        if not body.strip():
            raise ValueError('empty skill body')
    except (ValueError, KeyError, yaml.YAMLError) as e:
        errors.append(f'{path.relative_to(ROOT)}: {e}')

# Scope to operational instructions, their references and the maintainer entry pages.
paths = sorted((ROOT / 'skills').rglob('*.md')) + [ROOT / 'AGENTS.md', ROOT / 'docs/maintainer-workflow.md']
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
if not skills:
    errors.append('No skills found')
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
print(f'PASS: {len(skills)} skill headers and local file targets in {len(paths)} instruction/reference pages. External URLs and anchors require editorial review.')
