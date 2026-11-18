# Spell checking follows the session language

The reader is Sonnet 6.30.0, used by Plasma 6.7.4's Spell Check page.
Inspect the installed page before changing a default: missing dictionaries and disabled automatic checking are separate conditions.

## Recipe

1. Install the edition's language package and Sonnet plugin set in the isolated login rig.
   A minimal rig with `--no-install-recommends` can omit the real backend and dictionaries.
2. Compile the look recipe's `tests/spellcheck/sonnet-state.cpp` against the installed Sonnet libraries.
   It reads Settings, Speller and ConfigView without saving them, and creates a Speller for each dictionary language.
3. Run a fresh Plasma login in pt_BR, de_DE and one more dictionary language with `LOGIN_LANG` and `DESKTOP_PROBE`.
   Open the actual installed page with `kcmshell6 kcmspellchecking` and capture it.
4. Compare the page selection, system locale, Settings language, actual Speller language and available dictionary IDs.
   The seven required dictionary languages are en, pl, pt_BR, fr, de, es and ko.
   Japanese and the two Chinese entries have no word-list spelling dictionary in Debian or upstream; morphology and character-variant tables are different data.
   Leave those sessions at Sonnet's own English choice for Latin-letter words.
   Do not write a locale for a nonexistent dictionary or install a new backend for this default.
5. Repeat with a saved user configuration and through a real package upgrade.
   Check the file's bytes before and after, as well as the page's effective values.

## Reader, shipped values and precedence

The KCM is `plasma-desktop/kcms/spellchecking/spellchecking.cpp`.
It creates Sonnet::ConfigView and sets its language from Sonnet::Settings::defaultLanguage().
Sonnet `src/core/settingsimpl.cpp` reads native `QSettings("KDE", "Sonnet")`.
On Linux its system fallback is `/etc/xdg/KDE/Sonnet.conf`, below the person's `~/.config/KDE/Sonnet.conf`.
This is QSettings, not a `sonnetrc` KConfig group.

The recorded configured account differs from Sonnet in **two** keys:

| Key | Sonnet 6.30.0 default | Edition system default |
|---|---|---|
| checkerEnabledByDefault | false | true |
| checkUppercase | true | false |

`Settings::defaultSkipUppercase()` is false, so the default value of **check**Uppercase is its inverse, true.
The look package supplies only these two keys in `[General]`.
Autodetection and background checking already default to true; the default client is already empty.
Do not write those keys or `defaultLanguage`.
`Settings::defaultLanguage()` follows `QLocale::system().name()`, and ConfigView chooses an available dictionary.
A person's saved automatic-checking, uppercase or language value wins independently over the system default.
Sources: [settings implementation](https://github.com/KDE/sonnet/blob/v6.30.0/src/core/settingsimpl.cpp), [Settings defaults](https://github.com/KDE/sonnet/blob/v6.30.0/src/core/settings.cpp), [ConfigView](https://github.com/KDE/sonnet/blob/v6.30.0/src/ui/configview.cpp).

## Traps

- **Symptom:** a Japanese case reports `isValid=true` but uses en_US.
  **Cause:** validity alone does not identify the dictionary; Speller falls back to an installed language.
  **Fix:** compare actual language and the inventory; explicitly list the three entries without word-list data and preserve Sonnet's choice.
  **Found by:** a fresh ja_JP login, native Speller output and the installed page capture.
- **Symptom:** only automatic checking is copied although the recorded account also disables uppercase checking.
  **Cause:** confusing the positive checkUppercase key with the negative skipUppercase API.
  **Fix:** read settingsimpl.cpp together with settings.cpp and invert the defaultSkipUppercase value.
  **Found by:** source inspection and the predecessor's native `checkUppercase=true` result.
- **Symptom:** a proposed sonnetrc leaves the page unchanged.
  **Cause:** the current release reads KDE/Sonnet through QSettings.
  **Fix:** install the system-scope file below the user's file and measure both states.
  **Found by:** inspecting the exact release's SettingsImpl before shipping the change.
- **Symptom:** kcmshell6 is absent although kde-cli-tools is installed.
  **Cause:** libkf6kcmutils-bin supplies it in this release.
  **Fix:** install that verified rig dependency.
  **Found by:** the failed probe and installed package/file inventory.
