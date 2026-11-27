# A GTK and Rust program at home in KDE (DriveSync, queue row 299)

A GTK 4 and libadwaita program written for GNOME, packaged from source and given what a KDE program has: a system tray entry, its credentials in the desktop's Secret Service, Plasma notifications, a place in Dolphin, and respect for a metered connection.
The example is Rafael Tosta's DriveSync (Google Drive synchronization, Rust, GPL-3.0-only), built from one commit of its main branch on 2026-11-27, with every change written as a patch its author could take.

## Working recipe

1. **Reconcile first.** Read the program's newest commit, its releases and tags (DriveSync had none: the source is a commit, pinned by archive SHA-256, the commit in the archive's pax header and the git tree id), its `Cargo.lock`, how it authenticates, where it keeps secrets, and every path it hard-codes for the Flatpak (`/app/share/...`).
   Check Debian for the program and its crates (`apt-cache policy librust-NAME-dev`): when the lock's versions differ from Debian's, vendor the crates as [LACT's recipe](lights-and-peripherals.md) does.
2. **Read the project's agent and contribution rules whole** (every `AGENTS.md`, not only the root one, the pull request template, `CONTRIBUTING`, the README): DriveSync's say how its author wants changes shaped (commit titles `type(scope): description`, a body with motivation, changes, validation and limitations; no permanent deletion; no unrequested fallbacks or dependencies; never a push or a pull request without authorization).
3. **Make the series on a fork branch, one commit per change, each compiling** (rustfmt and `clippy -D warnings` at every commit), then export it with `git format-patch` into `debian/patches` with DEP-3 `Origin: vendor` and `Forwarded: no`. Never edit the exported patches: regenerate them.
4. **Vendor from the patched lock.** A patch that changes `Cargo.toml` features changes `Cargo.lock`; `make-orig.sh` applies `debian/patches` to a copy of the tree before `cargo vendor --locked`, so the vendor component matches what the package builds.
5. **Build through the Lean Code toolkit** (`release/build-dh-lean.sh`), as LACT's `build.sh` does, with the program's production identity (`DRIVESYNC_APP_ID`), the distribution's data directory and the source revision set in `debian/rules`.
6. **Prove it in a Plasma login without the service's real account** ([the proof](#the-proof-without-a-real-account)), red against the upstream build and against the series cut before each feature.

## The integration, part by part

| Part | What a GNOME program does | What the patch does | Why there |
| --- | --- | --- | --- |
| Data directory | reads `/app/share/...` (Flatpak) | a build-time `DATADIR` (`option_env!`), `/app/share` by default | the OAuth client file and the catalogues must be found under `/usr/share`; the Flatpak build stays as it is |
| TLS roots | reqwest `rustls-tls` (webpki-roots compiled in) | `rustls-tls-native-roots` | one copy of the trust store, the system's; also what lets a rig's test authority stand in for the service |
| Tray | none (GNOME has no tray); the Background portal hides the window | a StatusNotifierItem and a `com.canonical.dbusmenu` menu exported with GIO's own D-Bus API (no new crate), registered with `org.kde.StatusNotifierWatcher` when one is there | KDE's tray protocol; a closed window stays reachable |
| Secrets | the Secret Service (secret-service crate) | nothing to change | the interface is the desktop's; which daemon answers is the session's |
| Notifications | `GNotification` only for "continues running" | transitions of the public status: done (a run with changes), failed (not retryable), conflict, needs a decision; one per account and kind, replaced | Plasma shows GLib's freedesktop notifications with the app's desktop entry |
| Dolphin | opens the folder with `GtkFileLauncher` | "Add local folder to Places": one XBEL bookmark appended to `$XDG_DATA_HOME/user-places.xbel`, only when the file exists and only on the person's request | KDE's Places are that file; overlay icons would need a per-file state interface and a `KOverlayIconPlugin` |
| Metered | nothing | while GLib's network monitor says metered, saved scopes are not started or are stopped, said once (notification, banner, tray), restarted afterwards; a setting allows metered connections | the person's data plan; the edition's rule for downloads |
| Languages | pt_BR only | catalogues for the ten languages, the desktop entry's keys in each | every string the edition adds |

## The proof without a real account

The rig is [`stereo-proof-rig/scripts/google-standin`](../../stereo-proof-rig/scripts/google-standin/README.md): a real Plasma login (KWin on a virtual output, plasmashell, kded's StatusNotifierWatcher, Plasma's notification server) in a container with no network.
The service is a local stand-in written from the program's own provider code and the service's public references: the program cannot tell it from the real host because the four host names resolve to it and the system store trusts the rig's test authority, which is why the system-store patch comes before the proof.

1. Build the images (`mkrig.sh`, `mkrig2.sh`), then a layer that installs the package with `apt-get install ./PKG.deb` and keeps apt's plan.
2. Sign in through the window: AT-SPI presses the buttons by name; the stand-in browser (`rig-browser`, the default `https` handler) follows the consent redirect to the program's loopback address, as a person's browser does after "Allow".
3. Read the credential back through the Secret Service interface (`secret-items.py`): the executable of the process that holds the bus name, the item's attributes, and a hash of the token compared with the stand-in's `/issued`.
4. Write the folder configuration as the program's own save writes it (the save validates, writes one INI file, then applies it), and start the program again.
5. Each feature has its trigger and its reading: a remote and a local file (download, upload), the same file changed on both sides (conflict), `/fail-upload` (Drive's 403 `storageQuotaExceeded`), a short `/ttl` (refresh, and the stored token replaced), the stand-in NetworkManager's `Metered` (hold and resume), the tray's own dbusmenu `Event` (open, close to the tray, open again), the account menu (Places, then Dolphin).
6. Red: the same cases on upstream's build and on the series cut before each feature; a feature's row must change between them.

Measured on 2026-11-27 (DriveSync 082e743 with the series, Plasma 6.7.4 of round r1123a, KDE Wallet 6.32 answering): sign-in 3.5 s after start; the item in `kdewallet` with the attributes `application` and `account-credential` and the issued token's hash; first sync 2 s (one download, one upload); one notification each for done, conflict and failure, with the program's desktop entry; after the 75 s token lifetime a `refresh_token` grant and the stored token replaced under a new key; 50 s metered with no Drive request, the upload 2 s after the connection is no longer metered; the tray round trip; the Places entry in Dolphin with Google Drive's icon.

### What the proof leaves unproved

- No real Google account or OAuth client was used, so Google's own consent screen, its verification warnings, real quotas, rate limits, shared drives, Google Docs files and Google's real error bodies are not proved.
- The stand-in implements the calls DriveSync made in these cases; other Drive calls (revisions, permissions, comments, shortcuts) are not exercised.
- The folder pages of the setup were not driven (GTK's folder dialog): the configuration was written as the save writes it.
- KDE Wallet was unlocked the way pam_kwallet does it, not through a display manager's real PAM login; no logout and login cycle, no real NetworkManager, no real network.

## Traps

- **Symptom:** the account is saved but its state is `Unavailable`, with a pending intent, and nothing is in the wallet. **Cause:** KDE Wallet's `ksecretd` was activated without a key (the wallet needs its first-use wizard), or GNOME Keyring was activated from its own activation file with no unlocked collection (default alias `/`). **Fix:** in the rig, unlock the wallet as pam_kwallet does (`kwallet-login.py`); on a system, a login with pam_kwallet or pam_gnome_keyring. **Found by:** `ReadAlias("default")` returning `/` and `ksecretd: Unknown option 'pam-login'` in its log.
- **Symptom:** `ksecretd: Unknown option 'pam-login'`. **Cause:** ksecretd reads `--pam-login` only when `PAM_KWALLET5_LOGIN` is in its environment (`src/runtime/ksecretd/main.cpp`, KWallet 6.32). **Fix:** set it to the socket's path. **Found by:** reading main.cpp after the option was refused.
- **Symptom:** `GLib-GIO-WARNING: Type of return value is incorrect: expected '(u(ia{sv}av))', got '(uv)'` and an empty tray menu. **Cause:** a GLib `Variant` placed in a Rust tuple is boxed as `v`; the dbusmenu layout must be a structure, and the children of an `av` must not be boxed a second time. **Fix:** `Variant::tuple_from_iter` for the reply, the entries themselves in the `Vec<Variant>`, and a unit test on the reply's type string. **Found by:** the program's own warning in the session log, then the test.
- **Symptom:** AT-SPI finds no window of the program. **Cause:** the accessible application's name is the executable's name; a binary copied as `tip` is not `drivesync`. **Fix:** keep the name. **Found by:** the tree listing an application called `tip`.
- **Symptom:** a GTK check button cannot be pressed through AT-SPI (no action), and popover menu items have no names. **Fix:** the check button has the window's first focus, so Space through KWin's fake input selects it; menu items are pressed by their order, after counting them (a build with fewer items must not press the wrong one). **Found by:** `atspi.py tree`.
- **Symptom:** one failing upload gives several "failed" notifications within seconds, and a conflict is preceded by a "failed" one. **Cause:** the engine retries a blocked item, and the status passes through other phases on each retry. **Fix:** tell an event only once its phase has lasted two seconds, and a failure, conflict or decision once until the account is idle again. **Found by:** the `Notify` log (`notifications.py`) of the first full run.
- **Symptom:** three engine tests fail in a container on ext4 and on upstream's own commit alike. **Cause:** they expect a file's identity to stay the same between scans of a Btrfs tree. **Fix:** skip them by name in `debian/rules` and say why; every other test runs.
- **Symptom:** a Drive quota refusal reaches the person as "an operation needs verification". **Cause:** the engine treats a Google error it does not list, during a mutation, as an uncertain effect. **Fix:** none in this series (the engine's safety model is the author's); reported as a finding.
- **Symptom:** the keyring the case asks for (GNOME Keyring, or none at all) never owns `org.freedesktop.secrets`; KDE Wallet's `ksecretd` does, with no wallet open, and sign-in ends with "Secure credential storage is unavailable. Unlock your keyring and try again.". **Cause:** the Plasma session starts `ksecretd` through its compatibility names before a keyring started afterwards can take the standard name. **Fix:** start the login's keyring before `startplasma-wayland`, as PAM does at a display manager's login. **Found by:** the line `session.sh` prints for the process that holds the bus name, its executable read from `/proc`.
- **Symptom:** a case runs its whole login a second time and its log mixes two sessions. **Cause:** the case's `session.sh` was edited while a container's shell was still reading it (the proof rig's rule: never edit a script while it runs). **Fix:** write a new file and swap it in between cases.
- **Perk:** the Background portal's login autostart works for the packaged program on Plasma: KDE's portal writes `~/.config/autostart/com.rtosta.DriveSync.desktop` (`Exec=drivesync --background`, `X-XDP-Autostart`), so the next login starts DriveSync in the tray. **Found by:** a second login in the same home, which autostarted the installed package.
- **Symptom:** the Docker daemon refuses a bind mount of `/var/tmp/sparky-repo-current`. **Cause:** it is a symbolic link to the round's tree. **Fix:** mount the link's target.
