# Session, menu, sound and battery defaults

ORDER 668, measured on Plasma 6.7.4 in fresh private `startplasma-wayland` logins.
The look package and power-profiles package supply system defaults, never a login-time rewrite of the person's settings.

## Recipe

1. Merge existing defaults work into the current build main, preserving newer look assets and dependencies.
2. Build the look and power-profiles successors from committed recipes.
   Rebuild each `.dsc`, compare binary payloads and controls, and run the Lean Code package gate.
3. Build the predecessor rig with `stereo-proof-rig/scripts/login-splash/mkrig.sh`, installing the precise staged predecessor over the published repository.
   Include the published power-profiles package explicitly; installing the look alone does not establish a power baseline.
4. Run the look recipe's `tests/login-defaults/probe.sh` as `DESKTOP_PROBE` in a fresh login.
   Require the old configuration and live launcher to fail the new expectations.
5. Upgrade both packages with apt, with no removals.
   Run the same probe in a fresh successor login and require all expectations to pass.
6. Retain the predecessor's panel and save explicit opposite choices for every changed configuration key.
   Hash this home before and after the package upgrade, then supply it as `CONFIG_SEED` to another fresh successor login with `EXPECT_USER=1`.
   Require the existing panel and every saved choice to survive.

Use one container and one session per case, `--ulimit core=0`, an isolated runtime directory and the lane's Docker socket.
The probe queries the actual panel through `org.kde.PlasmaShell.evaluateScript`, then reads the installed KConfig layers inside that session.
A configuration result does not prove physical brightness, battery-triggered shutdown, audible playback, application restoration or a logout dialog.
State those limits separately.

## Each default and its reader

| Default | Where KDE reads it and how a new account receives it | How a person's choice survives |
| --- | --- | --- |
| Application Menu (`org.kde.plasma.kicker`) | The edition look's `contents/layouts/org.kde.plasma.desktop-layout.js` creates the initial panel with Kicker | The script creates a panel only when `panels().length === 0`; an existing panel remains as saved in `plasma-org.kde.plasma.desktop-appletsrc` |
| Start an empty session | `ksmserver/main.cpp` reads `ksmserverrc [General] loginMode`; `/etc/xdg/ksmserverrc` supplies `emptySession` | A saved `loginMode` in the person's file wins |
| No logout confirmation | `libkworkspace/sessionmanagementbackend.cpp` reads `ksmserverrc [General] confirmLogout`; `/etc/xdg/ksmserverrc` supplies `false` | A saved `confirmLogout=true` wins; explicit ForcePrompt callers remain possible |
| Oxygen sounds | `/etc/xdg/kdeglobals [Sounds] Theme=oxygen`, with `oxygen-sounds` in Depends | The person's `[Sounds] Theme` wins; keep other installed sound themes |
| Low battery 25%, critical 15%, critical action 8 (shutdown) | `PowerDevilGlobalSettings.kcfg` reads `powerdevilrc [BatteryManagement] BatteryLowLevel`, `BatteryCriticalLevel`, `BatteryCriticalAction` | Each saved key in the person's `powerdevilrc` wins |
| AC display 100%, profile-specific display brightness enabled on AC and Battery | `PowerDevilProfileSettings.kcfg` reads `[AC][Display] DisplayBrightness` and `[AC][Display]`, `[Battery][Display] UseProfileSpecificDisplayBrightness` | System defaults stay below the person's keys; Battery's brightness amount is unchanged |
| AC keyboard 100%, low-battery keyboard 11%, profile-specific keyboard brightness enabled on all three profiles | `PowerDevilProfileSettings.kcfg` reads each profile's `[Keyboard]` group: `KeyboardBrightness` and `UseProfileSpecificKeyboardBrightness` | Each saved amount and enable flag wins; Battery's brightness amount is unchanged |

The keyboard enable flags belong to the recorded machine settings, alongside the brightness amounts.
Do not infer additional battery, display, keyboard or idle defaults.
Keep system files as conffiles and do not set KConfig immutable markers.
The packaged source schemas establish the exact nested group names; do not copy names from an older KDE generation.
The session readers are in [plasma-workspace](https://invent.kde.org/plasma/plasma-workspace); the PowerDevil schemas are `PowerDevilGlobalSettings.kcfg` and `PowerDevilProfileSettings.kcfg` at [the repository root](https://invent.kde.org/plasma/powerdevil).

## Traps: symptom, cause, fix, how found

- **Symptom:** merging the earlier defaults branch conflicts in the look builder and reintroduces an older splash dependency.
  **Cause:** a newer loading-screen milestone changed the same recipe lines.
  **Fix:** retain current main's splash files, preview, retained selectable theme and dependency floor, then add the session conffile and sound dependency.
  **Found by:** merge conflict inspection and byte-for-byte archive comparison of every splash, preview and `ksplashrc` member.
- **Symptom:** D-Bus returns an empty string although the Plasma scripting expression produced a value.
  **Cause:** `evaluateScript` returns script print output.
  **Fix:** use `print(JSON.stringify(...))` for the live panel query and parse that output.
  **Found by:** the saved empty D-Bus response and JSON parse failure in the first predecessor probe.
- **Symptom:** the power package assembles but its `.dsc` rebuild refuses unmet build dependencies.
  **Cause:** the build image did not configure `sparky-stereo-problems`, whose dependency includes systemd.
  **Fix:** install and configure the real build dependency and its prerequisites in the private build image before rebuilding; never bypass `dpkg-checkbuilddeps`.
  **Found by:** the dependency error from `dpkg-buildpackage` and the original dpkg installation log.
- **Symptom:** a green fresh-user test says nothing about a person's existing panel.
  **Cause:** the initial-layout script and saved-panel path are different paths.
  **Fix:** retain the predecessor's actual panel configuration and run the successor with that seed, expecting the old launcher to remain.
  **Found by:** the live D-Bus launcher list, checked separately for the fresh account and saved-choice account.
