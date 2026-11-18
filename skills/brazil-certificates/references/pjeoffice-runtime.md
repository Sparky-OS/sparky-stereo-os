# PJeOffice Pro runtime boundaries

Measured on 2026-11-18 with the unchanged CNJ Linux x64 2.5.16u ZIP.
These are startup and component probes, not a completed court login or a signed PDF qualification.

## Recipe

Use a disposable Debian testing container, no host desktop sockets, no physical reader and no network for the signing fixtures.
Disable core dumps and run the program as an ordinary user.
Fetch the ZIP twice from the link in [TRF3's guide](https://pjeoffice.trf3.jus.br/pjeoffice-pro/docs/userguide.html), compare the files and record both SHA-256 values.
Apply the two executable permissions that its launcher sets for `jre/bin/java` and `ffmpeg.exe`.
Give each case a fresh HOME.
Run the launcher's JVM arguments in the foreground to retain exceptions, keeping the jar unchanged.

The reusable probes are in `tools/pjeoffice-audit` of the [build repository](https://github.com/Sparky-OS/sparky-stereo-os-build).
`startup.py APP JAVA OUT [JVM_ARGUMENTS...]` starts an isolated Xvfb and records process state and localhost replies.
`token-fixture.sh NEW_SCRATCH_DIRECTORY` generates a test identity, initializes SoftHSM, imports the test key/certificate, verifies a challenge and requires an altered challenge to fail.
It writes an A1 PKCS#12 file too; all its keys, PIN files and token storage are disposable.
Run these scripts inside the container only, and remove the complete scratch directory afterwards.

Compile the Java probes using `javac --release 8` and run them with the selected Java and unchanged PJeOffice jar on the classpath.
`ProviderProbe file PIN_FILE P12_FILE` verifies a synthetic challenge using the generated A1 identity.
`ProviderProbe softhsm PIN_FILE MODULE` invokes the jar's own provider constructor and verifies a synthetic challenge through that provider.
These component probes do not execute a PJeOffice signing task.
`UpdaterPermission` invokes the original preliminary permission check; it does not install a patch.
`TrustProbe` enumerates the selected JVM's default TLS trust manager; it does not verify a signed document or the application's entire certificate policy.

## Java results

| Java | Observation |
| --- | --- |
| Bundled Azul Zulu 8.72.0.17, Java 1.8.0_382 | Application startup and localhost ping pass; generated file and SoftHSM challenge probes pass |
| Debian OpenJDK 21.0.13.0.3+1-1 | Startup with OpenJFX 21 passes; file challenge passes; upstream PKCS#11 constructor fails without the export below and passes with it |
| Debian OpenJDK 25.0.5+8-1 | Same component results as 21 |
| Debian OpenJDK 28~18ea-1 | Full OpenJFX 21 module set fails before main; file and PKCS#11 component results match 21 when JavaFX is not loaded |

OpenJFX was Debian 21.0.12+3-3.
The full module set was `javafx.controls,javafx.swing,javafx.web,javafx.media,javafx.fxml`, with `--module-path /usr/share/openjfx/lib`.
OpenJFX 21 on Java 28 reports `java.lang.module.FindException: Module jdk.jsobject not found, required by javafx.web`.
This is a module-set failure, not proof that every application path fails on Java 28.
The JavaFX cutter was not qualified.

## Traps

**Symptom:** startup succeeds on Java 21 or 25, but constructing a token provider fails.
Cause: `com.github.signer4j.provider.SunPKCS11Creator` reflects on `sun.security.pkcs11.SunPKCS11`; the cryptoki module does not export that package.
The cause was found by running the jar's constructor with the generated SoftHSM fixture and reading its nested `IllegalAccessException`.
With `--add-exports=jdk.crypto.cryptoki/sun.security.pkcs11=ALL-UNNAMED`, the same constructor and independently verified challenge succeed on the measured Java 21, 25 and 28.
This launcher argument requires full application signing qualification before becoming a shipping choice.

**Symptom:** a plain GET to localhost receives HTTP 403 although startup opened the listener.
Cause: the application's secure request filter expects its documented preflight-compatible request shape.
The cause was found in the application's rejection log and its bundled integration JavaScript.
The documented ping uses PUT to `/pjeOffice/?u=18`, `Content-Type: application/json`, `Force-Preflight: true`, and a local Origin.
That exchange returned HTTP 200 with `{"success": true}`; `/pjeOffice/versao/?u=18` returned version 2.5.16 and the selected Java properties.
This was an HTTP client reproduction of the browser protocol, not a browser execution or a court login.

**Symptom:** OpenSC's module sees no SoftHSM token.
Cause: the modules implement different token backends.
[SoftHSM](https://www.opendnssec.org/en/latest/softhsm/) implements its own software PKCS#11 provider; OpenSC exposes supported smart cards.
OpenSC's `pkcs11-tool --module libsofthsm2.so` can exercise SoftHSM; this does not mean `opensc-pkcs11.so` can expose it.
A test requiring SoftHSM through the OpenSC module must be corrected to the SoftHSM module or p11-kit's proxy, or use a separate virtual PC/SC card fixture.
The cause was established with module enumeration against one generated token, a running PC/SC daemon, and the same jar's provider constructor.
OpenSC's provider reported `slotListIndex is 0 but token only has 0 slots`.
No hardware-token compatibility claim follows from this test.

**Symptom:** Sparky CA installs ICP-Brasil roots but the bundled Java's default trust manager finds none.
Cause: the bundled Java uses its private trust store, while Debian's Java consumes ca-certificates-java's generated store.
With the published Sparky CA 2.0.4 installed without recommends and `sparky-ca install icp-roots` run in a container, the Debian Java 21 probe changed from zero to five accepted ICP-Brasil TLS issuers, and the bundled Java stayed at zero.
The installed roots seen by Debian Java were v5, v6, v10, v11 and v12.
Ed521 was skipped in this fixture because the optional OpenSSL provider was not installed.
This does not prove PJeOffice validates every signing chain through that manager.

**Symptom:** an ordinary user cannot pass the self-updater's preliminary check in a root-owned installation.
Cause: `Updater.checkWritingPermission()` tries to create and remove `write.test` inside `pjeoffice_home`.
The unchanged method returned false with `AccessDeniedException` in a root-owned folder and true in a user-owned folder.
With the original update properties, `isDisabled()` returned false in both; with `update.url=disabled`, it returned true.
No patch was applied, so later patcher failure handling and atomic replacement remain unqualified.
`HttpVersionChecker` fetches `update.properties`; the live file reported app.version 2.5.16.
A distribution-managed root-owned installation needs its own update transaction and the upstream updater explicitly disabled.

**Symptom:** PJeOffice reports no tray support inside a working Plasma Wayland login.
Cause: `PjeOfficeFrontEnd.supportsSystray()` requires `SystemTray.isSupported()` and rejects Unix platforms with `Jvms.isUnix()`.
The cause was found by inspecting the unchanged method, then comparing both calls inside a fresh `startplasma-wayland` login with Xwayland.
The platform call returned true and the application call false, with the SNI host registered and an XEmbed selection owner present.
The application registered no SNI item and opened its own desktop window instead.
Do not claim that installing another tray proxy enables this binary's Unix tray.
A supported upstream option or a separately designed KDE integration would be needed; the binary was not patched.

For an isolated login probe, inherit DISPLAY, XAUTHORITY and WAYLAND_DISPLAY from a normal client in that same private session.
The script that starts `startplasma-wayland` does not inherit the session's X11 credentials back from its child.
The first fixture had no DISPLAY and raised HeadlessException; assuming `:0` without the session's XAUTHORITY then raised AWTError.
Reading only those three variables from the container's own plasmashell process corrected the fixture.
Reading KWin's environment can be refused because its executable has capabilities.
No environment or socket from the host session is needed.
