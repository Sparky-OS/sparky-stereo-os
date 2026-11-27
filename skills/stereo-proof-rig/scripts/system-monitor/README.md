# System Monitor in the rig: a real plasma-systemmonitor read through AT-SPI, on recorded machines

The proof of System Monitor's Overview presets ([kde-desktop-defaults, the Overview fitted to the computer](../../../kde-desktop-defaults/references/system-monitor-overview-presets.md)): each row a fresh container with a virtual Stereo KWin, the session's own ksystemstats, the presets' login hook and System Monitor, read back three ways (ksystemstats' sensor list, the screen, every label through AT-SPI).

## Recipe

1. **The image.** `BASE_IMAGE=<debian:testing by digest> HTTPS_ONLY_APT=<the build tree's tools/https-only-apt.sh> CONTAINER_IDS=<lane>/.container-ids LOGS=... bash mkrig.sh TAG REPO_TREE APT_CONF_DIR` (`APT_CONF_DIR`: `sparky-stereo`, `sparky-stereo-only-ours` and `sparky-stereo-deb-multimedia.sources` from the published `sparky-stereo-apt`). It holds Stereo KWin, plasma-systemmonitor, ksystemstats, the Qt Wayland shell plugins, KDE's Qt Quick style, AT-SPI with its GObject bindings, umockdev with `udev` (umockdev-record calls udevadm) and a compiler for the fake input client. `addpkgs.sh IMAGE PACKAGE...` adds a layer; the image with the package installed is one more layer made by `apt-get install /stage/PACKAGE.deb` and committed.
2. **The fake input client:** `../build-fakeinput.sh OUTDIR` inside the image, `OUTDIR/fakeinput` into this folder's `bin/`.
3. **A recorded machine:** `umockdev-record /sys/bus/pci/devices/ADDR /sys/bus/pci/devices/ADDR/hwmon/hwmonN ... > machines/NAME.umockdev`, with the host's `/run/udev` mounted read-only so the cards keep their names (`ID_MODEL_FROM_DATABASE`). On a machine without umockdev, copy `umockdev-record` and `libumockdev.so.0` into a temporary folder and run it with `LD_LIBRARY_PATH`; nothing is installed. Only `/sys` is recorded: `/proc/cpuinfo` stays the host's. `machines/` holds a one-card recording (an AMD Cezanne iGPU alone) and a two-card one (an A10-9600P notebook: Wani iGPU and Sun XT/Hainan, the second with no `gpu_busy_percent`, neither with a power reading).
4. **A row:** `DOCKER_HOST=... OUT=... PKG=<the package source> CONTAINER_IDS=... RIGS=<this skill's scripts/> bash run-case.sh NAME MACHINE=live|/machines/NAME.umockdev HOOK=0|1 [INSTALLED=1 IMAGE=...] [LOGIN_LANG=pt_BR.UTF-8] [ACT=/rig/switch.sh BETWEEN=/rig/relogin.sh STARTS=2] ["APP_ARGS=--page-id history.page"]`. KWin draws on the NVIDIA card through CDI; ksystemstats reads the host's own sysfs read-only (`live`) or a recording through `umockdev-run`; System Monitor uses Mesa's software renderer, `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`, and is maximised by a KWin script.
5. **All rows and their verdicts:** `bash proof.sh` (red and green for three machines, the two-card recording in pt_BR and German, the person's switch with a next login and a restart, KDE's History page as a control); `verify.py CASE MACHINE LANG red|green LANG_DIR` checks each row against expectations written from the recordings, not from the probe's output.
6. **Outside a container** (a test laptop with a fresh account): `session.sh` takes `RIG_HOME` (the account's own home), `RIG_DIR`, `RIGS_DIR` and `FAKEINPUT`; run it with `sudo -u ACCOUNT -H env -i PATH=... HOME=... CASE=... MACHINE=live INSTALLED=1 ...`.

## What each file does

| File | Does |
|---|---|
| `session.sh` | one session: KWin, the AT-SPI bus, ksystemstats, `kstatsviewer --list`, the hook (`--explain`, then the autostart entry's Exec), System Monitor once or twice, capture, AT-SPI reading, the optional action and the step between starts |
| `run-case.sh` | one fresh container per row (`--ulimit core=1`, `--network none`, the NVIDIA card through CDI) |
| `atspi_dump.py` | every accessible object of System Monitor: role, name, text, box, showing, checked (GObject bindings, no pyatspi needed) |
| `switch.sh`, `switch_to_stock.py` | the person's switch to KDE's Overview through Edit Pages: the overflow button by fake input, the menu item through AT-SPI, the dialog by pointer |
| `relogin.sh` | a next login's hook, and a copy of the person's `systemmonitorrc` after it |
| `verify.py`, `proof.sh` | the rows and their verdicts |

## Traps

- A dialog of Kirigami (a popup) and the sidebar's overflow menu items until opened are not in the AT-SPI tree: read positions from a capture; keys sent to a ComboBox's open list did nothing, a click on the item works.
- `kstatsviewer --details` never ends: `timeout`.
- ksystemstats quits when its last client disconnects: start it under umockdev with `--remain`, or D-Bus starts a plain one on the host's sysfs at System Monitor's first call and the row measures the host (`ksystemstats-ps.txt` in each start says which process served the page; `verify.py` checks the card names shown against the recording's).
- In a container with no network and no disks, KDE's own Overview shows "This page is missing some sensors": compare with the red row.
- Never edit a script of a running `proof.sh`: run it from a copy (bash reads scripts as it goes; one edit gave `syntax error near unexpected token '|'` mid-run).
