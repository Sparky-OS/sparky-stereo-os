# One Mac session for the three iPhone programs

**Use Xcode on the Mac to build and sign KDE Connect, Cardboard and Flat Headset, then pair once through KDE Connect.**
Check freshness first: prepared 2026-11-21 for Intel macOS, Xcode 26.3 and an iPhone on iOS 16.7.
The three native builds are green on Intel in [run 44850264729](https://github.com/Sparky-OS/flat-headset/actions/runs/44850264729); the new session helper's hosted proof must also be green and reviewed before using its signing path.
Nothing here claims a phone run.
Before any Apple-account sign-in, including the Xcode download page, read [what goes to Apple and what stays on the Mac](iphone-mac-signing.md#before-entering-an-apple-account); the person types those credentials only into Apple's own page or application.
The former Linux sign-in route is retained only in the [anisette audit](iphone-auth.md); its third-party identity-service question is why this procedure uses the Mac.

## First start and the Mac's tools

1. Connect the Mac to power, open its lid and follow Setup Assistant for language, region, keyboard and network. Create the Mac's local user and password yourself. An Apple account for iCloud is not needed for our source build; any optional sign-in is your decision.
2. If the screen says **Activation Lock** and requests an earlier owner's account, or **Remote Management** names an organization you do not belong to, stop and have the seller resolve it. Do not enter your account to work around either condition. See the [first-start observations](#what-the-mac-in-hand-must-tell-us).
3. Open **Apple menu → About This Mac** and record the macOS version, then **System Settings → General → Software Update**. Xcode 26.3 needs Sequoia 15.6 or later in that release family, or Tahoe 26. Update if necessary, keeping power and network connected. The [Apple compatibility table](https://developer.apple.com/xcode/system-requirements) is the authority, read 2026-11-21.
4. Download **Xcode 26.3** from [Apple's additional downloads](https://developer.apple.com/download/all/), using your free Apple account on Apple's page. Expand the archive and move Xcode to Applications. Do not take the current App Store version without checking: Xcode 27's connected-device support starts at iOS 17, so it is unsuitable for this iOS 16 phone.
5. Open Xcode once, read and accept Apple's agreement yourself, and let it finish installing required components. In **Xcode → Settings → Components**, ensure iOS platform support and **Metal Toolchain** are installed. Simulator runtimes for other platforms are not required for this USB session.
6. In **Xcode → Settings → Locations**, choose Xcode 26.3 for Command Line Tools. In Terminal, `xcodebuild -version` must begin `Xcode 26.3`; `xcrun --sdk iphoneos metal --version` must print the Metal compiler version. If Metal is missing, use Components → Metal Toolchain → Get, or type `xcodebuild -downloadComponent MetalToolchain` on the Mac and repeat the check.
7. The source build also needs Python 3.12 or newer, CMake, Ninja and pkg-config; Xcode supplies the compiler and developer tools. A partner can prepare these on this Mac with the person's approval using [Homebrew's installation instructions](https://docs.brew.sh/Installation), then `brew install python cmake ninja pkgconf`. Homebrew now labels Intel as Tier 3, so a fresh installation on this Mac is not yet proven; if a dependency install fails, keep that error for the partner before the phone session. The scripts find tools through PATH; they assume neither `/opt/homebrew` nor `/usr/local` for dependencies. The first SSH session must have the same tools in its PATH.

Apple's [component instructions](https://developer.apple.com/documentation/xcode/downloading-and-installing-additional-xcode-components) say: “To build your Metal apps, download and install the optional Metal Toolchain for the platforms your app targets.” (read 2026-11-21).
That page's component command has no account option and specifies no separate account requirement; Xcode itself and the agreement must already be set up.
The successful Intel run found Metal 32023.864 installed before it reached the download branch, so it did not measure a Metal download or prove that branch on a fresh personal Mac.
Neither that log nor the cited Apple page states the component's download size; read the size Xcode displays before Get.
Do not confuse the Xcode archive size, expanded Xcode and separately installed components.
The hosted Intel log measured 4,515,932 KiB for Xcode 26.3's Contents directory, excluding external components and build space.
Apple's authenticated archive listing must supply the exact 26.3 download size at download time; the current App Store listing is not that archive.
Software Update shows the actual update size and progress for the arriving macOS; there is no fixed duration or disk figure for an unknown starting release.
Allow a separate preparation period for download, expansion, restarts and the first build; the scripts require 10 GiB free for their build work, in addition to the installed tools and OS update's own requirements.

## Turning on Remote Login

Apple describes Remote Login as access “using SSH (Secure Shell Protocol) or SFTP (SSH File Transfer Protocol).” ([Apple Support](https://support.apple.com/guide/mac-help/mchlp1066/mac), read 2026-11-21).

1. At the Mac, open **System Settings → General → Sharing**, then the information button beside **Remote Login**. Choose **Only these users**, add the same Mac user who will hold the Xcode account, and turn Remote Login on. Full disk access is not required for a work directory in that user's home.
2. The partner supplies only the Linux station user's public SSH key. At the Mac place that public line in that user's `~/.ssh/authorized_keys`, with permissions 700 on `.ssh` and 600 on `authorized_keys`. Keep the private key on the station. Compare the Mac host-key fingerprint through the person at the screen before accepting the first SSH connection.
3. Test public-key login while the person remains at the Mac. The partner then configures the Mac's SSH server to require `AuthenticationMethods publickey`, with `PubkeyAuthentication yes`, `PasswordAuthentication no` and `KbdInteractiveAuthentication no`. Preserve existing configuration and validate with `/usr/sbin/sshd -t` and the effective `/usr/sbin/sshd -T` output before ending the working connection. This is a one-time Mac administration step authorized at its screen, not part of either build script.
4. Check a second key-only connection before closing the first. Keep the actual key, login name, host and address in the station's private connection configuration; none belongs in this page. The Remote Login screen's command supplies the private destination.

The public-key and password settings come from [Apple's distributed sshd_config(5)](https://github.com/apple-oss-distributions/OpenSSH/blob/main/openssh/sshd_config.5), read 2026-11-21.
Remote Login's GUI alone does not disable password authentication; that is why step 3 checks the server's effective configuration.
Do not disable the existing keychain locking policy to make SSH appear to work.

## Before adding the Apple account in Xcode

Read [what Xcode sends and keeps, and the SSH keychain requirements](iphone-mac-signing.md#before-entering-an-apple-account).
The sign-in goes to Apple through Apple's own Xcode; provisioning sends the app/capability, certificate and phone-registration information to Apple's developer service.
The private signing key stays in the Mac user's keychain; Xcode keeps account state and downloaded profiles locally.
No account, password or code is entered into our scripts, the Linux station's partner session or `ios-deploy`.
Apple's public pages do not enumerate every Xcode authentication token or its disk path; the linked audit states that limit.

1. In **Xcode → Settings → Apple Accounts** (Accounts in some versions), add your account yourself and complete any verification prompt yourself. A paid membership is not required: Apple's [Xcode listing](https://apps.apple.com/us/app/xcode/id497799835) says “To test or run applications on an Apple device, all you need is a free Apple Account.” (read 2026-11-21).
2. Select the **Personal Team** and use **Manage Certificates → + → Apple Development** if no signing identity exists. If Xcode does not display the ten-character Team ID, open Keychain Access with Spotlight, select that Apple Development certificate and read **Details → Organizational Unit**. Copy only that non-secret team ID for the session command. Apple documents the certificate field in [QA1886](https://developer.apple.com/library/archive/qa/qa1886/_index.html), read 2026-11-21. Do not copy the account name or any credential into a command, project or report.
3. When signing first requests access to the key, answer Apple's dialog yourself at the Mac. **Always Allow** for `codesign` permits that tool to use that key subsequently. If the keychain later locks, unlock it yourself once before that session. The [SSH explanation](iphone-mac-signing.md#login-keychain-over-ssh) includes Apple's interactive unlock alternative if a Mac-screen unlock does not reach the SSH context.
4. Keep this Mac user logged in and the Mac awake for the first session. Use a stable USB connection, unlock the phone and accept **Trust This Computer** for this Mac. Confirm **Settings → Privacy & Security → Developer Mode** on the phone, restarting and confirming if it was just enabled. In Xcode's **Window → Devices and Simulators**, wait until the phone is ready and resolve any trust/preparation message there.

The three programs occupy the free account's three installed-app slots on this phone.
Apple's [account limits](https://developer.apple.com/help/account/basics/about-your-developer-account/) permit up to ten App IDs and three registered devices, expiring after seven days, and expire free profiles seven days from issuance; renewal is a build and replacement install with the same account and identifiers.
No App Store publishing, paid membership or cloud signing API key is used.

## First command and expected results

After the new Intel session job for commit `94067879dfa4c59af665983db3195ca296657a55` is green and reviewed, the partner prepares this public source on the Mac:

```sh
git clone --no-checkout https://github.com/Sparky-OS/flat-headset.git "$HOME/FlatHeadset-tools"
cd "$HOME/FlatHeadset-tools"
git checkout --detach 94067879dfa4c59af665983db3195ca296657a55
git rev-parse HEAD
```

Stop on any Git error; the last command must print that exact full commit before continuing.
Use a new directory if the named directory already contains work; never erase a checkout to satisfy this step.
From that checkout, use Terminal at the Mac or a key-only SSH shell with no window:

```sh
bash ios/Tools/Mac/first-session.sh --work "$HOME/FlatHeadset-session" --check-host
```

It prints the macOS version, `Xcode 26.3`, host processor, selected tool directory, Metal version and free disk, then `PASS: Mac, Xcode 26.3, Metal and build tools are ready.`
The partner checks source pins in `ios/Tools/Mac/sources.json` against the reviewed commits; they are fetched from our public repositories and checked again by the helper.
For an account-free rehearsal, without the phone, run:

```sh
bash ios/Tools/Mac/first-session.sh --unsigned --work "$HOME/FlatHeadset-session"
```

Expected: one verified commit per repository, three arm64 builds, then one `unsigned build verified; nothing installed` sentence per program.
This compiles the pinned USB installer's source too, but never discovers a phone or signs anything.
The real session uses the non-secret team ID selected above.
In the person's private shell set `TEAM_ID` to that ten-character value with a shell assignment; it is neither the account name nor a password.
Then run:

```sh
bash ios/Tools/Mac/first-session.sh --work "$HOME/FlatHeadset-session" --team "$TEAM_ID"
```

No script prompts for input.
It checks the connected phone, builds KDE Connect, Cardboard and Flat Headset in that order, verifies all three profiles and signatures, then installs them in that order.
For iOS 16 this uses the explicitly named `ios-deploy` USB installer, because Apple's `devicectl` supports iOS 17 and later; signing still belongs entirely to Xcode.
Expected final sentences are `KDE Connect: installed; open it on the phone to check its first screen.`, then the corresponding Cardboard and Flat Headset sentences.
Any failed command stops the sequence with a `STOP:` sentence and the action to take; a partial install is not reported as success for all three.
Keep the work directory private: it contains signed profiles and USB-install logs.
If a signing build fails, its output is not stored by this helper; check the account, keychain and automatic-signing status in Xcode with the person before retrying.
If iOS reports an untrusted developer, open **Settings → General → VPN & Device Management** and trust this account's development apps; verification may need Apple's network service.

## Open, pair, scan, catch

1. Open **KDE Connect** and allow its local-network request. Select the intended PC and approve pairing on both ends. The virtual-monitor page should report whether this paired PC supports the receiver and offer to open Flat Headset.
2. Open **Flat Headset** and allow its local-network request. Its generated left/right picture is only a display check. In **Computers**, the PC paired by KDE Connect should be available through that app's shared identity and certificate trust. There is no second pairing. A missing or refused shared identity is a failure to resolve, not an invitation to authorize an address.
3. Open **Cardboard**, tap **Scan viewer QR code**, allow the camera and scan the viewer's own QR. A full profile becomes ready offline. A shortened link asks whether to resolve it; camera denial, an invalid code or a network error stays visible without substituting a profile.
4. Tap **Use in Flat Headset**, then confirm **Use this viewer** in the receiver. **Import viewer QR link** remains the second way to import a full profile URL.
5. In **Computers**, tap **Catch** for the paired PC. Success means the changing desktop arrives over RDP and is aligned through the actual viewer, with each eye at its own pixels. The generated start picture and an enabled button do not prove reception.
6. Disconnect, reconnect once, then leave the app once. The session/output should be removed on disconnect or backgrounding; the next Catch uses the confirmed profile. Never silently re-pair a changed certificate or invent another optical coefficient.

## Weekly renewal

With the same Mac user, account, Team ID and source pins, connect/unlock/trust the phone and unlock the signing keychain yourself if it has locked.
Run from the same reviewed checkout:

```sh
bash ios/Tools/Mac/renew.sh --work "$HOME/FlatHeadset-session" --team "$TEAM_ID"
```

The helper prints the actual profile expiry in UTC before installation; rebuilding early can reuse a still-valid profile, so do not assume seven new days from every invocation.
At expiration Xcode must obtain a new profile; an expired result stops before installation.
Expect the same three installation sentences, then open the programs and check that KDE Connect still recognizes the paired PC and Flat Headset can Catch from that same trust.
Do not uninstall the programs to renew them.
If Xcode's account session has expired, sign in again in Xcode itself; the helper never requests a password or verification code.
No change of source pin is required just to renew, and new releases are a separate reviewed update.

## One observation for each unknown

| Unknown before the phone | Observation that separates the cases | Next action |
| --- | --- | --- |
| Personal Team sharing | All signed profiles permit their actual prefix and the receiver's two keychain groups; after KDE Connect pairs once, Flat Headset can use that PC | A profile refusal stops before installation; a runtime keychain refusal remains visible. Resolve it; never add a second pairing |
| Pairing over this network | The intended PC appears and both ends confirm the same pairing; Catch is authorized by its pinned certificate | Resolve the localized discovery/trust error; an address alone is never sufficient |
| Camera and profile handoff | A real QR becomes ready and **Use in Flat Headset** opens the receiver's confirmation | Grant camera permission if wanted, or use the paste route; an invalid profile stays refused |
| Hardware decode | A moving desktop appears without the hardware-decoding failure prompt | If it fails, frames stop; choose the explicitly slower, higher-battery software decode for this session or **Go back** |
| Lens alignment | Matching desktop features align through the actual viewer; circles keep their shape and edges stay in their own eye | Keep the actual profile and observation; no invented coefficient or automatic substitution |
| SSH/keychain/USB access | All three installs succeed through the same user's SSH session after the person's setup | An unlock, account or USB error is a distinct stop; GUI login is not assumed to prove SSH access |
| Renewal persistence | After replacement install with the same team/IDs, KDE Connect and Flat Headset still recognize the paired PC | Record retained versus lost trust; installation alone does not prove persistence |

## What the Mac in hand must tell us

| First-start observation | What to record and do |
| --- | --- |
| Arriving macOS | About This Mac's version, then the update needed for Xcode 26.3; do not assume an OS from the Mac's model |
| Activation Lock | A request to unlock with an earlier owner's Apple account means stop for the seller. Apple says it prevents others from using a lost/stolen Mac; erasing is not an unlock. [Apple Support](https://support.apple.com/102541), read 2026-11-21 |
| Management enrollment | A **Remote Management** screen naming another organization means stop for the seller. Apple says this pane cannot be skipped for a device assigned through its organizational enrollment service. Also check System Settings → General → Device Management for remaining profiles. [Setup Assistant](https://support.apple.com/guide/deployment/depdeff4a547/web), read 2026-11-21 |
| Battery | System Settings → Battery → Battery Health: record **Normal** or **Service Recommended**, and the displayed capacity. Apple's [battery guide](https://support.apple.com/guide/mac-help/mh20865/mac), read 2026-11-21, distinguishes those states |
| Keyboard | Compare the physical key legends with the chosen input source; type a harmless test including punctuation in TextEdit before entering any secret |
| First SSH session | `sw_vers -productVersion`, `xcodebuild -version`, `xcode-select -p`, `df -h`, `uname -m`, `xcrun --sdk iphoneos metal --version`; expect Xcode 26.3, Intel `x86_64`, an Xcode developer directory, adequate free space and a Metal version |
| Personal Team and renewal | The profile checks, actual shared pairing and a later seven-day renewal with retained pairing remain real-Mac/phone checks |

The hosted Intel job remains the account-free build proof; only the person's Mac can prove its account/keychain context, USB trust, installation and renewal.
Flat Headset is the static desktop receiver, without tracking; the later iStereoVR pose path is outside this session.
Each installed program already has its own icon; the [function icon facts and prepared Shortcut artwork](iphone-functions.md) remain available if the application shape changes.
