# Xcode signing and a USB install from an SSH session

**Build and sign with Xcode on the Mac; keep the Apple account and signing key there.**
Check freshness first: read 2026-11-21 against Apple's documentation and the Intel Xcode 26.3 build.
The helper's complete unsigned path passed on Intel in [run 44854555442](https://github.com/Sparky-OS/flat-headset/actions/runs/44854555442), read 2026-11-21; account use, USB installation and keychain sharing still need the person and the real phone.

## The two Mac routes

| Route | What the person does | What can fail | What remains reproducible | Run over SSH from the Linux station |
| --- | --- | --- | --- | --- |
| A: build pinned sources with Xcode automatic signing | Install Xcode and build tools once, add the account in Xcode, select its Personal Team ID, trust the USB phone, then run the first-session or renewal command | Missing component/tool, source download, account session, certificate/private-key access, provisioning, USB trust | Exact source commits and dependency archive hashes; Xcode version recorded; a local signed app is not byte-identical to the hosted unsigned IPA | `xcodebuild` builds and provisions headlessly after account/keychain preparation; the accepted scripted iOS 16 installer is `ios-deploy`; Xcode's window is the no-extra-installer choice; no window is opened by our helper |
| B: re-sign the hosted unsigned IPAs | Download/check each IPA, obtain a valid Personal Team profile for each identifier, inject matching entitlements and sign/install the app bundles | In addition to the same account/keychain/USB issues: profile acquisition, entitlement/prefix mismatch, stale embedded profile, manual re-signing | The downloaded original retains its hosted hash; re-signing changes the executable and package hash | `codesign` can run headlessly, but a free account still needs provisioning; the IPA alone does not supply it; an automatic-signing Xcode build or equivalent provisioning work remains necessary |

Recommend A because Xcode keeps the profile, capabilities and app signature together, and the pinned native build is already proven on Intel.
Route A is the accepted scripted route; the session page also offers Xcode's own installation window with the same signed builds and no ios-deploy.
Route B remains a comparison, not the active procedure.
Apple's [TN3125](https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles) says: “When signing code, use Xcode (all platforms) or the `codesign` tool (macOS only).”
This also makes hand-signing an iPhone IPA a less suitable documented route than Xcode's own signing.
Both shapes use the same free Personal Team, three app slots and seven-day profiles; neither changes Apple's limits.
The source build's three pins are in [sources.json](https://github.com/Sparky-OS/flat-headset/blob/order737/ios/Tools/Mac/sources.json).

## The iOS 16 command boundary

Apple DTS confirms: “The command supports iOS 17+ devices.” ([devicectl and iOS 16](https://developer.apple.com/forums/thread/772724), reply February 2025, read 2026-11-21).
A USB-connected iOS 16.7 phone is therefore not an installation target for `devicectl`, even though Xcode 26.3 can build and run on it.
For an iOS 17+ phone `xcrun devicectl device install app --device … …` is the headless command family, but that is not this session.
`xcrun xcresulttool` reads build/test result bundles without a window; it does not install an app.
[run 44854555442](https://github.com/Sparky-OS/flat-headset/actions/runs/44854555442) captured the selected Xcode's `xcodebuild`, `devicectl`, `xcdevice`, `xcresulttool`, `security` and `codesign` help/man output; all six documentation commands exited zero without a phone or account.
The captured `xcodebuild -help` describes provisioning updates and device registration; `xcdevice` documents listing and waiting for devices, while `xcresulttool` 24514 reads/exports result bundles.
The captured devicectl help specifies JSON-file output for automation; it does not establish iOS 16 support.

The scripted USB installer is [ios-deploy 1.12.2](https://github.com/ios-control/ios-deploy/tree/ed7de7792d28a5110242748649047a95c95ea917), GPL-3.0-or-later, compiled from a hash-pinned source archive on the Mac.
Its maintainers describe it as: “Designed to work on un-jailbroken devices running iOS versions prior to iOS17.” ([README](https://github.com/ios-control/ios-deploy/blob/master/README.md), read 2026-11-21).
Its upstream project temporarily copies MobileDevice.framework into its source tree; our helper instead compiles the same single Objective-C source directly and links the installed framework in place.
It calls Apple's installed MobileDevice framework; it is not a signer and has no Apple-account input.
The helper selects USB only, checks exactly one iPhone on iOS 16, checks Xcode's availability/trust report and Developer Mode, and installs without uninstalling or launching.
Its Developer Mode option is compiled only when `IOS_DEPLOY_FEATURE_DEVELOPER_MODE` is defined; the build enables that source flag explicitly.
Run 44854555442 completed that source compile, executed its `--version` check and found the compiled Developer Mode option before it built the three apps.
The success follows the mandatory command sequence in the pinned helper; the successful-run artifact does not contain the installer binary or its private compile log, so there is no separate downloaded-installer disassembly claim.
The 12 artifact files are three IPA/checksum pairs and six documentation texts; no Apple framework or SDK is copied into them.
USB behavior still awaits hardware.
Apple also offers [Configurator's cfgutil](https://support.apple.com/guide/deployment/dep6f70f6647/web) for command-line automation, but its current install-app behavior was not verified in this work and it is not silently substituted.

## Before entering an Apple account

| Exchange or local state | What is known from Apple; what remains unspecified |
| --- | --- |
| Sign-in in Xcode's Apple Accounts settings | The person enters credentials into Apple's own Xcode. Apple's [project guide](https://developer.apple.com/documentation/xcode/creating-an-xcode-project-for-an-app) says “choose Add an Account to enter your credentials in Apple Accounts settings.” Our scripts have no account, password or verification-code field. |
| Provisioning | `-allowProvisioningUpdates` allows Xcode to communicate with Apple's developer website, as described in [Apple's WWDC21 session](https://developer.apple.com/videos/play/wwdc2021/10204/). The app identifiers/capabilities, phone identifier for device registration and public certificate information participate in provisioning; Apple receives the network requests. There is no third-party anisette server. |
| Account privacy | Apple's [Developer Program privacy page](https://developer.apple.com/support/privacy/) says “We collect your personal data to create and maintain your developer account.” Its paid-program enrollment/identity-verification discussion is not a requirement to send an ID document for free Personal Team use. This is not a packet-capture audit or a complete published list of authentication fields/hosts. |
| Signing identity | Apple's [provisioning guide](https://developer.apple.com/library/archive/documentation/ToolsLanguages/Conceptual/YourFirstAppStoreSubmission/ProvisionYourDevicesforDevelopment/ProvisionYourDevicesforDevelopment.html) says “The private keys for your certificates are stored in your keychain, and the public keys are stored in the portal.” The certificate and private key stay together in the Mac user's login keychain. |
| Profiles and account state | [Xcode 16 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-16-release-notes) locate downloaded profiles at `~/Library/Developer/Xcode/UserData/Provisioning Profiles`. Xcode retains its account entry and authentication state; the cited public documentation does not specify every token's storage path or retention period. Do not claim that Xcode stores no authentication state or that a plaintext password file was verified absent. |
| Our work directory | Sources, dependency downloads, unsigned build logs, signed app bundles with embedded profiles and private USB-install logs remain in the chosen Mac directory. Profiles include device/team identifiers. It is private, not a repository or public artifact. Signed `xcodebuild` output is discarded by the helper, and no account fields are parsed. |
| Source downloads | GitHub and the dependency projects' own hosts receive download requests and the connection's IP address. They receive no Apple-account arguments from this helper. `ios-deploy` operates over the selected USB connection. |

All sources in this table were read 2026-11-21.
Apple's documentation does not provide a complete Xcode authentication wire-format audit; that limitation remains explicit before anyone signs in.

## Login keychain over SSH

Apple's [DTS explanation](https://developer.apple.com/forums/thread/712005), read 2026-11-21, says: “Logging in via SSH does not unlock the keychain.”
The same explanation reproduces `errSecInternalComponent` when `codesign` cannot present an unlock dialog in an SSH session.
`User interaction is not allowed` is a possible underlying Security error, not a promise of the exact text `xcodebuild` will show for every failure.
`-allowProvisioningUpdates` authorizes developer-website communication; it does not unlock a local keychain or grant private-key access.

There are two separate permissions: the keychain must be unlocked, and `codesign` must be allowed to use that signing key.
For the first signing attempt the person uses Xcode at the Mac, answers its keychain prompt themselves and selects **Always Allow** for `codesign` if they want later uses of that key without another ACL prompt.
This grants access to that tool and key; do not change the key to allow every application.
If a new signing key is made later, its approval may be needed again.

| Password-free script route | What the person does | What it proves and costs |
| --- | --- | --- |
| Stay logged in at the Mac | Log in at the Mac's screen, unlock the login keychain there if needed, approve `codesign` once, then leave that user session logged in while the SSH command runs as the same user | Usually no repeat password until logout, sleep/timeout locking or a new key. Confirm with the first SSH signing attempt; a GUI login alone is not proof that the SSH context can sign. |
| Explicit unlock in the person's own terminal | The person, not an automation script or partner, runs `security unlock-keychain` in their own interactive SSH terminal and types only into Apple's prompt, then runs the helper in that session | Apple documents this SSH case with no GUI login. Password is needed again whenever that keychain relocks. No `-p` argument, environment variable, file, pipe or transcript receives it. |
| Manual key-specific authorization when GUI access is unavailable | Apple documents a key import with an ACL and a key-partition-list update, but this adds key-export/import handling | Not used here: the Mac has a screen and Xcode creates its own identity. The documented import example puts a password on the command line, so it is not a recipe to copy under this session's rules. |

The captured `codesign(1)` says “a digital identity must be stored in a keychain that is on the calling user's keychain search list.”
The captured `security(1)` includes `unlock-keychain` and separate sleep/timeout locking controls.
These are installed-tool observations from run 44854555442, not an account/keychain experiment.

Apple's [security(1) source](https://github.com/apple-oss-distributions/Security/blob/main/SecurityTool/macOS/security.1) documents the unlock command and sleep/timeout settings; the helper changes none of those settings.
A password is not inherently required on every renewal if the right keychain remains unlocked and the key ACL already permits signing.
If it has locked, the smallest action is for the person to unlock it once at the Mac before that session; if that does not unlock the SSH context, use their own interactive `security unlock-keychain` session as above.
No helper tries an empty password, imports a private key, changes an ACL, creates a keychain or runs as root.

Apple demonstrates signing over SSH after logging out of the GUI, so GUI login is not an inherent requirement for `codesign` once the keychain is explicitly unlocked.
No Apple source found guarantees that the whole Xcode account/provisioning and USB installation chain works with nobody logged in on this exact macOS/Xcode/phone combination.
For the first session keep the person logged in, the Mac awake and the phone unlocked; observe one SSH install and then the later renewal before claiming unattended operation.

## Before the session: who does what

Read this table with the person before any account is entered.
Only the person supplies account credentials, verification codes and the Mac/keychain password, in Apple's own screens or their own interactive terminal.
The exact helper failures below come from `session.py` at 94067879; fixture coverage is not a real-phone result.

| Order | Person at the Mac or phone: screen and action | Partner over SSH | Failure and the displayed sentence |
| --- | --- | --- | --- |
| 1 | Setup Assistant: choose language/keyboard/network and local Mac user; stop at an earlier owner's Activation Lock or an unrelated Remote Management screen | Nothing before Remote Login is enabled | No script runs; keep the screen wording and ask the seller to resolve it |
| 2 | About This Mac and Software Update: reach Sequoia 15.6+ or Tahoe 26; install/open Xcode 26.3 and its iOS/Metal components; accept Apple's terms personally | After access exists, check host/tool/disk versions | `STOP: This macOS cannot run the verified Xcode 26.3; update to Sequoia 15.6 or Tahoe 26.` or `STOP: This Xcode is too new for the iOS 16 phone; select Xcode 26.3.` |
| 3 | System Settings → Sharing → Remote Login: allow the chosen Mac user; confirm the public key and host fingerprint; authorize the one-time server setup | Validate key-only login and effective sshd configuration; check a second connection | SSH errors are SSH's own messages, not helper output; do not close the working connection until the second succeeds |
| 4 | Xcode → Settings → Locations/Components: resolve missing tools shown by the preflight | Run `first-session.sh --check-host`; verify Xcode, Metal, PATH and disk | `STOP: Xcode is unavailable; install Xcode 26.3, open it once and select its Command Line Tools in Settings > Locations.` or `STOP: The Metal Toolchain is missing; in Xcode Settings > Components install Metal Toolchain, or run xcodebuild -downloadComponent MetalToolchain on this Mac, then retry.` |
| 5 | Read the account-disclosure table, then Xcode → Settings → Apple Accounts: add the account and complete verification; select Personal Team and Apple Development certificate | Receive only the non-secret Team ID; fetch/check reviewed sources, optionally rehearse unsigned | `STOP: The Personal Team ID is missing or invalid; copy its ten-character ID from Xcode, not an account name.`; source-download failures name the pinned repository |
| 6 | At the Mac, unlock the login keychain and approve the signing-key prompt for codesign; keep this user logged in/awake | Prepare the reviewed command; wait for the phone readiness check in the next row before starting it | For KDE Connect: `STOP: KDE Connect did not build. Check automatic signing in Xcode and let the person unlock/authorize the login keychain at the Mac; then retry. Signing output is not recorded.` The other two failures use their program names |
| 7 | Phone: unlock, connect USB, Trust This Computer; enable/confirm Developer Mode. Xcode → Devices and Simulators: wait until ready | Scripted route inspects exactly one USB iPhone; window route uses the identifier copied privately from Xcode | `STOP: USB discovery failed; connect and unlock the phone, accept Trust and retry.` or `STOP: The phone is unavailable or not trusted in Xcode; unlock it, accept Trust and finish preparation in Devices and Simulators.` Window route instead stops on Xcode's visible device error |
| 8 | Stay available for any Apple provisioning/key permission dialog | Build all three, check profile expiry, device/team and keychain groups before any install | `STOP: This profile does not permit the shared KDE Connect pairing groups; stop before installing and have the team capabilities reviewed.` Never authorize a second pairing |
| 9 | Scripted route: wait for three installation sentences. Window route: Installed Apps → + → Open for KDE Connect, Cardboard, Flat Headset, in order | Scripted route uses ios-deploy; window route packages verified signed IPAs without ios-deploy | `STOP: KDE Connect was not installed; inspect kdeconnect-install.log and check USB trust. Keep the apps installed and retry; do not uninstall them.` Corresponding names/logs for the other two; the Xcode-window route uses Xcode's own error dialog |
| 10 | Open KDE Connect and pair once; scan with Cardboard; open Flat Headset and Catch. Observe a changing desktop through the actual viewer | Read only the agreed observations; no account/phone operation is automated here | Localized app messages identify discovery, shared-trust, profile or hardware-decoding failure; generated pictures do not prove reception |
| 11 | A week later: same user/account/IDs, phone trust, and personal keychain unlock if needed | Run renewal or prepare replacement signed IPAs for the Xcode window | `STOP: The signing profile has expired; let Xcode renew it before installing.` After success, observe whether pairing survived; do not uninstall |

Additional tool, source, disk and malformed-response stops remain in the helper and name what to repair.
`--check-host` checks the Mac even with no phone; it is not proof that subsequent account/USB steps will succeed.
The window procedure has no scripted USB discovery/Developer Mode check, so the person must resolve those states in Xcode and on the phone before installation.
