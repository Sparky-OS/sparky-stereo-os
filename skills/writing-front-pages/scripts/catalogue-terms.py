#!/usr/bin/env python3
"""Print how installed gettext catalogues translate exact English strings.

usage: catalogue-terms.py LANG 'English string'...
example: catalogue-terms.py es 'Display Configuration' 'Scale:' 'Refresh rate:' '&Keep'

Reads /usr/share/locale/LANG/LC_MESSAGES/*.mo (set LOCALE_DIR for another folder) and prints
catalogue, English, translation, one row per hit. A string no catalogue holds prints nothing:
then the program shows it in English, and the page must name it as the screen shows it.
"""
import gettext, glob, os, sys

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    lang, terms = sys.argv[1], set(sys.argv[2:])
    folder = os.path.join(os.environ.get('LOCALE_DIR', '/usr/share/locale'), lang, 'LC_MESSAGES')
    hits = 0
    for mo in sorted(glob.glob(os.path.join(folder, '*.mo'))):
        try:
            with open(mo, 'rb') as f:
                catalogue = gettext.GNUTranslations(f)._catalog
        except (OSError, ValueError, UnicodeError):
            continue
        for key, value in catalogue.items():
            if isinstance(key, tuple) or not key:
                continue
            english = key.split('\x04')[-1]
            if english in terms:
                print('%s\t%s\t%s' % (os.path.basename(mo)[:-3], english, value))
                hits += 1
    return 0 if hits else 1

if __name__ == '__main__':
    sys.exit(main())
