"""The licence classes of the font collection, and how a licence text or a short name is sorted into one.

The brief's list (ORDER 508 1e): the SIL Open Font License, Apache 2.0, the Ubuntu Font Licence, the Bitstream Vera
and DejaVu licences, GPL with the font exception, MIT, CC0 and public domain. Anything else is kept out of the
candidates and listed with its own name; "free for personal use" or terms that cannot be read are never used.
"""
import re

USED = ('OFL', 'Apache-2.0', 'UFL', 'Bitstream-Vera', 'GPL-font-exception', 'MIT', 'CC0', 'public-domain')

# a short name as Debian's machine-readable copyright files or Google Fonts' METADATA.pb write it
SHORT = [
    (r'^ofl', 'OFL'), (r'^sil[- ]?ofl', 'OFL'), (r'^ofl-1\.[01]', 'OFL'),
    (r'^apache', 'Apache-2.0'),
    (r'^ufl', 'UFL'), (r'^ubuntu[- ]font', 'UFL'),
    (r'^bitstream[- ]?vera', 'Bitstream-Vera'), (r'^vera', 'Bitstream-Vera'), (r'^bitstream-vera', 'Bitstream-Vera'),
    (r'^agpl', 'other'),
    (r'^gpl.*(font[-_ ]?exception|fonts[-_ ]exception|\+?fe$)', 'GPL-font-exception'),
    (r'^sil([-_ ]|$)', 'OFL'), (r'open[-_ ]font[-_ ]licen[cs]e', 'OFL'),
    (r'^(expat|mit)\b', 'MIT'),
    (r'^cc0', 'CC0'),
    (r'^public[- ]domain', 'public-domain'),
]

# words a licence's own text uses
TEXT = [
    ('OFL', r'SIL Open Font License|scripts\.sil\.org/OFL|openfontlicense\.org'),
    ('Apache-2.0', r'Apache License,? Version 2\.0|apache\.org/licenses/LICENSE-2\.0'),
    ('UFL', r'Ubuntu Font Licen[cs]e'),
    ('Bitstream-Vera', r'Bitstream Vera|Bitstream, Inc\..*Vera'),
    ('GPL-font-exception', r'As a special exception, if you create a document which uses this font|GNU General Public License.{0,400}font exception|font exception'),
    ('MIT', r'Permission is hereby granted, free of charge, to any person obtaining a copy'),
    ('CC0', r'CC0|creativecommons\.org/publicdomain/zero'),
    ('public-domain', r'\bpublic domain\b|placed in the public domain'),
]

NEVER = re.compile(r'personal use only|for personal use|non-?commercial use only|not for commercial', re.I)


def from_short(name):
    s = (name or '').strip().lower()
    if not s:
        return None
    # "Bitstream-Vera and public-domain" (DejaVu): every part must be on the list
    parts = [p.strip() for p in re.split(r'\s+and\s+|\s*,\s*|-and-', s) if p.strip()]
    if len(parts) > 1 and ' or ' not in s and '|' not in s:
        cls = [from_short(p) for p in parts]
        if all(c in USED for c in cls):
            return 'Bitstream-Vera' if 'Bitstream-Vera' in cls else cls[0]
        return 'other: ' + name.strip()
    if ' or ' in s or '|' in s:
        # a choice of licences: the first one on the list
        for p in re.split(r'\s+or\s+|\|', s):
            c = from_short(p)
            if c in USED:
                return c
        return 'other: ' + name.strip()
    for pat, cl in SHORT:
        if re.search(pat, s):
            return cl if cl != 'other' else 'other: ' + name.strip()
    return 'other: ' + name.strip()


def from_text(text):
    """the class a licence text names; None when it names none of the list or more than one that disagree"""
    if not text:
        return None
    if NEVER.search(text):
        return 'never: ' + NEVER.search(text).group(0)
    hits = [cl for cl, pat in TEXT if re.search(pat, text, re.I | re.S)]
    if not hits:
        return None
    # the GPL with the font exception mentions the GPL; Vera fonts often add "public domain" for changes
    if 'GPL-font-exception' in hits:
        return 'GPL-font-exception'
    if 'OFL' in hits:
        return 'OFL'
    if 'Bitstream-Vera' in hits:
        return 'Bitstream-Vera'
    if len(set(hits)) == 1:
        return hits[0]
    # MIT for the font and public domain for some of its parts: both on the list
    if set(hits) <= {'MIT', 'public-domain', 'CC0'}:
        return 'MIT' if 'MIT' in hits else hits[0]
    return 'unclear: ' + '+'.join(sorted(set(hits)))
