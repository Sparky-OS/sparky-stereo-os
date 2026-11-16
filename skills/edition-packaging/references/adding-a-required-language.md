# Adding a required language to the whole edition

**For** anyone who has to add one language to every string the edition ships (German in ORDER 290, Spanish in ORDER 507): what to scan, where the language lists hide, and the traps that stopped a generator or a test.

## Recipe

1. **Audit first, change nothing.** Run a read-only script over the clone: `git ls-files`, and for each text file that names `zh_TW` (the longest-named member of the set, so every list contains it) check for the new code. Classify by kind: `lang/` folders (en is the key list), `po/LANG` sets, `.po.patch` files (look for `+++ b/po/es/`), `.desktop` / `.actions` / `.notifyrc` / `.policy` / KDE `.json` (`[es]`, `xml:lang="es"`, `"es":`), JSON string tables and slides, Qt `.ts` files, recipe patches that add strings, and every test, generator and check script with a hard-coded list. A second pass finds lists spelled another way (`pt_BR` and `ko` and `ja` without `zh_TW`: kubabbar-glass's checks had never listed `de`). Keep the table as a TSV beside the report; its "already has" column has false positives (a regex for ` es ` matches locale names such as `es_AR` in locale lists, and the English word "es" in prose), so read every OK row once.
2. **Fill by kind, one commit per package or string set.** Existing lines stay byte for byte; generated files change through their generator (gen.py, make-pack.py, the slides' fill-ts.py) and the old languages' output must come out identical, which is the proof the generator ran the same way.
3. **Add the code to every list**, tests and generators together, then run each changed test red (remove one new entry in a scratch copy, the test must name it) and green.
4. **Say what only a rebuild can fix**: `tests/translations-shipped.py` reports the language missing from the built packages until the next publication round. Do not silence it.

## Where lists hide

- Tuples and sets in Python tests: `('en', 'pl', 'pt_BR', 'fr', 'de', 'ja', ...)`, `LANGS =`, `REQUIRED =`, `languages =` plus a plural-forms table keyed by language (`nplurals`).
- Shell: `for l in en_US pl_PL ...` (locale names: es_ES), `case $l in pt_BR|zh_CN|zh_TW) code=$l ;; *) code=${l%_*} ;; esac` (a bare language needs no entry), `LANGUAGES=(...)`, associative arrays `[de]=de_DE`, `pair` lists with an expected phrase per language (each needs a Spanish phrase from the new catalogue).
- Zig and C: `const nine = [_][]const u8{...}`, `static const char *const languages[]`; the language-picking function itself (`lang_lookup.pick`) takes the available list as data and needs no edit.
- Generators with the strings inside (`gen.py`): a `LANGS` list and one dict per language; a missing key stops them, which is the point.
- Names that still say "nine" in test titles, comments and `_about` texts: change what the code uses, say in the report what you left.

## Traps

- **Symptom:** a test passes on a new language although nothing is translated. **Cause:** glibc's gettext translates nothing in `C` and `C.UTF-8`, so the English equals the English. **Fix:** `localedef -i es_ES -f UTF-8 es_ES.UTF-8`, set `LANG` to it, require the text to differ from English. **Found by:** reading the German precedent in the lessons (ORDER 298b).
- **Symptom:** the generated polkit policy has an empty `<message xml:lang="es">`. **Cause:** `.actions` is read as a QSettings INI file and an unquoted comma makes a list. **Fix:** quote every translated value that holds a comma and check the generated policy, not only the file.
- **Symptom:** a `.po.patch` hunk drops lines silently. **Cause:** the `+1,N` count in the `@@` header is shorter than the lines added. **Fix:** recount each added hunk; `tests/validate-po-patches.py` checks it.
- **Symptom:** a language never reaches the person although its file exists. **Cause:** a `LANGS` list in the generator or installer (make-slideshow.py listed no `de` either) so the file is never written or never chosen. **Fix:** add it to the list, and make the list the same one the test reads.
- **Symptom:** a test compares a whole phrase for each language and has no Spanish. **Fix:** take the phrase from the new catalogue's own line (the test must fail if the catalogue falls back to English).
- **Spanish specifics:** one `es` catalogue, no territory variants: the lookup (whole `LANG`, bare language, English) serves es_ES, es_MX and es_AR. Terms follow KDE's own Spanish catalogues (read them with Python's `gettext.translation(domain, '/usr/share/locale', languages=['es'])`); several older host catalogues return the English key for newer Plasma strings, so check a term in more than one domain.
- **Symptom:** the audit says a file is done and the language is still missing in it. **Cause:** the "already has it" regex was written for `'es'` and `[es]` but a list can spell it `es*)`, `es_*)`, `es | es_*`, `pl|fr|de|es|ja`, or `LANGS = (...)` with the code last in a line. dpkg-stereo's `LANGS` tuple was found only by the second audit run after the fill. **Fix:** run the audit again after the fill with the spellings of every list you edited, and open each file that still reports MISSING.
- **Symptom:** older lists never had `de` either (kubabbar-glass's two check scripts, the installer slides' `make-slideshow.py` `LANGS`, the browser build's locale list). **Cause:** German was added to the packages and tests that existed that day. **Fix:** add the missing earlier language in the same commit and say so in the report; a generator whose list lacks a language also overwrites that language's finished file with an empty skeleton when it is rerun.
- **Symptom:** a test needs a language-specific phrase and the new catalogue's line is not what you guess. **Fix:** copy the phrase out of the `es` file the test reads (`grep '^LOCAL7=' lang/es`), never from memory, so the test fails if the catalogue is missing.
- **Symptom:** a package's tests fail in a clean container with or without your change. **Cause:** they need the installed package set (yad, wine, clamtk, kreadconfig6, `sparky-stereo-problems`). **Fix:** run the unchanged tree first (`git archive BASE path | tar -x` into scratch) and compare the failing names; your change must add only the new language's subtest, and the rest is reported as not runnable here.
- **Browser locale lists** (`./mach package-multi-locale --locales ...`) take Mozilla's own codes, and Mozilla has no bare `es`: `es-ES`, `es-AR`, `es-CL` and `es-MX` are separate locales. Name the choice in the report instead of inventing one; the edition's one `es` catalogue is for the strings the edition adds.
- **A Dolphin pack generator** (`gen.py`) writes `pack.json` and `lang/<code>` into the OUT-DIR you give it and no checked-in output, so the proof is: run it before and after into scratch and diff; the other languages' files must be identical and the new one must pass `bash -n`.
- **Test rig:** a Debian testing container with python3, gettext, locales, libxml2-utils, desktop-file-utils, python3-tk, dpkg-dev, libkf6config-bin, gcc and the ten locales generated with `localedef -i es_ES -f UTF-8 es_ES.UTF-8` (and the others) ran the pure-Python checks (saver receipts, integrations, check-translations, generators) as uid 1000 with the network off.

## The 3D switch's label: one name in the ten languages (ORDER 586)

The program switch "Enable 3D" (`Stereo::Enable3DAction`) keeps one name per language in every program the edition ships (same-ideas-same-names-everywhere). As shipped after ORDER 586 (2026-11-15):

| Language | Label of "Enable 3D" |
|---|---|
| en (source) | Enable 3D |
| de | 3D aktivieren |
| es | Activar 3D |
| fr | Activer la 3D |
| ja | 3D を有効にする |
| ko | 3D 사용 |
| pl | Włącz 3D |
| pt_BR | Ativar 3D |
| zh_CN | 启用 3D |
| zh_TW | 啟用 3D |

pt (Portugal) is a different language: the switch has no `pt` translation (Dragon's `po/pt` carries none and there is no `pt` hunk in the patches), so there is nothing to change there; do not let an `es` form leak into a `pt_BR` catalogue: `Activar 3D` is the Spanish label, and the identical spelling is a trap.

Where it lives: the stereo layer's `po/pt_BR/stereo-layer_qt.po`, sView's `lang/portuguesebr/*.lng` (`1461=Ativar 3D`), the gl-stereo launcher's `launcher-strings.json` (`"pt_BR": "Ativar 3D"`), and the `.po.patch` hunks the recipes add to Dragon Player, Haruna and the depth-source patches under `sparky-os/translations/`.

The grep that finds a drifting pt_BR form (run in the build tree; patch files match too because their hunks are the future language lines):

```sh
git grep -n -E 'msgstr "(Ativar o|Habilitar|Ligar|Instalar|Energizar) 3D"' -- '*.po' '*.po.patch' || echo "no drift"
grep -rn -B1 -E 'msgstr "Ativar o 3D"' published-src/*/po/pt_BR/*.po
```

A hit with an old form (`Ativar o 3D` was the drift ORDER 586 fixed in Dragon and Haruna) must be changed to the table's line, never to a new wording; the reverse check that every shipped pt_BR catalogue names the expected form is `grep -rn -A1 'msgid "Enable 3D"' */po/pt_BR/*.po`: every `msgstr` must read `Ativar 3D`, and a recipe patch that adds or fixes the string is proven in place: `patch -p1` it onto the pristine unpacked source in a container, then `msgfmt -c -o /dev/null` the changed catalogue.

## Traps met in ORDER 507b (Spanish leftovers)

- **Symptom:** a catalogue reads fluently and names another thing: the Spanish installer slides said "auriculares de RV" for "VR headsets" and "sin necesidad de auriculares" for "no headset needed", while a third slide used "auriculares" for "headphones". **Cause:** "headset" was taken for "headphones"; the two English words had become one Spanish word in one catalogue. **Fix:** take every new term from the language's published glossary (the front pages' glossary row for "VR headset" is "casco de realidad virtual") and write that word in the catalogue and the JSON table that generates it (`slides-*.json` and `calamares-sparky_es.ts` together: `tools/fill-ts.py` run into a scratch copy must reproduce the `.ts` byte for byte). **Found by:** reading the glossary's row against the catalogue, then this check, which lists every translation of a string holding "headset" or "headphone": the two words must not share a translation in one catalogue.

  ```python
  import sys, collections
  import xml.etree.ElementTree as ET
  by = collections.defaultdict(list)
  for m in ET.parse(sys.argv[1]).iter('message'):
      for w in ('headset', 'headphone'):
          if w in m.find('source').text.lower():
              by[w].append((m.find('source').text[:50], m.find('translation').text))
  for w, rows in by.items():
      print(w); [print('  ', r) for r in rows]
  ```

  Run it on each language: German "Headset", French "casque" (also the French word for headphones; the neighbouring slide says "casques de réalité virtuelle"), Polish "gogle" and Portuguese "óculos VR" keep the two ideas apart; Japanese "ヘッドセット" and "ヘッドホン", Korean "헤드셋" and "헤드폰", Chinese "头显" and "耳机" do too.
- **Symptom:** the tree has a catalogue for the new language and the installed system shows English. **Cause:** no built package carries it: the last published version of the package predates the catalogue (the Spanish installer slides were committed on 10 November, the published `sparky-stereo-calamares-branding` was built on 2 November and holds nine `.qm` files). **Fix:** a new version of the package; the proof is its `lang/` folder (`dpkg-deb -x` and list `calamares-sparky_es.qm`). **Found by:** listing the published package's files instead of trusting the commit log.
- **Symptom:** an audit of the tree says a string has no translation in any language, and the published package shows eight of them. **Cause:** the build tree no longer holds the patch that gave them; the published source's own `debian/patches` still carries it (kscreen's `kscreen-stereo.po.patch`, named in the series of every successor). **Fix:** ask the published binary: read its `.mo` with Python's `gettext.GNUTranslations` for each language and msgid and print "UNTRANSLATED" where the answer equals the key (no program of the package runs; the C locale problem above does not apply to reading a `.mo`). Then add only what is missing.

  ```python
  import gettext, sys
  root, domain, *ids = sys.argv[1:]
  for l in ['de','es','fr','pl','pt_BR','ja','ko','zh_CN','zh_TW']:
      t = gettext.GNUTranslations(open(f'{root}/usr/share/locale/{l}/LC_MESSAGES/{domain}.mo', 'rb'))
      for i in ids:
          r = t.gettext(i)
          print(l, i[:30], 'UNTRANSLATED' if r == i else r[:70])
  ```
- **Where a KDE program's added strings get their translations in the build tree:** KDE's own catalogues come from the release tarball (`po/<lang>/<domain>.po`); the strings the edition adds are carried as `sparky-os/translations/<program>-<feature>.po.patch`, a unified diff that appends to those files, named last in the package's `debian/patches/series` through the recipe's overlay folder (`overlay-stereo3dN/patches/series` for a Lean Code successor, `lc-successor.py --in-place --overlay`). A language the tarball already has (Spanish has `po/es/kcm_kscreen.po`) takes an appended hunk; a language it lacks needs the whole file in the patch. Check the hunk with `patch -p1 --dry-run` on the unpacked staged source and `msgfmt -c --check-format` on the result, add the patch to `SOURCES` in `tests/translations-shipped.py`, and give the README a line. The QML `i18n("...")` text is its msgid, with no context.
- **A successor of a source that depends on staged packages** (kscreen +stereo3d13 needs libkscreen +stereo3d12, which only a staged folder holds) builds with the staged `.deb` files as a second flat repository (`file:/repo2 ./` with the edition's origin so the 1001 pin applies) and the same files listed in `SPARKY_LC_SIBLINGS_FILE`, or the link and start gate in `override_dh_builddeb` stops with "kscreen Depends libkf6screen8 (>= ...) but none of the choices are installable". The gate's `sources.json` names the published tree as `file:/repo` (suite `mashtabba`, the repository key dearmored).
- **A standalone script package** (`sparky-stereo-calamares-branding`) builds with `bash build.sh`, which needs `lrelease` (`qt6-l10n-tools`) and for its JavaScript and QML files `nodejs` with `node-acorn` ("check failed: no independent tokenizer (node with acorn) available" otherwise); `lean.release check-debs` stops "release blocked: the build script did not call sparky_provenance_init" until the driver sources `sparky-os/repo/build-provenance.sh` and passes `"${SPARKY_PROV_ARGS[@]}"`. Its build record says "unrecorded: buildinfo", as the published one's does.
