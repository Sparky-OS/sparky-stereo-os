# One session for the three iPhone programs

**For the person at the phone and the partner beside them: prepare the three verified packages first, then sign, install, pair, scan and observe the desktop in one session.**
Check freshness first: prepared 2026-11-20 against the reviewed xtool CLI and unsigned workflow.
These are device-session instructions, not a record that installation or reception has happened.
The Cardboard job must be green and its downloaded artifact checked before starting.

## Before the phone session

The partner completes this part without an Apple account or a connected phone.
Use the same successful workflow commit for all three artifacts, and keep the downloaded originals for renewal.
The prerequisites are Python 3.11 or newer, GitHub CLI, `sha256sum`, and the reviewed Linux [xtool release](https://github.com/xtool-org/xtool/releases).
Use the installation already prepared for the [Linux signing route](iphone-arm.md); do not run `xtool setup` or `xtool sdk install` for these ready-built IPAs.
The files below live in a private working directory outside any source checkout.

```sh
read -r -p 'Reviewed green run ID: ' run
read -r -p 'Its full Flat Headset commit: ' commit
mkdir -p iphone-session/artifacts
cd iphone-session
for entry in 'KDEConnect kdeconnect' 'Cardboard cardboard' 'FlatHeadset flat-headset'; do
    set -- $entry
    gh run download "$run" --repo Sparky-OS/flat-headset \
      --name "$1-unsigned-$commit" --dir "artifacts/$2" || exit 1
    (cd "artifacts/$2" && sha256sum -c SHA256SUMS) || exit 1
done
```

Each checksum command must print its IPA filename followed by `OK`.
Download into new empty folders; a download error is a stop, not permission to reuse a different run.
Before scheduling the session, the partner also checks each IPA is one unsigned arm64 iOS executable, has the expected bundle ID, and contains no provisioning profile or embedded dynamic library/framework.
The bundle IDs are `org.sparkyos.kdeconnect`, `org.sparkyos.cardboard` and `org.sparkyos.flatheadset`.
All ten native catalogs and the licence texts must be present.
Keep the matching versions of [iphone-manifest.py](../scripts/iphone-manifest.py) and [iphone-renew.py](../scripts/iphone-renew.py) together in this private working directory.
The first joins the three workflow entries, rejects a mixed workflow commit, verifies every IPA hash and creates a private manifest; it never invokes xtool.

## With the person present

Use a stable USB connection and keep the phone unlocked.
If the connection drops, stop and restore it before retrying an installation; do not repeatedly start installations over an intermittent link.

1. On the phone accept **Trust This Computer** for this computer when prompted.
2. Confirm **Settings → Privacy & Security → Developer Mode** is on; if newly enabled, restart and confirm the phone's request.
3. In the private terminal run `xtool devices`. It must list the intended USB phone; copy its UDID locally, without placing the output in a report, screenshot or repository. If absent, settle USB trust/connectivity first.
4. Run the following command and paste that UDID at its hidden prompt:

```sh
python3 iphone-manifest.py --artifacts artifacts --commit "$commit" --output iphone-apps.json
```

Expected: `PASS: three reviewed IPA hashes and identities; private renewal manifest ready`.
The manifest is mode 0600 and stays private with the packages.
No account has been used yet.

5. The person themselves runs `xtool auth login --mode password` in this real terminal and enters their Apple account, password and any verification code. This is the signing authentication step. Review xtool's displayed anisette-service notice there; no partner records or enters those answers.
6. Run `python3 iphone-renew.py iphone-apps.json --dry-run`. It must print exactly three `xtool install --usb --udid …` commands, in KDE Connect, Cardboard, Flat Headset order, naming these three checked IPAs. Keep that output private too.
7. Run `python3 iphone-renew.py iphone-apps.json`. Expect `Renewing kdeconnect`, `Renewing cardboard`, `Renewing flat-headset`, then `xtool reported all three installations successful…`. Any nonzero exit stops the sequence; the error says which app failed. This command signs and installs using the person's authentication; it needs no SDK.
8. If iOS reports an untrusted developer, use **Settings → General → VPN & Device Management** and trust the developer corresponding to these programs. Verification can need network access. Then open each program.

The account prompt, provisioning and install completion have not been exercised in the SDK-free investigation.
The exact text of Apple's or xtool's authentication responses is not predicted here.
The helper's final line means xtool returned success for all three; the launches below are still required.
See the [Apple-linked signing limits](iphone-arm.md#build-and-installation-boundary): the three applications use the free account's three slots, with seven-day renewal.
Renew with the same `python3 iphone-renew.py iphone-apps.json` command, account and bundle identities.
If saved authentication expires, the person repeats the authentication step first.
Do not delete the apps to refresh them; persistence of their paired identities across renewal is itself an observation to record.

## Open, pair, scan, catch

1. Open **KDE Connect**. Allow its local-network request. The first run should show the device list; select the intended PC and explicitly approve pairing on the phone and that PC. Its virtual-monitor page should report whether that paired PC supports this receiver route and offer to open Flat Headset when available.
2. Open **Flat Headset** once and allow its local-network request. Its initial generated left/right picture is a display check only. In **Computers**, select and pair the same PC, comparing the displayed code before confirming. This is a separate identity from KDE Connect's app. A launch URL never transfers trust.
3. Open **Cardboard**, tap **Scan viewer QR code**, allow the camera, and point it at the viewer's own QR. A full profile should become ready offline. A shortened link presents a network choice; use **Resolve viewer link** only if wanted. A denied camera, invalid code or failed resolution remains a visible message and never substitutes another profile.
4. Tap **Use in Flat Headset**. The receiver should open and ask whether to use the scanned profile for the next connection. Confirm **Use this viewer**. Its Viewer menu should then show the imported QR profile. **Import viewer QR link** remains the second way, for a full profile URL; it does not resolve shortened URLs.
5. Return to **Computers** and tap **Catch** for the paired PC. Success means the live PC desktop arrives through RDP, each eye retains its own pixels, and the physical viewer's alignment is correct. The generated start picture and an enabled Catch button do not prove this.
6. Disconnect, reconnect once, then leave the app once. Confirm the desktop session/output is removed on disconnect or backgrounding and a new Catch uses the confirmed profile. Do not silently re-pair a changed certificate or select another lens profile when a check fails.

## One observation for each unknown

| Unknown before the phone | Observation that separates the cases | Next action |
| --- | --- | --- |
| Identity import and pairing over this network | The PC appears, both sides confirm pairing, and a subsequent connection retains that identity; otherwise the localized discovery/trust/refusal message identifies the stage | Resolve the named stage before Catch; never authorize an address alone |
| Camera and app handoff | A real viewer QR becomes ready; **Use in Flat Headset** opens the receiver's confirmation | If camera permission is denied, the person may enable it in Settings and retry; if opening fails, first open the installed receiver and retry |
| Hardware decoding | A changing desktop appears without the hardware-decoding failure prompt | That is the requested hardware path; if the prompt appears, frames stop and the person chooses the explicitly slower, higher-battery software path for this session or **Go back** |
| Lens alignment | Through the physical viewer, matching desktop features align in both eyes, circles keep their shape and edges remain within their own eye | Record the actual profile and observation; a bad result remains a failure, with no new coefficient or automatic profile substitution |
| Pairing persistence across renewal | After a later seven-day renewal with the same IDs, both apps still recognize the paired PC | Record retained versus lost identity; an installation success message alone does not settle this |

Flat Headset is the static desktop receiver, without tracking.
The later iStereoVR pose path is outside this session.
