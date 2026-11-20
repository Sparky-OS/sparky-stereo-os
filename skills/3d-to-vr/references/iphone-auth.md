# iPhone authentication and one shared pairing

**For the person reviewing the phone session: what the signer sends and saves, the local anisette boundary, and why KDE Connect can own one pairing for both apps.**
Check freshness first: source audit on 2026-11-20, xtool **1.24.0**, commit **70e1568fdfcb20b560774057cd783f02361293b9**.
No account was used and no authentication traffic was observed.
File and line references below describe that unmodified release; the shared-pairing changes are listed separately.

## Before any account is entered

The reviewed release defaults to **`https://mac-ani.jkcoxson.com`**, a third-party service, not Apple.
The xtool maintainer identifies it as jkcoxson's server in [issue 401](https://github.com/xtool-org/xtool/issues/401); this does not establish its retention policy or physical operator location.
The default is hardcoded at [OmnisetteADIProvider.swift:9–13](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/GrandSlam/Anisette/OmnisetteADIProvider.swift#L9).
The constructor accepts another URL internally, but this release exposes no command-line or environment override for it.

| Exchange | What leaves the machine | What returns | Source |
| --- | --- | --- | --- |
| GET `/v3/client_info` | An HTTP request; no account fields | `client_info` and `user_agent` strings used with Apple | [OmnisetteADIProvider.swift:30–43](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/GrandSlam/Anisette/OmnisetteADIProvider.swift#L30) |
| WebSocket `/v3/provisioning_session` | Base64 `identifier` (16-byte persistent random UUID), Apple's opaque `spim`, then `ptm` and `tk` | `cpim`, then `adi_pb`, plus protocol prompts | [OmnisetteADIProvider.swift:45–54, 110–153](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/GrandSlam/Anisette/OmnisetteADIProvider.swift#L110) |
| POST `/v3/get_headers` | Base64 `identifier` and saved `adi_pb` | Machine ID `X-Apple-I-MD-M`, one-time value `X-Apple-I-MD`, routing `X-Apple-I-MD-RINFO` | [OmnisetteADIProvider.swift:57–92](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/GrandSlam/Anisette/OmnisetteADIProvider.swift#L57) |

The service sees the connection's source IP and timing, and can correlate the persistent identifier and provisioning blob.
Calling this only a randomized token omits material information: the service participates in creating the device authentication state and receives it again when headers are requested.
The blobs are opaque to this audit; they are not the Apple account password or the account login token.
Apple's start/finish provisioning exchange is separate, via the endpoints returned by Apple's lookup: [ADIDataProvider.swift:156–214](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/GrandSlam/Anisette/ADIDataProvider.swift#L156).

The account name and SRP public value/proof go to Apple's GrandSlam service, not to the anisette request structures: [GrandSlamAuthenticateOperation.swift:67–103](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/GrandSlam/Operations/GrandSlamAuthenticateOperation.swift#L67).
The password is processed locally into the SRP proof, rather than sent verbatim: [SRPClient.swift:97–145](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/GrandSlam/Crypto/SRPClient.swift#L97).
Trusted-device verification codes go in Apple's `security-code` header; SMS codes go to `gsa.apple.com/auth/verify/phone/securitycode`: [GrandSlamValidateRequest.swift:12–55](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/GrandSlam/Requests/Concrete/GrandSlamValidateRequest.swift#L12).
The lookup starts at `https://gsa.apple.com/grandslam/GsService2/lookup`; subsequent URLs are trusted from that response, not checked against an independent hostname allowlist: [GrandSlamLookupManager.swift:15–61](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/GrandSlam/Lookup/GrandSlamLookupManager.swift#L15).
Thus the normal source path sends account authentication only to Apple; this is not a packet-capture proof or a guarantee against a modified executable, proxy or disabled TLS verification.
On Linux, `XTL_HTTP_PROXY` selects a proxy and `XTL_DISABLE_TLS_VALIDATION=1` disables certificate verification: [AsyncHTTPClient+HTTP.swift:25–60](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/HTTPClientProtocol/AsyncHTTPClient%2BHTTP.swift#L25).
Keep both unset for the session, and do not enable debug logging around authentication.

## What remains on disk

The default store is **`~/.config/xtool/data/`**, based on `NSHomeDirectory()`, not `XDG_CONFIG_HOME`: [DirectoryProvider.swift:4–10](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/Utilities/DirectoryProvider.swift#L4).
It is a plain directory store, not the Linux desktop keyring, and does not explicitly enforce private modes: [KeyValueStorage.swift:26–28, 101–126](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/Utilities/KeyValueStorage.swift#L101).

| Filename under that directory | Contents |
| --- | --- |
| `XTLLocalUserUID` | Persistent random UUID used with the anisette service |
| `XTLADIProviderID` | Provider association, `mac-omnisette` in stock 1.24.0 |
| `XTLProvisioningInfo` | Opaque `adi_pb` |
| `XTLRoutingInfo` | Routing integer as text |
| `XTLAuthToken` | JSON: account name, ADSID, login token, expiry, team ID and anisette-provider ID; no password or verification code |
| The team ID (password login) | Property-list encoded signing private key and certificate, saved when a signing certificate is obtained |

Anisette keys and writes: [ADIDataProvider.swift:91–115, 250–274](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/GrandSlam/Anisette/ADIDataProvider.swift#L91).
Account fields and JSON save: [AuthToken.swift:5–13, 58–82](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XToolSupport/AuthToken.swift#L5).
Signing fields and store: [SigningInfo.swift:11–16, 72–86](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/Utilities/SigningInfo.swift#L11); the password-login storage key is the team ID at [DeveloperServices+OpenAPI.swift:84–91](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/DeveloperServices/OpenAPI/DeveloperServices%2BOpenAPI.swift#L84).
Logging out removes the login-token entry, not the entire provisioning/signing store.
Use a private terminal with `umask 077` and private directory permissions; exclude this directory, the session manifest, device identifiers and signed outputs from source repositories and logs.
The login success message itself prints the account and team IDs.

## Local anisette: possible software, unavailable under the current file limit

[anisette-server-rs](https://github.com/fdkevin0/anisette-server-rs/tree/811b9d88aa88af9cba67be3890ef78db5b63c011) runs on Linux and is **GPL-2.0-only** ([Cargo.toml:10](https://github.com/fdkevin0/anisette-server-rs/blob/811b9d88aa88af9cba67be3890ef78db5b63c011/Cargo.toml#L10)).
It runs Apple's ADI implementation in Unicorn, not a replacement written entirely as free software.
Its [asset instructions](https://github.com/fdkevin0/anisette-server-rs/blob/811b9d88aa88af9cba67be3890ef78db5b63c011/assets/README.md#L5) require proprietary Apple binary assets; its container images already contain those assets.
Its [compatibility table](https://github.com/fdkevin0/anisette-server-rs/blob/811b9d88aa88af9cba67be3890ef78db5b63c011/docs/compatibility.md#L3) identifies Android, macOS and Windows ADI backends, with different authentication compatibility.
The macOS V3 backend also needs Apple's routing value in the finish message, which stock xtool drops.
SideStore's older omnisette-server and Dadoum's anisette-v3-server likewise require Apple libraries; neither inspected tree supplied an explicit project licence suitable for this recipe.

**The no-Apple-files condition prevents a real local anisette service from being started here.**
No Apple runtime, preloaded container, account or provisioning state was downloaded or used.
A metadata stand-in is only a client-routing test, not a working anisette service.
The session must remain before sign-in until the local-runtime boundary is resolved and the actual service is checked.
Do not quietly revert to the public default.

The patched xtool compiles and links on Linux with Swift 6.4.1 using `--build-system native`; the new default build engine crashed during planning.
The local policy tests compile and run without an SDK or account.
The compiled client also passed the loopback metadata fixture test; that proves endpoint selection and the HTTP request path only.
The xtool change adds `XTL_ANISETTE_URL`, displays the selected endpoint before the account prompt, namespaces saved provisioning by that endpoint, and forwards `X-Apple-I-MD-RINFO` during V3 provisioning.
Once an actual local service is available, its base URL is configured as:

```sh
export XTL_ANISETTE_URL=http://127.0.0.1:6969
xtool sparky-policy --probe
```

Expected first line: `sparky-shared-pairing-1`; expected endpoint: `http://127.0.0.1:6969`.
`Anisette metadata answered (not a provisioning or authentication proof)` proves only the metadata request.
A real `/v3/get_headers` result after account-free device provisioning is the remaining service proof; it must come from the real implementation, not a fixture.
Local service ownership removes the third party from the anisette exchange, but Apple still receives provisioning and authentication requests.

## One pairing under a free account

Apple's [iOS capability table](https://developer.apple.com/help/account/reference/supported-capabilities-ios), read 2026-11-20, marks **Keychain sharing and App groups** available in all three columns, including the no-cost Apple Developer column.
Its qualification is: “The capabilities available to an iOS provisioning profile depend on your program membership.”
Read the HTML check icons; a text-only table can lose all the yes marks.
Apple's [keychain sharing documentation](https://developer.apple.com/documentation/security/sharing-access-to-keychain-items-among-a-collection-of-apps) explicitly permits this: “you can add another app signed by the same Apple Developer team to the app’s default keychain access group”.
An App Group additionally offers a shared container and some inter-app messaging; it is unnecessary for these existing keychain records.
A custom URL remains a navigation mechanism and never carries pairing keys or grants.

Apple DTS confirms: “Personal Team is the term that Xcode uses for Apple’s free provisioning feature.”
The [DTS profile dump](https://developer.apple.com/forums/thread/821896) shows a free profile allowing its own prefix wildcard for keychain groups; the missing `com.apple.token` group discussed there concerns external token keys, not our own group.
This supports one pairing, subject to checking the actual returned profile; it is not a guarantee that a particular account will receive every requested entitlement.

KDE Connect holds the canonical identity and paired-PC certificate records.
The receiver's signer keeps its own default group first and adds KDE Connect's default group only if Apple's returned profile permits both.
The receiver reads KDE Connect's identity and paired certificate before any network connection, again after TLS, throughout the control loop, and before starting an RDP grant.
Absent or changed trust stops reception with a localized instruction to use KDE Connect; there is no second pairing or trust copy.
The receiver has read-only behavior by implementation; keychain group membership itself is not an OS-enforced read-only permission.
Cardboard receives no pairing-group entitlement.

Stock xtool replaces keychain groups with only the app's own group at [EntitlementWithTeamOrBundleID.swift:27–44](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/DeveloperServices/App%20IDs/Entitlements/EntitlementWithTeamOrBundleID.swift#L27).
The change therefore applies after provisioning, checks the profile's own prefix and allowed groups, and refuses missing permission before signing.
The renewal helper checks `xtool sparky-policy` before its first installation; stock xtool is refused.
xtool maps installed IDs to `XTL-TEAM.original.bundle.id` for password login with that team ([ProvisioningIdentifiers.swift:24–26](https://github.com/xtool-org/xtool/blob/70e1568fdfcb20b560774057cd783f02361293b9/Sources/XKit/Utilities/ProvisioningIdentifiers.swift#L24)).
Use the same tool, account and team for all three apps and renewals.
No real profile or phone was used to validate the cross-app entitlement; the later session must observe it before Catch.
