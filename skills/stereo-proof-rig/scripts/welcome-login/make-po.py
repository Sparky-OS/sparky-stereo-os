#!/usr/bin/python3
"""make-po.py POT TRANSLATIONS.py PO_DIR: one LANG.po for each language of the table (TRANSLATIONS.py's T: (context, English)
-> {LANG: text}), every message of POT translated; exits 1 when the table lacks a message of POT or a language's text."""
import importlib.util, re, sys
pot, table, out = sys.argv[1:4]
spec = importlib.util.spec_from_file_location('t', table); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def unq(lines):
    return ''.join(eval(l) for l in lines)  # PO strings are C strings: a Python literal reads them
entries, cur, key = [], {}, None
for line in open(pot, encoding='utf-8').read().splitlines() + ['']:
    if not line.strip():
        if cur.get('msgid') and unq(cur['msgid']):
            entries.append((unq(cur.get('msgctxt', [])), unq(cur['msgid'])))
        cur, key = {}, None
        continue
    mt = re.match(r'^(msgctxt|msgid|msgstr) (".*")$', line)
    if mt:
        key = mt.group(1); cur[key] = [mt.group(2)]
    elif line.startswith('"') and key:
        cur[key].append(line)
langs = sorted({l for tr in m.T.values() for l in tr})
def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
missing = [e for e in entries if e not in m.T]
if missing:
    sys.exit('not in the table: %r' % missing)
for lang in langs:
    with open('%s/%s.po' % (out, lang), 'w', encoding='utf-8') as f:
        f.write('# The pages of sparky-stereo-welcome, %s.\n# This file is distributed under the same license as the sparky-stereo-welcome package.\n' % lang)
        f.write('msgid ""\nmsgstr ""\n"Project-Id-Version: sparky-stereo-welcome\\n"\n"PO-Revision-Date: 2026-11-25 00:00+0000\\n"\n"Last-Translator: Sparky Stereo OS\\n"\n"Language-Team: Sparky Stereo OS\\n"\n"Language: %s\\n"\n"MIME-Version: 1.0\\n"\n"Content-Type: text/plain; charset=UTF-8\\n"\n"Content-Transfer-Encoding: 8bit\\n"\n\n' % lang)
        for ctx, mid in entries:
            text = m.T[(ctx, mid)].get(lang)
            if not text:
                sys.exit('no %s text for %r' % (lang, mid))
            f.write('msgctxt %s\nmsgid %s\nmsgstr %s\n\n' % (q(ctx), q(mid), q(text)))
print('%d messages in %d languages: %s' % (len(entries), len(langs), ' '.join(langs)))
