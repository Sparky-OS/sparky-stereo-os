# Licensed data downloaded during installation

## Working recipe

1. Reconcile before changing package selection.
   In a disposable container with the image's sources and pins, run `apt-cache policy ttf-mscorefonts-installer` and download the candidate with `apt-get download ttf-mscorefonts-installer`.
   Record its version, origin and SHA-256.
   Extract its payload with `dpkg-deb -x PACKAGE.deb payload` and its maintainer metadata with `dpkg-deb -e PACKAGE.deb metadata`.
   Read the active installer sequence, package operations, first-run handlers and generated task lists, including published packages rather than only source folders.
2. Check consent in the actual `metadata/templates`, `metadata/config` and `metadata/postinst`.
   Search for `accepted-mscorefonts-eula` and read the surrounding control flow.
   A debconf value set by a test fixture does not establish that the package asks for or honours it.
   Where explicit consent is required, show the licence and obtain the person's answer before the first download.
   Never put an automatic acceptance into the image or installer.
3. Put the selection in the target system's installation path.
   A package installed while building the live root file system can download its data onto the ISO.
   A role list alone does not establish that the active installer selects it.
   Verify `contrib` in the target's Debian sources when selecting the Debian core-font installer.
4. Use the existing install-time download declaration.
   Binary control fields are `Sparky-Install-Download-Size`, a positive number of bytes, and `Sparky-Install-Download-Source`, an HTTPS address.
   Source control uses `XB-Sparky-Install-Download-Size` and `XB-Sparky-Install-Download-Source`.
   Measure the data download separately from the `.deb` size.
   Both apt's hook and Stereo APTus read these fields through the shared reader in `sparky-stereo-apt`.
   Do not add separate frontend or package warning mechanisms.
5. Test the installed result in separate, fresh containers.
   Acceptance must install real font files and make `fc-match Arial` select Arial.
   Refusal must leave no downloaded fonts and explain the result.
   A failed download must fail visibly and supply `dpkg --configure ttf-mscorefonts-installer` after the connection is repaired; use `dpkg-reconfigure ttf-mscorefonts-installer` after a deliberate refusal.
   On a metered connection the shared notice must show the measured size and source in the frontend the person used before fetching the data.
   Keep an unmetered control and inspect the resulting ISO for both package selection and font data.
6. Before modifying upstream packaging, search current upstream sources, changes and reports, and carry an existing suitable implementation with credit.
   Separate archive inspection from a runtime test and from a completed installer run in the handoff.

## Traps found by core-fonts-at-install-519

- **Symptom:** a fixture sets `msttcorefonts/accepted-mscorefonts-eula`, but the package never asks that question.
  **Cause:** Debian testing's `ttf-mscorefonts-installer` 3.8.1 has five templates for download location, invalid location, saved files, mirror and proxy, with no acceptance template or check in its config or postinst.
  **Fix:** implement the required consent using inspected packaging and installer interfaces before wiring automatic selection; do not treat a preseed as proof of consent.
  **Found by:** `apt-cache policy`, authenticated archive download and `dpkg-deb -e`, followed by reading all three maintainer files.
  The inspected archive SHA-256 was `8b2d9b10fbddfd3f1083b8a4d7724c766d681ccb8392566c8ffbaf168d3a19f2` on 2026-11-11.
- **Symptom:** an install-time data download has no shared size notice.
  **Cause:** the inspected Debian 3.8.1 binary control has neither `Sparky-Install-Download-Size` nor `Sparky-Install-Download-Source`.
  **Fix:** add the declaration in the package that performs the download, through the edition's packaging, and verify that it reaches the Packages index and both frontend paths.
  **Found by:** comparing `dpkg-deb -f PACKAGE.deb` with the shared reader and its existing test in `sparky-os/packages/sparky-stereo-apt/tests/test-install-downloads.sh` of the build repository.
- **Symptom:** adding an `install` item to Calamares' package operations appears to satisfy a consent requirement without any visible prompt being demonstrated.
  **Cause:** the inspected Calamares 3.4.3 Sparky apt backend invokes `apt-get -q -y install`; that invocation alone establishes no licence UI.
  **Fix:** prove the person's consent through the actual installer UI and target installation, including refusal, rather than relying on the package operation's name.
  **Found by:** reading the published `packages/main.py`, `packages.conf` and the active settings sequence.
- **Symptom:** the no-install-downloads ISO gate appears sufficient for unmodified upstream downloader packages.
  **Cause:** the inspected gate checks declaration fields and FlightGear's data path; unmodified Debian core fonts have no declaration and are not covered by that path check.
  **Fix:** check the font data and prohibited package explicitly as well as declaring downloads; preserve an ISO rejection case when implementing the integration.
  **Found by:** comparing `iso-build/check-no-install-downloads.py` with the inspected binary control.

## Useful existing behaviour

Debian 3.8.1's `mstt_exit_with_error` prints that the fonts are not installed, supplies the reconfigure command and exits 1.
Retain that behaviour when adding consent and declarations.
This is source inspection of the failure handler, not a network-failure test.
The package records CAB-file SHA-256 checksums in `var/lib/msttcorefonts/cabfiles.sha256sums`, which provides an existing integrity mechanism to inspect before writing another downloader.

## Target installation recipe, ORDER 519

The build repository's `sparky-os/packages/msttcorefonts/build.sh` rebuilds verified plain Debian 3.8.1, with Michael Vogt's Ubuntu EULA presentation adapted to Debian's synchronous downloader.
Set `OUT` to an empty output directory and run the recipe from a committed checkout.
The recipe uses the commit date, downloads the pinned Debian native source and checks SHA-256 `211f86e82b56cf87461da4bb21136b096a57ae70ed9bcb6eb27f34c407295bf3`.
It builds plain authored source and binary candidates for testing; publication must still run the edition's Lean Code qualification.
Never import a published `+lc1` tree as authored source without the plain-source restoration tool.

The 11 CAB archives measured on 2026-11-11 total **3,934,864 bytes**, with every SHA-256 matching Debian's `cabfiles.sha256sums`.
The candidate declares that total and `https://downloads.sourceforge.net/corefonts/` in the shared control fields.
The Microsoft font data is absent from both the binary package and its source archive.
The ISO gate also rejects an undeclared stock installer package and the downloaded font directory, so forgetting the declaration cannot let fonts onto the image.

The live installer carries `calamares-settings-sparky-stereo`'s `lib/core-fonts` helper.
Calamares invokes `core-fonts --window TARGET`; the text installer invokes `core-fonts --terminal TARGET` before unmounting the target.
The text path runs the target's interactive apt with debconf's readline frontend. The graphical path shows a KDE window; never open a terminal from Calamares for the licence.
The helper enables `contrib` on enabled HTTPS Debian sources in classic or deb822 form, preserving other sources and components.
It requires the candidate's download declaration before starting installation.
The package's default consent answer is false, and the helper never supplies an answer.
The person's deliberate refusal is printed with a retry command and allows the operating-system installation to continue without those fonts.
A download failure fails the apt transaction and is reported by the installer.

Run `tests/runtime.py` from the font recipe in separate disposable containers with the real shared apt hook and its language files installed.
The test indexes the real candidate in a local apt source and types the test answer into debconf rather than preseeding acceptance.
The `accept`, `refuse`, `noninteractive` and `failed-download` cases check actual fonts, consent presentation, visible results and retry guidance.
The `metered` and `unmetered` cases substitute only NetworkManager's answer, keeping apt, the reader and package metadata real.
The retry cases run from the refused or failed installation state and check real Arial with fontconfig.
For the graphical join, `tests/corefonts-gui.py` in the Calamares settings recipe runs in a fresh private KWin Wayland / D-Bus session, with the published edition KWin and Qt packages and a copied target root.
Drive actual Wayland input and capture with KWin ScreenShot2; Xvfb and terminal text do not prove this path.
Keep English and another language, acceptance, refusal and window-close captures, the actual debconf answer and the target font/package state.
Build the root yourself from the build scripts' published sources and pins. Name every omitted layer when the root is partial; do not ask for a developer-image fixture the scripts already define.

## KDE debconf integration

Debian testing's `debconf-kde-helper` and `libdebconf-kde1` 1.2.1-1 use Qt6. Inspect the actual archive candidate rather than assuming an older Qt5 implementation.
`DEBIAN_FRONTEND=kde` starts the stock helper with inherited FIFO descriptors. It would run inside the target chroot and need the live desktop's runtime socket there.
For Calamares, embed `DebconfKde::DebconfGui` in the live root and use its documented UNIX socket interface: target `DEBIAN_FRONTEND=passthrough`, `DEBCONF_PIPE=/run/.../debconf`, with the same socket created at `TARGET/run/.../debconf` by the live process.
This is the KDE debconf renderer and protocol; no GUI licence parser or acceptance preseed is needed.

The stock boolean widget calls its radio choices OK/Cancel. A small native embedding can offer explicit translated Accept/Decline actions and still let KDE debconf send/store the answer.
Queue the licence note and default-false boolean before one `db_go`, so the scrollable licence and consent actions share a window.
Only an actual Accept action selects true. Decline is the keyboard default, and closing the licence submits false through the same frontend, then shows that fonts were not installed and how to retry.
Do not cancel the frontend connection on licence close and accidentally invoke debconf's automatic fallback.
Keep the original legal text intact; localize the question, actions and result in all edition languages.

Read the candidate's declaration with the shared ORDER 399 `declaration()` and `assess()` functions in `sparky_install_downloads.py`.
Render the same metered decision, measured bytes and source in the graphical frontend before apt installs the package. Replace only the reader's terminal instruction with the frontend's buttons.
Suppress the duplicate terminal notice for that already-displayed transaction only; do not create another package size table or metering policy.
Check frontend startup before apt, fail visibly if it disappears, and keep refusal separate from a failed download. Both must say the next action in the person's frontend.

## Further traps found during the implementation

- **Symptom:** refusal displays the same EULA question twice in one apt transaction.
  **Cause:** apt preconfiguration and postinst both invoke debconf's config script; unconditionally resetting `seen` after a false answer discards the first refusal.
  **Fix:** honour the first answer during ordinary configuration, and reset the prompt after refusal only for an explicit `reconfigure` call.
  **Found by:** the original terminal refusal test stopped at the second question; the earlier candidate's transcript contained two questions and failed the new single-question assertion.
- **Symptom:** a scripted acceptance still refuses the licence, with `noyes` visible in the transcript.
  **Cause:** readline pre-fills the default `no`, so a test that appends `yes` does not replace the default.
  **Fix:** clear the input with Ctrl+U before typing the test answer, and advance the EULA's `[More]` pages before answering.
  **Found by:** reading the real terminal transcript and the retained terminal transcript.
- **Symptom:** Calamares opens a terminal with a paged licence and a typed answer.
  **Cause:** reusing the text installer's readline presentation for the graphical route.
  **Fix:** use KDE debconf in a live window; retain readline only for the text installer. A terminal completion-file workaround does not meet the graphical design.
  **Found by:** review against the newcomer/defaults decision, followed by Debian testing frontend source inspection.
- **Symptom:** `dpkg-reconfigure ttf-mscorefonts-installer` reports that the package is broken or not fully installed after a failed download.
  **Cause:** Debian's synchronous downloader exits 1, leaving the package half-configured, and dpkg-reconfigure requires `--force` in that state.
  **Fix:** retain `dpkg-reconfigure ttf-mscorefonts-installer` for a deliberate refusal, and use `dpkg --configure ttf-mscorefonts-installer` to retry failed configuration after repairing the download problem.
  **Found by:** reading dpkg-reconfigure's installed-state check and strengthening the real recovery test to assert both Arial and dpkg's `installed` state.
  The earlier `--force` suggestion restored fonts but left the package half-configured; that attempt is retained as a failing regression control.
- **Symptom:** direct source extraction cannot find `msttcorefonts-3.8.1/debian/changelog` although apt source extraction worked.
  **Cause:** the verified native tarball contains `msttcorefonts/`, while apt names its extraction with the version.
  **Fix:** create the destination explicitly and extract with `--strip-components=1` after checking the archive hash.
  **Found by:** the build-driver rehearsal and inspecting the archive's top-level members.
- **Symptom:** an isolated target's apt update cannot resolve archive hosts.
  **Cause:** exporting a container omits the contents of its mounted resolver file.
  **Fix:** provide the disposable target with its test container's resolver and CA bundle before running the actual install helper.
  **Found by:** the apt diagnostic in the isolated terminal, which occurred before any licence question or font download.

- **Symptom:** the KDE window offers generic OK/Cancel choices rather than explicit licence actions.
  **Cause:** libdebconf-kde's generic Boolean widget uses KStandardGuiItem labels.
  **Fix:** keep its renderer and socket protocol in a native embedding and customize the licence actions; package that executable through the native Lean Code pipeline, separately from the script-only settings adapter.
  **Found by:** inspecting Debian's authenticated source and upstream DebconfBoolean.cpp / DebconfGui.h before implementing the installer join.
- **Symptom:** a partial root has unpacked but unconfigured Calamares and installer packages.
  **Cause:** mount-skipped mmdebstrap has no proc for systemd-tmpfiles; GRUB probes the container filesystem; Sparky artwork expects desktop-base's directories.
  **Fix:** retain the build script's os-prober and grub-mkconfig diversions, include desktop-base from its base list, and finish the authored root as an ordinary Docker container with its own proc/dev namespace. Name this adaptation and omitted hardware/ISO stages; never claim a boot test.
  **Found by:** retained dpkg errors for cryptsetup-bin, sparky-info and sparky-artwork in the published-repository partial-root build.
- **Symptom:** a host tar stream omits files with permission-denied errors.
  **Cause:** files created by container root are not necessarily readable by the host user, especially private skel settings.
  **Fix:** export/tar the owned root from inside its container and check the pipeline's status; do not relax packaged file permissions to make a copy work.
  **Found by:** the partial-root export's explicit tar diagnostics.
