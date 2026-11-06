# contrib-qt: lessons from the lanes of 25 October to 6 November 2026

Harvested by ORDER 429 from the accepted lane reports; each line names the lane it came from.
A trap gives its symptom, its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Recipes that worked

- Qt example fix through Gerrit: (1) authenticated REST read of codereview.qt-project.org with `path:` (not `file:`) for a file, `message:QTBUG-N` for bug linked changes, status:open/abandoned and history of the file; (2) clone dev depth 50, install the commit-msg hook from the server; (3) one commit, Fixes: QTBUG, Task-number, Pick-to (6.12 6.11 6.8, trimmed by Daniel), Assisted-by, no Signed-off-by from the assistant; (4) prove red and green in a Debian testing container: cmake Ninja Release with an install prefix, `cmake --install`, `readelf -d` of plugin and example, `ldd`, run with QT_QPA_PLATFORM=offscreen and `timeout 8`; (5) push to refs/for/dev with %r=<gerrit usernames>. (lane qt-mystyle-runpath-419)

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: installed attachedstyleproperties example fails with `Cannot load library .../bin/MyStyle/libMyStyleplugin.so: libMyStyle.so: cannot open shared object file` (QTBUG-129784, QTBUG-135094), exit 255. Cause: the plugin installs two directories below the prefix but kept the example's run path `$ORIGIN/../lib`, one level short. Fix: `set_target_properties(MyStylePlugin PROPERTIES INSTALL_RPATH "$ORIGIN:$ORIGIN/../../${CMAKE_INSTALL_LIBDIR}")` guarded `UNIX AND NOT APPLE` (same technique as Qt6CoreMacros.cmake deploy support). Found by: `readelf -d` RUNPATH and `ldd` showing `libMyStyle.so => not found`. Accepted and pushed as Gerrit change 786846. (lane qt-mystyle-runpath-419)
- Symptom: `cmake --install` of a Qt example on Debian's Qt fails with `file RPATH_SET could not write new RPATH ... No valid ELF RPATH or RUNPATH entry exists`. Cause: qt_generate_deploy_qml_app_script's install step; Debian's Qt libraries carry no run path. Fix: leave the deploy script line out of the standalone install proof, identically in red and green, and disclose it. Found by: the install error. (lane qt-mystyle-runpath-419)

## Perks of the part

- Qt Gerrit: the earlier 403 was the unauthenticated REST API, an authenticated token read works; find reviewers by looking at who approved earlier merged changes of the same file and check their recent activity (drop inactive ones); in qtdeclarative no example sets INSTALL_RPATH, so follow what the maintainers' deploy code does. (lane qt-mystyle-runpath-419)

