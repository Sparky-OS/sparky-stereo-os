# Required QML modules are runtime dependencies

Symptom: Plank Player exits before opening a window with `QQmlApplicationEngine failed to load component` and `qrc:/qml/main.qml: module "org.kde.desktop" is not installed`.
In the `+stereo3d3` source, `app/main.cpp` selects the `org.kde.desktop` Qt Quick Controls style before loading `main.qml`.
The module is only a `Recommends` in the binary control file.
Removing `qml6-module-org-kde-desktop` version `6.30.0-1+b1` from a disposable rig container reproduced exit 255 with that diagnostic.

A module required by the main QML document or its selected style is a `Depends`.
Looking only for literal QML imports misses styles selected from C++.
An ELF dependency scan does not establish that a QML module will be installed.

## Installation test

1. Check the module name, candidate version and expected archive with `apt-cache policy` inside the packaging container.
2. Begin with a disposable container without the module, with package sources configured over HTTPS and the edition's pins.
3. Install the player's package using `apt-get --no-install-recommends install ./PLAYER.deb`.
   Require the module in apt's installation result and confirm it with `dpkg-query -W`.
4. Start the installed player as a non-root user on the isolated display and require a mapped application window.
   A solver success or a `--version` invocation does not prove the QML root loaded.
5. Keep the old package as the failing control, with the same missing-module starting state and `--no-install-recommends`.

The missing-module startup failure above is verified; the successor's complete installation-and-window test belongs to its package proof.
Do not add the module explicitly to the test image and then claim that the player pulled it in.

## Follow the source-generation route

Inspect the published source's `debian/control`, its patch series and changelog before editing a packaging template.
Plank's shipped successor uses `packages/depth-source/next-source.sh` in the build repository, which modifies the control file from the previous source package.
An edit only to `upstream/qtmultimedia/packaging/plank-player-debian/control` will not change that generated successor.
Check the new source and the built binary's `Depends`, as well as any maintained standalone recipe.
