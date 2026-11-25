# Online Accounts and secrets

A KCM provider definition makes an account selectable.
A service definition and a consumer make the account useful to a program.
Check the installed packages, account backend and program separately.

## Inventory the installed routes

1. Read the image’s inherited package list, removal lists, desktop metapackage and ISO install flags together.
   The edition archive contains its own overlay and rebuilt packages.
   Debian can supply KAccounts, SignOn and KDE PIM even when the edition’s package index has no stanza for them.
2. In a disposable installed session, save package versions and sort the files under `/usr/share/accounts/providers/kde`, `/usr/share/accounts/services/kde` and `/usr/share/akonadi/agents`.
   Compare them with the release’s install rules and default-branch source.
   Inspect XML setting names and scopes without dumping client credentials.
3. Trace the settings reader from the service definition to the worker or resource.
   Use [KAccounts Integration’s models and jobs](https://github.com/KDE/kaccounts-integration) for older Plasma accounts.
   A consumer selects an eligible enabled service, resolves the account’s credentials identity with GetCredentialsJob and handles the job’s errors.
   The KDED consumer plug-ins receive account create/remove and service enable/disable callbacks.
4. Check [KOnlineAccounts](https://github.com/KDE/konlineaccounts) separately.
   Its account objects expose capabilities through distinct D-Bus interfaces.
   KDE PIM 26.08.2 already has readers for its Google, CalDAV and CardDAV interfaces.
   The service’s README describes its prototype status and application-identity and revocation limitations.
   Keep legacy KAccounts consumers in the test matrix when evaluating the newer service. [DAV integration](https://invent.kde.org/pim/kdepim-runtime/-/merge_requests/284), [Google integration](https://invent.kde.org/pim/kdepim-runtime/-/merge_requests/285).

| Route | Service and consumer | Credential path to prove |
| --- | --- | --- |
| Google with KAccounts | Google provider; Calendar and Contacts XML disabled in the provider bundle. KIO GDrive adds `google-drive` and Purpose can add `google-youtube`. | OAuth via SignOn. Measure which extension holds credentials and refresh data. Inspect consent scopes for each enabled service. |
| Nextcloud with KAccounts | Storage and Contacts service definitions, with a Purpose upload service. KAccounts Integration’s WebDAV plug-in creates the storage link for Dolphin. | Server-issued app password via SignOn. The WebDAV plug-in copies it to native KWallet `Passwords` under a scheme, account, host and realm key. Inspect the generated remote link for absence of a password. |
| ownCloud with KAccounts | Storage through the same WebDAV plug-in. Old Calendar and Contacts definitions are disabled. | Compatible server credentials through SignOn and the native network wallet. |
| OpenDesktop with KAccounts | Rating and commenting through Plasma Desktop’s Attica add-on. | OAuth through SignOn. |
| Microsoft with KAccounts | The separately developed OneDrive KIO worker supplies Microsoft provider and OneDrive service definitions. | Microsoft OAuth through SignOn. Check the exact tenant, client, redirect and delegated scopes. [OneDrive worker](https://invent.kde.org/bernardogn/kio-onedrive). |
| Nextcloud with KOnlineAccounts | Nextcloud, CalDAV and CardDAV interfaces. KDE PIM and Purpose contain readers. | QKeychain service `konlineaccounts`, account-derived password key. |
| Mastodon with KOnlineAccounts | Mastodon interface for Tokodon. | Instance OAuth registration and consent. QKeychain service `konlineaccounts`, account-derived token and client-secret keys. |
| Google with KOnlineAccounts | Google interface for PIM and Purpose. | QKeychain service `konlineaccounts`, account-derived access and refresh token keys. |
| Direct IMAP, POP3 and SMTP | The KDE PIM wizard creates incoming resources, an identity and an outgoing transport. | QtKeychain services `imap`, `pop3` and the mail transport store. Check the SMTP config-file branch on wallet failure. |
| Direct DAV, Google Groupware, EWS, EteSync | Akonadi collections, with EWS transport and EteSync dependent on package build options. | QtKeychain services `Passwords`, `Akonadi Google`, `akonadi-ews`, `Akonadi Etebase`. Open-Xchange instead declares a KConfigXT password. |
| Microsoft Graph PIM | Microsoft 365 groupware and transport developed after 26.08.2. | OAuth with PKCE, QtKeychain `akonadi_graph_resource`. Check whether the packaged release contains the resource. |

## Check who owns the secret service

Inside the disposable desktop session, query the session bus before and after the first credential request.

```sh
gdbus call --session --dest org.freedesktop.DBus \
    --object-path /org/freedesktop/DBus \
    --method org.freedesktop.DBus.GetNameOwner org.freedesktop.secrets
busctl --user --no-pager status org.freedesktop.secrets
```

The first call gives the owning unique name, and the second identifies its process and executable.
Repeat on a deliberately absent name first to verify that the probe can detect absence.
On a fresh private bus, `StartServiceByName` for `org.freedesktop.secrets` tests explicit activation separately from the normal startup order.
Inspect the packaged D-Bus service files, session autostart entries and login hooks for each competing daemon.
On the r1123a package subset, the classic Plasma test saw the name unowned at first and GNOME Keyring after explicit activation.
The generic no-systemd session tests activation and the classic Plasma launch path.
Run a display-manager login case to cover its PAM and systemd user-service order.

For KAccounts, compare the libaccounts metadata database `$XDG_CONFIG_HOME/libaccounts-glib/accounts.db` with SignOn’s stock databases under its configured storage path.
The KDE SignOn extension writes into KWallet’s native `accounts` folder under the numeric identity ID and per-method keys.
QtKeychain and native KWallet also have different backend choices.
A loaded plugin, an owned bus name and a correctly persisted test item require separate observations.
[Secret Service specification](https://specifications.freedesktop.org/secret-service/latest/), [KDE SignOn Wallet extension](https://github.com/KDE/signon-kwallet-extension).

## Local-server rig for a continuation

Prepare package dependencies first, then use one fresh, disposable Plasma session on a private internal network.
Use mail submission and retrieval, a CalDAV and CardDAV collection, and a WebDAV or Nextcloud fixture on that network.
Give each protocol a distinct fixture item and use a synthetic account with a unique secret marker.
Use test trust roots if the client requires TLS.
The rig should fail when a container can reach outside the test network.

Add the account through the KCM once.
Test inbox and SMTP delivery separately, then verify the expected calendar event, contact and file are visible through their usual applications.
Check account/service ID, wallet item label, unlock failure, repeated start, removal and two accounts on one server.
The red control writes the synthetic marker to a disposable file.
The actual check examines only the isolated fixture stores and records paths, match counts and item names.
Avoid printing secret values or reading an existing profile.
A successful server login from a test utility alone does not prove account reuse by the application.

## Traps

- **Symptom:** an online account appears but an Akonadi collection never does.
  **Cause:** provider and service metadata exist independently of resource creation and of the backend the resource reads.
  **Fix:** trace account ID delivery into the resource and test its first successful sync.
  **Found by:** comparing the actual installed definitions with the resource D-Bus calls and disabled XML install rules.
- **Symptom:** KWallet is installed, yet Secret Service may activate another daemon.
  **Cause:** distro packages can ship GNOME Keyring’s standard activation descriptor while KWallet also supports the standard name.
  **Fix:** measure the bus owner and executable before choosing the default; preserve separately selectable user backends.
  **Found by:** listing package-owned D-Bus activation files and reading KWallet’s name-registration code.
- **Symptom:** an account test reports that everything is in the wallet while an SMTP password can still survive in a file.
  **Cause:** MailTransport supports explicitly accepted or previously active obfuscated configuration storage when the keychain fails.
  **Fix:** include wallet-unavailable and existing-account migration cases.
  **Found by:** following `Transport::usrSave()` and its read-side migration from the `mailtransports` configuration.
- **Symptom:** Plasma session startup invokes KWin repeatedly and gets “Operation not permitted.”
  **Cause:** a capability-bearing KWin binary cannot exec with a container bounding set that excludes that capability.
  **Fix:** use the proof rig’s explicit container settings for a desktop case. An ordinary executable copy inside the disposable container can isolate the capability issue during diagnosis.
  **Found by:** comparing `getcap` on the packaged binary and the diagnostic copy.
- **Symptom:** the diagnostic binary starts but KWin aborts at its internal Qt platform plug-in in the headless container.
  **Cause:** the virtual KWin launch attempted the built-in platform integration in a container with no render nodes.
  **Fix:** for a D-Bus and MIME probe, add `-platform offscreen` in the virtual KWin shim and require the real `org.kde.plasmashell` service before measuring.
  **Found by:** a direct virtual launch with the platform argument accepted clients, then a fresh classic Plasma login passed the bus and MIME checks.
