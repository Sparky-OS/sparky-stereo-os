# PJeOffice Pro runtime boundaries

Measured on 2026-11-18 with the unchanged CNJ Linux x64 2.5.16u ZIP.
Synthetic PDF and login tasks were run through the actual application on bundled Java 8 with a file identity, SoftHSM and a local callback server.
No court login or physical-card signing was performed.

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
The cutter opens on bundled Java 8 and Debian Java 21, but both reject the synthetic H.264/AAC MP4.
The shared JavaFX media API fails with MediaException, caused by com.sun.media.jfxmedia.MediaException: Could not create player!
Its DEBUG output reports ERROR_MEDIA_AUDIO_FORMAT_UNSUPPORTED, including on a video-only control.
A native-loader trace tries libavcodec majors up to 59 on bundled Java and 60 on Debian OpenJFX, while testing supplies major 63.
This is separate from the external FFmpeg executable.
The unchanged jar’s video-slice handler successfully cuts 1–4 seconds with bundled FFmpeg 5.1.1 and system FFmpeg 9.0.2; both outputs contain H.264/AAC and have duration 3.08 seconds.
Set ffmpeg_home to a directory containing the literal filename ffmpeg.exe; the system test used a symlink to /usr/bin/ffmpeg.

## Traps

**Symptom:** startup succeeds on Java 21 or 25, but constructing a token provider fails.
Cause: `com.github.signer4j.provider.SunPKCS11Creator` reflects on `sun.security.pkcs11.SunPKCS11`; the cryptoki module does not export that package.
The cause was found by running the jar's constructor with the generated SoftHSM fixture and reading its nested `IllegalAccessException`.
With `--add-exports=jdk.crypto.cryptoki/sun.security.pkcs11=ALL-UNNAMED`, the same constructor and independently verified challenge succeed on the measured Java 21, 25 and 28.
Full task enumeration additionally needs `--add-exports=jdk.crypto.cryptoki/sun.security.pkcs11.wrapper=ALL-UNNAMED`.
Without it, PKCS11Driver raises IllegalAccessError for CK_C_INITIALIZE_ARGS, and the UI says the operation was cancelled.
Even with both exports, the actual task still fails the certificate filter described below; component success does not qualify system Java.

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
The official patcher was subsequently run through download, SHA-1 verification, extraction and file replacement, as an ordinary user.
A complete user-owned installation was patched and restarted, and the restarted signer answered its localhost ping.
Every installed patch file matched the official update ZIP bytes.
The root-owned target displayed the administration-permission error and retained its original files.
The installed-version property was a synthetic 2.5.15 trigger because the older official archive URL returned 403; this measures the full patch path, not a genuine old-binary version upgrade.
Power-loss rollback and atomicity were not fault-tested.
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

## Full task recipe and additional traps

The build repository's `tools/pjeoffice-audit/README.md` carries the full fixture recipe.
For the file case use the application's list.a1 setting; for the software token use list.a3 with the installed SoftHSM module.
The application also accepts p11-kit-proxy.so, with SoftHSM registered in the private test user's p11-kit module directory; its login challenge verifies too.
The uninitialized spare SoftHSM slot logs CKR_TOKEN_NOT_RECOGNIZED but the initialized token remains usable.
A generated PIN is entered only into the application dialog; no real identity or PIN is needed.

PDF signing uses the official ShellExtension local action, cnj.assinador with samefolder, DEFINIDO, CADES, ATTACHED and SHA256withRSA.
The result is an attached CAdES `.pdf.p7s` sidecar.
OpenSSL independently verifies the generated chain and signature, and the extracted content equals the original PDF bytes.
The CMS includes contentType, signingTime, messageDigest and CMSAlgorithmProtection.
Overriding the content with altered bytes fails verification for both file and SoftHSM cases.
The login callback contains a raw SHA256withRSA signature and a DER PkiPath certificate sequence, not PKCS#7.
It has no CMS signed attributes by format.
The file callback contains leaf and test root; SoftHSM returns only the imported leaf, whose chain verifies against the separately generated test root.

**Symptom:** a valid generic test certificate does not appear in the application's chooser.
Cause: PjeCertificateListAcessor requires digitalSignature and a recognized PF or PJ otherName.
The cause was found by inspecting that unchanged predicate and OIDReader, then adding a synthetic all-zero PF field to the generated leaf.
The fixture's SAN uses `otherName:2.16.76.1.3.1;UTF8:` followed by 51 zeros.
This makes an accepted test identity, not a government-issued or legally valid ICP-Brasil certificate.
Do not disable the application's filter to make a fixture pass.

**Symptom:** on Java 21 the same certificate is filtered out even after both token exports are supplied.
Cause: OIDReader requires each SAN entry's size to equal two; the JDK SUN provider returns four elements for this otherName on Java 21, versus two on bundled Java 8.
The cause was found by a same-certificate SanShape comparison and the actual task's warning, “Subject alternative list must have at least 2 entries (keystore bug?)”.
The Java 21 [X509Certificate API](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/security/cert/X509Certificate.html) explicitly permits the third and fourth elements.
The observed fix requires the owning application's compatible certificate reader; it was not applied to the official jar.
Retain bundled Java as the measured signing control until a supported current runtime passes full tasks.

**Symptom:** OpenSC loads but the application's certificate chooser is empty without a card.
Cause: there are no PC/SC slots, not a missing SoftHSM installation.
A file-system trace records probes of /usr/lib/opensc-pkcs11.so, /usr/local/lib/opensc-pkcs11.so, /usr/lib/x86_64-linux-gnu/opensc-pkcs11.so and its pkcs11 subdirectory alias.
The application saves the installed multiarch path automatically and loads it successfully.
The raw slotListIndex exception came from the separate provider-constructor probe; the actual application shows an empty chooser with disabled OK and a configuration link.
Physical-card signing through OpenSC is not proven.
Debian's vsmartcard-vpcd and python3-virtualsmartcard 3.3+dfsg-2 were tried as a bounded fixture lead.
The normal vicc CLI is in the separate vsmartcard-vpicc package.
Its --help works, but actual cryptoflex startup fails to find virtualsmartcard.
With the installed library directory in PYTHONPATH it fails importing Crypto, followed by its obsolete sha fallback.
No card containing a signing key was established; the library-only first attempt was not the final feasibility result.

**Symptom:** Sparky CA's roots appear in Debian Java but do not update the application's HTTPS trust.
Cause: PjeWebGlobal.HTTPS_CODEC loads /pjeoffice.jks directly from the application resource.
The actual store contains 168 trusted certificates, 80 ICP-Brasil subjects and one self-signed ICP root, v5; it has no key entries.
Its HTTPS codec rejects a generated local TLS chain even when javax.net.ssl.trustStore points at a store containing that generated root.
A private classpath resource union, containing every original certificate plus the generated root, is accepted by that same unchanged HTTPS codec.
All 168 original certificate encodings were compared and preserved.
This demonstrates an additive local resource bridge; it does not implement a product trust updater or prove Ed521 support.
A later integration must preserve original anchors and the person's selected system TLS trust, regenerate the union when either input changes, and report failures.
Document-signature policy remains a separate concern.

**Symptom:** startup or video output fails with InvalidPathException in a minimal container.
Cause: the C locale cannot encode non-ASCII characters in the built-in driver paths or output filenames.
The cause was found from the rejected path and a same-command UTF-8-locale rerun.
Use C.UTF-8 for disposable fixtures; preserve the person's UTF-8 locale in the product launcher.

**Symptom:** an HTTP request for a local PDF task is refused as an internal-only task.
Cause: the application separates remote requests from local file operations.
The supported ShellExtension entry point writes the normal watched local request instead and succeeds.
Do not bypass that boundary or expose local-file tasks over HTTP.

**Symptom:** the bundled JavaFX cannot load any of testing's codec libraries.
The loader trace and a successful private ABI-59 control established the cause.
Build private shared libraries from the signed FFmpeg 5.1.10 source, using the build repository's build-media-compat.sh fixture, and scope LD_LIBRARY_PATH to that application's process.
This supplies libavcodec.so.59/libavformat.so.59 and their private matching dependencies without replacing the system ABI 63 libraries or executable.
With that fixture, MediaProbe reports READY and 8000 ms; the actual cutter displays decoded video, accepts its normal cut events for 1–4 seconds and saves a 3.08-second H.264/AAC MP4 through system FFmpeg.
The output passes an independent full decode.
The fixture's mark events were posted through the existing public event classes; the visible save button and folder dialog were operated normally.
The null ALSA PCM is only for the isolated container's lack of an audio device; no host audio connection was used and physical audio output was not tested.
A later compatibility package needs normal source/licence/provenance and update maintenance; the scratch library build is not a shipped package.
