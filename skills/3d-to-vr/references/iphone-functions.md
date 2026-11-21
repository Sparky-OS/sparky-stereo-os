# iPhone package shapes and function icons

Checked 2026-11-20 against Apple's documentation and the current receiver sources.
The built shape is three separate programs sharing one KDE Connect pairing.
The receiver inside KDE Connect is a comparison, not a second built package.
The [session page](iphone-session.md) now uses Xcode on the Mac, with the person adding the account there; its new helper must pass hosted review before the hardware session.

## Installation and seven-day renewal

| Shape | Programs to install | Pairings per PC | Free signing slots | What each seven-day renewal touches |
| --- | --- | --- | --- | --- |
| Built: shared pairing | KDE Connect, Cardboard, Flat Headset: 3 | 1, only in KDE Connect | 3 of 3; none spare | Reprovision, sign and replace all three apps with the same account, team and bundle identifiers; the receiver's profile must still permit KDE Connect's keychain group |
| Receiver inside KDE Connect | KDE Connect including Flat Headset, plus Cardboard: 2 | 1, only in KDE Connect | 2 of 3; one spare | Reprovision, sign and reinstall the combined KDE Connect IPA and the Cardboard IPA; no cross-app keychain grant for reception |

Apple's [developer account overview](https://developer.apple.com/help/account/basics/about-your-developer-account/) says: “You can install up to 3 apps per device.”
It separately limits registered App IDs to ten and devices to three, with seven-day expiry; installed-app provisioning expires seven days from issuance.
The table assumes no other free-provisioned apps or app extensions, and the host-side signing tool consumes no phone slot.
A function icon or a Shortcuts shortcut is not another installed development app and consumes no additional slot.
Neither shape changes the signing authentication boundary.
Renewal must retain data rather than uninstall first; actual pairing persistence across renewal is still a device test.
The current Mac renewal helper builds and installs three programs; a combined build would need its source pins and install list adjusted to two, not a dummy third app.

The [keychain audit](iphone-auth.md#one-pairing-under-a-free-account) establishes the documented free-provisioning route for the built shape; the actual returned profile and cross-app access remain device gates.
The shared shape keeps three independent build artifacts and requires the Xcode shared-group entitlements and receiver checks.
The combined shape would build the same receiver source files into KDE Connect, replace the separate app entry point with an internal presentation route, and use KDE Connect's identity and trust in-process.
It would retain Cardboard's profile handoff and the receiver's lifecycle checks, including closing its RDP session on backgrounding.
That integration, unsigned combined build and manifest change have not been done; the conditional reason for switching shapes has not been established.
This table does not choose between them.

## What an icon can do

**A person-added Shortcuts icon can open Flat Headset directly in either shape, provided the installed app owns and handles `flatheadset://catch`.**
The current separate receiver handles this exact link by opening its Computers screen, where the person selects the already paired PC and taps Catch.
“Directly” means that receiver screen, not automatic connection to a PC and not bypassing pairing.
Source: [Launch.hpp](https://github.com/Sparky-OS/flat-headset/blob/209961bb3e446a7b70a450af47f23b8ab87e4e9c/ios/Sources/Launch.hpp#L6) accepts the exact link, and [Main.mm](https://github.com/Sparky-OS/flat-headset/blob/209961bb3e446a7b70a450af47f23b8ab87e4e9c/ios/Sources/Main.mm#L161) dispatches to Computers.

Apple's [alternate-icon API](https://developer.apple.com/documentation/uikit/uiapplication/setalternateiconname(_:completionhandler:)) says: “Changes the icon the system displays for the app.”
It selects the primary icon or one alternate; it does not define separate function entry points or add a second differently routed icon.
The documented primary/alternate-icon model therefore does not provide Android-style launcher aliases for one iPhone app.
This is a conclusion about that API, not a claim that iOS forbids every duplicate placement of an app on Home Screen pages.
No Apple documentation found in this check promises independently routed app-icon duplicates.

| Mechanism | What the person gets | Setup cost for the person | Work in the app |
| --- | --- | --- | --- |
| App's ordinary icon | Opens that installed program; the separate Flat Headset already has its own app entry | Install the program; place its icon where wanted | Existing app entry point; a combined KDE Connect icon would normally open KDE Connect |
| Alternate app icon | A different appearance for the same app icon, not an additional function launcher | Choose an offered icon in the app | Bundle alternatives and implement selection; not implemented here |
| Home Screen quick action | Touch/press and hold the app icon, then select a function in its menu; not a second grid icon | No shortcut setup for static actions; press and select each time | Define the item and route both cold and warm launches to the function; not implemented here |
| Shortcuts Home Screen icon | Its own name and picture; one tap runs a shortcut opening the receiver link | Create the two-action shortcut below, choose the picture and add it once | Existing URL handler suffices for the separate receiver; a combined app must register and route the same link |
| Apple's Shortcuts widget | A tappable shortcut tile, occupying widget space | Create the shortcut, add a Shortcuts widget and select that shortcut or its folder | Same URL handler; no widget extension of ours |

Apple's [Home Screen quick-action guidance](https://developer.apple.com/design/human-interface-guidelines/home-screen-quick-actions/) says: “you can provide a total of four.”
Its [UIKit API](https://developer.apple.com/documentation/uikit/uiapplicationshortcutitem) says: “The system registers your static quick actions when your app is installed.”
The person still invokes a menu and chooses an action; this does not meet a request for a separate grid icon by itself.
Static and dynamic actions share the displayed limit, rather than four each.

Apple's [Shortcuts URL-scheme guide for iOS 16](https://support.apple.com/en-au/guide/shortcuts/apd68802640c/6.0/ios/16.0) describes using the “URL action” and “Open URLs action” for another app's scheme.
Its [Home Screen guide](https://support.apple.com/en-lamr/guide/shortcuts/apd735880972/ios) says: “You can add shortcuts to the Home Screen, and optionally group them into folders.”
The same page documents selecting an image through Files or Photos and choosing the displayed name.
Apple also documents [running shortcuts from its widget](https://support.apple.com/en-euro/guide/shortcuts/apd029b36d05/ios): “The small Shortcuts widget displays a single shortcut of your choice.”
The URL-scheme guide was checked in its iOS 16 version; the Home Screen and widget pages were checked in their current versions, so exact menu placement on iOS 16 remains a session observation.
No account, phone, Apple asset or SDK was used for this preparation.

## Prepare the Flat Headset icon

The [existing Android Flat Headset pictures](../assets/iphone-shortcut/README.md) are supplied unchanged, with attribution and licence, for selecting from Files in Shortcuts.
These are ordinary 2D launcher images, not stereo pairs or optical calibration images.
They are not new app-icon assets compiled into an IPA, and their appearance under iOS cropping has not been observed.

After the session's sign-in and installation gates have been cleared, the person can create this shortcut:

1. Save [flat-headset.png](../assets/iphone-shortcut/flat-headset.png) to Files on the phone; the [round picture](../assets/iphone-shortcut/flat-headset-round.png) is also available.
2. In Shortcuts, create a new shortcut named **Flat Headset**.
3. Add a **URL** action with the literal `flatheadset://catch`, then **Open URLs**, taking the first action's output. No PC address, account, certificate or credential goes into it.
4. In the shortcut's details/share controls, choose **Add to Home Screen**, set the displayed name to **Flat Headset**, select the supplied picture from Files, and tap **Add**.
5. Tap that icon: it should open the receiver's **Computers** screen. If it does not, record the displayed error; do not substitute a browser receiver or add a pairing. Test once with the receiver closed and once already open.

The person may see an iOS permission/confirmation for opening the app; its actual wording and first-run behavior remain untested.
The shortcut itself needs no weekly development signing, but it cannot run an expired or missing native receiver.
It does not authorize a PC or change KDE Connect's trust.
This is a manually created shortcut, not a signed `.shortcut` download or an iCloud share; no account-dependent shortcut distribution has been prepared.

## If the receiver is built into KDE Connect

The same Shortcuts icon and `flatheadset://catch` link would open the internal receiver screen once KDE Connect owns the scheme and dispatches it there.
KDE Connect would also handle the existing `flatheadset://viewer` profile route, retaining explicit profile confirmation.
The standalone Flat Headset package must leave the set; do not leave two apps registering `flatheadset` and assume which receives a link.
Apple's [custom URL scheme documentation](https://developer.apple.com/documentation/xcode/defining-a-custom-url-scheme-for-your-app) says: “If multiple apps register the same scheme, the app the system targets is undefined.”
Keep URL input validation and the KDE Connect trust checks on both entry paths.
The receiver files stay one source, built into KDE Connect rather than copied into a second maintained implementation.
These are the integration obligations for that shape, not a claim that it has been built or tested.

## Traps

- **Symptom:** a proposed second function icon replaces the first app icon. **Cause:** confusing alternate appearance with another launcher entry. **Fix:** distinguish the alternate-icon API, quick-action menu and person-added Shortcuts icon. **Found by:** Apple's API description and Shortcuts guide.
- **Symptom:** a link opens an unexpected program after combining the receiver. **Cause:** both packages still register the same URL scheme. **Fix:** only the combined package owns it when the standalone package leaves the set. **Found by:** Apple's custom-scheme warning, not a phone reproduction.
- **Symptom:** the three-slot count is applied to every icon. **Cause:** counting shortcuts as independently provisioned apps. **Fix:** count the installed native packages; the shortcut still depends on its native target's valid signing. **Found by:** the account limit and Shortcuts' documented URL dispatch.
