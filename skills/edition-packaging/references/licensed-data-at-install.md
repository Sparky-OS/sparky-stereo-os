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
   A failed download must fail visibly and supply `dpkg-reconfigure ttf-mscorefonts-installer` as the retry command.
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
