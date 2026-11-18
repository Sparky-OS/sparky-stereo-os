# Inspect spell checking before setting defaults

ORDER 670 inventory, Plasma 6.7.4 and Sonnet 6.30.0.
This reference records the reader and the diagnostic recipe; it does not claim that dictionaries for all ten edition language entries have been supplied.

## Recipe

1. Read the installed language package set, the Sonnet version and the actual Spell Check KCM before adding a configuration file.
   Include Sonnet's recommended plugin and the dictionaries the edition already lists in the baseline.
   A minimal `--no-install-recommends` rig can omit those and give an artificial empty result.
2. Build the look recipe's `tests/spellcheck/sonnet-state.cpp` against the installed libraries in a container, with CMake, make and a C++ compiler.
   The helper reads Settings and Speller, and the same ConfigView language selector that the KCM uses, without saving settings.
3. Use `stereo-proof-rig/scripts/login-splash/run-case.sh` with `LOGIN_LANG` set to a generated locale and `DESKTOP_PROBE` set to `tests/spellcheck/probe.sh`.
   Use a separate fresh login for pt_BR and at least two other required language entries.
   Mount the helper at `/test-bin/sonnet-state`; the probe opens the installed page with `kcmshell6 kcmspellchecking` and captures it.
4. Read system locale, Settings default language, the page's selected dictionary, Speller language, backend clients and every available dictionary separately.
   Run `check-inventory.py` against the JSON; an unavailable required entry or wrong selected language must fail.
5. Only after this inventory, change what is missing and repeat the installed page and user-override cases.
   Do not replace an unavailable language with English and call it configured.
   A lexical conversion or morphology table is not evidence of a usable spelling dictionary.

## The reader and existing behavior

The KCM is `plasma-desktop/kcms/spellchecking/spellchecking.cpp`.
It creates Sonnet::ConfigView and calls `setLanguage` with Sonnet::Settings::defaultLanguage().
In Sonnet 6.30.0, `src/core/settingsimpl.cpp` uses native `QSettings("KDE", "Sonnet")`, whose Linux configuration file is `KDE/Sonnet.conf`, rather than a `sonnetrc` KConfig group.
`src/core/settings.cpp` supplies `QLocale::system().name()` as the default language.
`src/ui/configview.cpp` selects an available dictionary in its combo box.
Read those sources for the installed release before carrying an older spelling configuration forward.
Sources: [Sonnet settings implementation](https://github.com/KDE/sonnet/blob/v6.30.0/src/core/settingsimpl.cpp), [default language](https://github.com/KDE/sonnet/blob/v6.30.0/src/core/settings.cpp), [ConfigView](https://github.com/KDE/sonnet/blob/v6.30.0/src/ui/configview.cpp).

With the seven relevant dictionaries already listed by the edition installed, the measured Portuguese and German pages select pt_BR and de_DE.
The Japanese session has `defaultLanguage=ja_JP`, but both the page and Speller select en_US.
Speller still reports valid.
The dictionary inventory lacks ja_JP, zh_CN and zh_TW.
The automatic-checking-by-default checkbox is also unchecked; record that separately from dictionary selection and availability.
This is a measured prerequisite gap, not proof that the missing language support cannot be implemented.
The ten-entry requirement needs verified spelling dictionaries and compatible checking behavior before a complete default can be claimed.

## Traps: symptom, cause, fix, how found

- **Symptom:** a Japanese case passes a checker-validity assertion while using English.
  **Cause:** Speller falls back to an installed dictionary; validity alone does not establish its language.
  **Fix:** compare the system locale, configured language, page selection, actual Speller language and available dictionary IDs.
  **Found by:** a fresh ja_JP login returned `isValid=true` alongside `spellerLanguage=en_US`; the installed page capture also showed American English.
- **Symptom:** a proposed `sonnetrc` file leaves the current page unchanged.
  **Cause:** that proposal targets the older configuration reader; Sonnet 6.30.0 uses the KDE/Sonnet QSettings namespace.
  **Fix:** inspect the exact release's SettingsImpl before writing a default; retain the native user-over-system fallback behavior.
  **Found by:** source inspection before making a shipping change; this was prevented, not observed as a failed package upgrade.
- **Symptom:** the page probe exits with `kcmshell6: command not found` although kde-cli-tools is installed.
  **Cause:** the launcher is supplied by libkf6kcmutils-bin in this release.
  **Fix:** install that verified test dependency; do not replace the actual page with a stand-in.
  **Found by:** the failed probe log and the installed package/file inventory.
- **Symptom:** apt update in a derived rig image says its `file:/repo` source has no Release file.
  **Cause:** the image retains the source definition but the derived builder omitted the repository mount.
  **Fix:** mount the frozen repository read-only during apt operations, with the HTTPS helper and CA mounts as usual.
  **Found by:** the derived builder's apt error; no shipping configuration change was needed.
