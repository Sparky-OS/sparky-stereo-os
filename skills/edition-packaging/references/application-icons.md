# Application artwork in the installed icon theme

## A window has the right app_id but its task bar tile is blank

**Symptom:** Spirula Studio's task bar tile and title-bar icon are empty, and its launcher-menu entry has the generic document icon.
The installed desktop entry names `spirula-studio`, matching the Wayland app_id.
Qt loads the PNG by its absolute path at every requested size, but `QIcon.fromTheme` is null at 16 through 512 px.
Rebuilding the icon cache alone leaves that lookup null.

**Cause:** the package put its only PNG under `hicolor/1024x1024/apps`, which the installed hicolor `index.theme` does not list.
The icon-theme lookup algorithm searches the directories declared by the theme.
Spirula's upstream runtime registration supplies a 128 px icon by absolute path; our edition build correctly leaves menu registration to the package instead.
Its earlier Wayland app_id fix, Guozhongyuan's upstream PR #107, was already present.

**Fix:** install the project's own artwork at indexed sizes, including 48 px, and let the normal icon-cache machinery run during installation.
Keep an existing original file when another consumer may use its path.
Generate the sizes deterministically from the original artwork; do not redraw it or turn a failed theme lookup into an absolute-path workaround in the desktop entry.
The icon-theme specification's application-installation section requires a 48 px hicolor icon at minimum.

**How found:** compare the actual installed theme index, named and direct-path Qt lookups, an independent cache-only control, and full compositor captures of the task bar, launcher menu and window title bar before and after the package update.
Inspect those three locations by eye as well as checking file lookup.
A matching app_id alone proves neither that artwork is discoverable nor that Plasma draws it.

Sources: [Icon Theme Specification](https://specifications.freedesktop.org/icon-theme/latest/), [Guozhongyuan's merged app_id fix](https://github.com/harry7557558/spirula-studio/pull/107), Spirula Studio's `src/app/gui/DesktopEntry.cpp` and `tools/package_macos.sh`.

## Reuse compiled programs for an artwork-only successor

Keep the ordinary cold source build available.
A packaging-only path names the exact qualified predecessor archives and their source/build record by hash, and refuses changed native source, components or runtime controls.
Restore authored text through its verified HR companion before the new payload projection; never project an already projected file again.
Record which recipe compiled the carried executables and which recipe assembled the successor.
Compare the final executable bytes directly, requalify all changed archives, and explain every changed or removed payload member against the predecessor.
Do not repeat the stereo matrix when both compiled programs are byte-identical and the task explicitly preserves its accepted measurements.

Trap: a source-input guard refuses many unchanged files because their modes changed from 0644 to 0664 while copying a Git checkout.
The cause is the checkout's umask, not a content change.
Use the edition's normal source normalizer before sealing the .dsc, then keep the guard strict.
The refusal's mode/hash table distinguishes identical bytes with changed modes from actual source edits.

Trap: an offscreen Qt probe reports every installed icon missing because its theme search path contains only `:/icons`.
Read `QIcon.themeSearchPaths()` before trusting that result.
Give the probe the installed `/usr/share/icons` path and rerun the old, cache-only and successor controls.
The corrected probe still fails on the unindexed predecessor and succeeds on the indexed successor, matching the actual Plasma captures.
