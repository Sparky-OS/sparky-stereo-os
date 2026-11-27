# A Google account's program, proved without a Google account

The rig of queue row 299 (DriveSync): a real Plasma login in a container with no network, Google's four host names pointing at a local stand-in, a test certificate authority the system store trusts, a stand-in NetworkManager for the metered state, the Secret Service owner a case asks for, and AT-SPI and KWin's fake input to drive the program's window.
Nothing real is contacted: no Google account, no client of anybody's, no token that can open anything.

| File | What it is |
| --- | --- |
| `mkrig.sh TAG` | Debian testing by digest with the published round as a `file:` source and the edition's pins: Plasma, KDE Wallet with pam_kwallet, GNOME Keyring, the portals, Dolphin, KAccounts and KIO GDrive. The edition's local host names map to nothing. |
| `mkrig2.sh BASE TAG` | AT-SPI, a test CA trusted by `update-ca-certificates`, the stand-in's certificate for `www.googleapis.com`, `oauth2.googleapis.com`, `openidconnect.googleapis.com` and `accounts.google.com`, `rig-browser` as the default `https` handler, the fake-input client. Then install the package under test with `apt-get install ./PKG.deb` in a further layer. |
| `run-case.sh IMAGE OUT VAR=VALUE...` | One fresh container per case (`PREFIX` names it): `--network none`, the four `--add-host` lines, `--sysctl net.ipv4.ip_unprivileged_port_start=0` (the stand-in listens on 443 as the person), KWin on the NVIDIA card through CDI, `--ulimit core=1`. |
| `session.sh` | Inside: the stand-in, the stand-in NetworkManager on a private system bus, `startplasma-wayland` on a virtual output, the Secret Service owner (`SECRETS=kwallet`, `gnome` or `blocked`), a `dbus-monitor` of `Notify`, then the scenario. |
| `fakegoogle.py` | The stand-in: OAuth with PKCE (consent granted at once, a 302 to the program's loopback address), an RS256 ID token checked against its own JWKS, userinfo, Drive v3 files, changes and generateIds, resumable uploads (308 with `Range`), Drive v2 reads and conditional writes with strong ETags. Admin port 8099: `/log`, `/tree`, `/issued` (token hashes only), `/ttl`, `/put`, `/mkdir`, `/fail-upload` (the next upload of that name gets Drive's 403 `storageQuotaExceeded`). |
| `fake-nm.py STATE_FILE` | `org.freedesktop.NetworkManager` with `Connectivity` and `Metered`, the two properties GLib's network monitor reads; writing `metered` or `unmetered` to the file publishes the change. |
| `kwallet-login.py` | Unlocks or creates KDE Wallet as pam_kwallet does at a display manager's login: `ksecretd --pam-login PIPE SOCKET` with `PAM_KWALLET5_LOGIN` set, the 56-byte key on the pipe, the environment on the socket. |
| `atspi.py` | Read and press a GTK or Qt program's widgets by role and name; `focus`, `text`. |
| `secret-items.py APP` | The program's items read back through the Secret Service: owner and executable, label, attributes, and of the secret only the field names and a hash of the token. |
| `notifications.py LOG` | The `Notify` calls a session received: application, summary, body, actions, desktop entry, urgency. |
| `scenario-full.sh` | Sign-in through the window, the credential read back, the folder configuration written as the program's save writes it, first sync, conflict, quota refusal, token refresh, metered hold and resume, tray round trip, Places. `PHASES` chooses. |
| `scenario-red.sh` | The same session for a build without the integration. |
| `scenario-locale.sh` | With `METERED_AT_START=metered` and `LOGIN_LANG`: the integration's strings (notice, tray tooltip and menu, banner) in a language, with no sign-in. |
| `collect.sh CASE OUT [SHOT...]` | A case's small evidence: marks, parsed notifications, secrets, tray dumps, token hashes, request list, chosen captures. |
| `vault-test.sh OWNER` | The program's own ignored vault test on a private bus answered by KDE Wallet or GNOME Keyring. |
| `apt-plan.sh DEBS OUT` | apt's plan for the package on a bare Debian testing with the published round, read from `Inst` and `Remv` lines. |

What this leaves unproved is in the reference [a GTK and Rust program at home in KDE](../../../edition-packaging/references/a-gtk-rust-program-at-home-in-kde.md#what-the-proof-leaves-unproved).
