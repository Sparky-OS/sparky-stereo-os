# Auditing a program's 3D options

Written on 2026-11-13, from an audit of every program in the edition's published repository.
It lists the 3D options a packaged program offers without running it, and sorts each one by the contract in [the general skill](../SKILL.md#part-one-the-contract).
Use it before a program's package is accepted, and again whenever its menu changes.

## The rule an option is measured against

A program in the edition offers three 3D options: enable 3D, the render resolution per eye, and a shortcut to Display Configuration.
A program that shows media files adds two corrections of its input, for each file it shows in 3D: the input packing, and "Swap left and right eyes".
Depth, separation, the screen plane, the kind of display and every output format belong to Stereo KWin.
The audit cuts both ways: an option the rule does not allow is one finding, and an option the rule asks for and the program lacks is another.

## Recipe

1. **Name what ships.**
   Read the published repository's `Packages` index, not a recipe folder: `Package`, `Version`, `Source` and `Filename` give the binary packages of each source.
   Write down the tree you read and the `Date:` of its `InRelease`.
   A package that is built but not yet published is listed apart, with its own version.
2. **Read what we added.**
   The source's `debian.tar.xz` holds `debian/patches/series` and the patches; the added lines (`+`) that carry `i18n(`, `tr(`, `.label =`, `<string>` or a command-line option are the options we wrote.
   `tar -xOf SOURCE.debian.tar.xz --wildcards '*NAME.patch'` prints one patch without unpacking the rest.
3. **Read what is installed.**
   Unpack one package at a time (`dpkg-deb -x PACKAGE.deb DIR`), read it, remove it.
   Where each kind of program keeps its options:

   | Kind | Where the options are |
   |---|---|
   | KDE program | `usr/share/kxmlgui5/*/*.rc` (menus and toolbars), `usr/share/config.kcfg/*.kcfg` (settings and their labels), `*.desktop` (`Actions=`), `*.notifyrc`, the binary's own strings for `i18n()` labels |
   | Qt Widgets | `.ui` forms compiled into the binary: labels and object names (`kcfg_...`, `label_...`) show in `strings` |
   | Qt Quick | `.qml` files under `usr/lib/*/qt6/qml` or compiled into the binary; a `.qmltypes` file lists a module's properties |
   | GTK program | `.ui` and `.glade` files, `usr/share/glib-2.0/schemas/*.gschema.xml` (settings keys), the binary's strings |
   | Browser built on Gecko | `omni.ja` and `browser/omni.ja` are zip archives: `localization/en-US/browser/*.ftl` holds every label, `chrome/browser/content/browser/browser.xhtml` the menu items by id, `defaults/pref/*.js` the package's preferences; `strings` on `libxul.so` lists the preference names the code reads |
   | Program with its own language files | the English file (`lang/English/*.lng`, a `Translations/*.xml`, a `.json` of strings) |
   | Library | environment variables and configuration keys in `strings`: a library's own stereo modes reach every program built on it |
   | Command-line tool | the option table in `strings` (`--name`), the manual page, a `.desktop` service menu's `Name=` lines |

4. **Search with the families, then read the hits.**
   Enable: `Enable 3D`, `Stereo 3D`, `--stereo`.
   Resolution: `per eye`, `render resolution`.
   Shortcut: `kcm_kscreen`, `Display Configuration`, `Display Settings`.
   Packing: `side by side`, `top and bottom`, `interleaved`, `checkerboard`, `frame sequential`, `anaglyph`.
   Swap: `swap` near `eye`.
   Output: `anaglyph`, `interlace`, `page flip`, `cross-eyed`, `parallel pair`, `left view`, `right view`.
   Depth: `separation`, `eye distance`, `convergence`, `parallax`, `screen plane`, `focal`.
   Store: `user.` (extended attributes), `setxattr`, the name of the program's own state file.
5. **Sort each option** (next section), and write for each: the package and version, where the option is (menu path, settings page, key, command line, environment variable), what the person sees, what it does, the class, and for an extra the patch or build switch that removes it.
6. **List what is missing** per program in a table of its own.
7. **Say how each row was read:** from the patch, from an installed file, from the binary's strings, or by running the program.
   A row read from strings alone says so.

## The classes

| Class | Rule line behind it |
|---|---|
| Enable 3D | the rule above, its first option |
| Render resolution per eye | the second; "Internal rendering resolution is not output resolution" |
| Shortcut to Display Configuration | the third; "Per-monitor settings live in one place" |
| Input packing, per file | "Programs decode or generate stereo in any standard"; every packing of the specification, both eye orders |
| Swap left and right eyes, per file | "The definitive eye swap is the output's"; the program offers "only the per-file correction of its input ... and only for content it shows in 3D" |
| Other input option (a detector on or off, a decoder path, the options of picture-with-depth content) | "When two ways give the person different results, build them all" |
| Output mode or output module: extra | "A program that has its own output modes loses them" |
| Separation, depth, screen plane, convergence, kind of display: extra | the rule above: these belong to Stereo KWin; "Per-monitor settings live in one place" |
| A swap for everything the program shows: extra | "A program offers no swap of its own for everything it shows" |
| A 3D correction offered on 2D content: extra | "only for content it shows in 3D" |
| A per-file choice written into the file without the person's word: finding | "Never touch the user's file on your own" |
| A server that feeds another device | not a desktop program: "The network is not the desktop"; its formats are that device's |
| No rule covers it | listed with what the person sees, for the person who decides |

A choice between two ways of doing the same input work is never an extra.
A choice of what reaches the screen always is.

## Traps

- **Symptom:** a Qt Quick program shows no 3D label in `strings`, yet it has a 3D menu.
  **Cause:** QML compiled into the binary keeps its strings as UTF-16.
  **Fix:** `strings -el` beside plain `strings`, and the patch series first.
  **How found:** a player whose patch added a menu gave two matches in the plain listing and the menu's lines only with `-el`.
- **Symptom:** the binary holds the labels of output modes the build was meant to drop.
  **Cause:** the labels sit in a language file or a string table that is always shipped, while the menu that used them is compiled out by a build switch.
  **Fix:** read the function that builds the menu in the published source (`tar -xf SOURCE.tar.xz --wildcards '*MenuFile.cpp'`), and report an action that only a key can still reach apart from a menu item.
  **How found:** a viewer's `#ifndef` around its display-mode menu, with the action names still in the library.
- **Symptom:** a browser package looks clean in a file scan and still has a depth menu.
  **Cause:** the interface is inside `omni.ja`, which a scan of text files skips.
  **Fix:** unzip both archives into scratch and read the `.ftl` labels with the `browser.xhtml` ids; list the preference names from `libxul.so`, since a preference with no menu item is still a setting.
  **How found:** the patch added `.label =` lines that no installed text file held.
- **Symptom:** the audit reports a menu that the person no longer has, or misses one they do.
  **Cause:** the build tree, the staged package and the published package are three different versions.
  **Fix:** read the published package for "what ships", and name a staged or merged version in its own row.
  **How found:** the published package and the staged one of the same program differed by a whole menu.
- **Symptom:** hundreds of false matches.
  **Cause:** the words are shared with sound and video: stereo sound, interlaced scanning, buffer swaps, bit depth, colour separation, red-eye removal, convergence of a solver.
  **Fix:** drop lines with `audio`, `deinterlac`, `SwapBuffers`, `swapchain`, `bit depth`, `depth buffer`, `red eye`, and symbol names; then read what is left instead of counting it.
  **How found:** a video editor's effect list filled the first listing.
- **Symptom:** an option is in no menu and still changes everything the program shows.
  **Cause:** it is a saved preference, a command-line option or an environment variable.
  **Fix:** read the option table in the source (`add_bool`, `add_string`, an option parser, a `getenv`) and say whether the value is kept between runs.
  **How found:** a player's swap option declared as an ordinary saved setting beside its per-file one.
- **Symptom:** a program built on a scene library has an anaglyph mode nobody added.
  **Cause:** the library reads its own stereo mode from an environment variable or a property.
  **Fix:** audit the library once and name every program built on it.
  **How found:** the mode names in the library's strings, and the program's own message refusing them.
- **Symptom:** `grep -o` stops with "exceeds complexity limits".
  **Cause:** the system's `grep` is ugrep, which refuses a pattern with large counted repeats.
  **Fix:** extract quoted strings with a few lines of Python.
  **How found:** the error text itself.

## What the audit does not prove

Reading files shows that an option exists, not when the program enables it.
Whether "Swap left and right eyes" is greyed out on a 2D file, and where a per-file choice is written, are proved only by running the program in the proof rig ([stereo-proof-rig](../../stereo-proof-rig/SKILL.md)) or by reading the code that sets the item's state.
Say which rows rest on strings alone.
