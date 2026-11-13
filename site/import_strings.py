#!/usr/bin/env python3
"""Import current Markdown, or fail if committed catalogues have drifted."""
import argparse
from model import SITE, dump, extract, load_catalogs, missing_report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = extract()
    missing = missing_report(data)
    if args.check:
        import json
        if data != load_catalogs():
            raise SystemExit('FAIL: catalogues differ from the Markdown. Run python3 site/import_strings.py and review the diff.')
        if missing != json.loads((SITE/'missing.json').read_text()):
            raise SystemExit('FAIL: missing-key report differs; reimport and review.')
    else:
        for lang, catalog in data.items(): dump(SITE/'strings'/f'{lang}.json', catalog)
        dump(SITE/'missing.json', missing)
    for lang, catalog in data.items():
        print(f'{lang}: {len(catalog["pages"])} pages, {len(catalog["strings"])} keys, '
              f'{len(missing[lang]["missing_keys"])} missing, '
              f'{len(missing[lang]["additional_keys"])} additional; absent pages: {missing[lang]["missing_pages"]}')
    print('PASS: all catalogue values have their own source; no translation fallback')

if __name__ == '__main__': main()
