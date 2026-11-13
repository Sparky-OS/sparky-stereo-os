#!/usr/bin/env python3
"""Check the page's string tables (site/strings.js and site/lang/*.js): every language has every key and no other,
every placeholder of the English string ({0}, {1} ...) appears in the translation and no other, no string is empty,
and a translation differs from the English unless the string is a name or a unit. Exit 1 on any finding.
check_strings.py [SITE-DIR]"""
import os
import re
import sys

site = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'site')
LANGS = ['pl', 'pt_BR', 'fr', 'de', 'es', 'ja', 'ko', 'zh_CN', 'zh_TW']
# strings that are names, units or symbols: the same in every language is right
SAME_OK = {'hTitle', 'presetIsdn', 'presetDsl', 'presetMobile', 'longestValue', 'problem', 'total', 'kindScript', 'kindModel',
           'tlTexture', 'summaryPart', 'linkChoice', 'quickDsl'}
# words that are the same in one language and English
SAME_OK_LANG = {'fr': {'aLicenceLink', 'presetFibre'}, 'de': {'a3dH'}, 'es': {'presetCable'}}


def table(path, quote):
    out = {}
    pat = re.compile(r"^\s{2,4}([A-Za-z0-9]+): %s((?:\\.|[^%s\\])*)%s,\s*$" % (quote, quote, quote))
    for line in open(path, encoding='utf-8'):
        m = pat.match(line)
        if m:
            out[m.group(1)] = m.group(2).replace('\\' + quote, quote)
    return out


en = table(os.path.join(site, 'strings.js'), "'")
bad = 0
print('en: %d keys' % len(en))
for l in LANGS:
    p = os.path.join(site, 'lang', l + '.js')
    if not os.path.isfile(p):
        print('%s: no file' % l)
        bad += 1
        continue
    tr = table(p, '"')
    missing = [k for k in en if k not in tr]
    extra = [k for k in tr if k not in en]
    same = [k for k in en if k in tr and tr[k] == en[k] and k not in SAME_OK and k not in SAME_OK_LANG.get(l, ())]
    ph = [k for k in en if k in tr and sorted(set(re.findall(r'\{\d+\}', en[k]))) != sorted(set(re.findall(r'\{\d+\}', tr[k])))]
    empty = [k for k in tr if not tr[k].strip()]
    print('%s: %d keys; missing %s; extra %s; same as English %s; placeholders differ %s; empty %s' % (l, len(tr), missing, extra, same, ph, empty))
    bad += len(missing) + len(extra) + len(same) + len(ph) + len(empty)
sys.exit(1 if bad else 0)
