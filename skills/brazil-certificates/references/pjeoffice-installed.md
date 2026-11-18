# PJeOffice Pro as the edition installs it (ORDER 18, milestone 2)

What `sparky-pjeoffice` and `sparky-pjeoffice-codec` do, how each part was proved, and the traps met while building them.
The measurements of the unchanged program (Java, tray, updater, trust store, tokens) are in [pjeoffice-runtime.md](pjeoffice-runtime.md); this page is the installed integration.
Read the packaging side too: [a program fetched on the person's machine](../../edition-packaging/references/a-program-fetched-on-the-persons-machine.md).

## What is installed and where

- `sparky-pjeoffice` holds only our code: `/usr/bin/sparky-pjeoffice` (install, remove, rollback, trust, status, check, sign-pdf, launch), `/usr/bin/pjeoffice-pro` (the launcher), `/usr/bin/sparky-pjeoffice-tray` (a KStatusNotifierItem), the System Settings page (`kcm_sparkystereo_pjeoffice`), a menu entry, the tray's autostart entry, a Dolphin service menu for PDFs and the reviewed `catalogue.json` (version, address, size, SHA-256).
  The package's control file declares the install-time download (`Sparky-Install-Download-Size` 167505940, `-Source` the ZIP's address), so apt and Stereo APTus say it first.
- The official ZIP is fetched by the package's setup from CNJ's own address, verified against the catalogue, unpacked to `/opt/pjeoffice-pro/versions/VERSION` and switched in by renaming a symbolic link (`/opt/pjeoffice-pro/current`) over the old one.
  The previous version stays beside it; `sparky-pjeoffice rollback` goes back.
  Inside the installed copy one file changes: `pjeoffice-update.properties` gets `update.url=disabled` (CNJ's own updater cannot patch a root-owned folder; the original is kept as `.cnj`, and `SHA256SUMS.cnj` lists every file as CNJ shipped it).
- The launcher starts the bundled Java 8 from the resolved version folder with `-cp TRUSTDIR:pjeoffice-pro.jar` and `-Dffmpeg_home=/var/lib/sparky-pjeoffice/ffmpeg` (a folder whose `ffmpeg.exe` is a link to the system's FFmpeg).
  `LD_LIBRARY_PATH` carries `/usr/lib/sparky-pjeoffice/codec` for that process only.
- `sparky-pjeoffice-codec` is FFmpeg 5.1.10 unmodified (signed release), shared libraries with only the decode paths JavaFX Media plays, so the cutter finds `libavcodec.so.59`.

## The proofs (all in disposable containers, generated identities, the real 2.5.16u fetched from CNJ by the package)

1. **Installed by apt from the built packages:** `apt-get install sparky-pjeoffice` fetches 167505940 bytes, checks them, unpacks 355 MB, makes the certificate list (168 original certificates and 91 of the system's), switches. `sparky-pjeoffice status` reports it.
2. **The transaction with generated stand-ins for the ZIP** (`tests/installer.sh`, 48 checks, a local HTTPS server and a generated authority trusted by the container): a wrong digest is refused and deleted; an interrupted download keeps its `.part` and the next run resumes it (the Portuguese line "Retomando um download anterior" shows the language lookup); an update keeps the previous folder; a version that fails its checks leaves the one in use in use (exit 10); a failed switch restores the folder it replaced; a changed system certificate list is merged (and an unreadable one is told, then cleared); removal leaves the person's files.
   Red controls (`tests/mutations.sh`): each rule broken in a copy makes its test fail (no verification, no restore, a merge that drops the originals, no previous version, a watcher that fetches once, a launcher without its lock).
3. **Both signing backends through the package's own command** (`tests/rig/signing.sh`): `sparky-pjeoffice sign-pdf` (the Dolphin action's command) with a generated PKCS#12 identity, then with the same identity in SoftHSM through its own module (`list.a3=/usr/lib/softhsm/libsofthsm2.so`); each CAdES file verified outside the program with OpenSSL (chain to the generated root, content equal to the PDF, signed attributes present, an altered content refused).
   A login challenge through the program's developer entry point (`LocalTestMain`) to a local backend, its PkiPath chain and raw signature verified the same way.
4. **The cutter** (`tests/rig/cutter.sh`): JavaFX Media without the private libraries cannot create the player (`MediaException: Could not create player!`); with them it is READY and its clock advances; the program's own cutter opens, its "Salvar todos os cortes..." writes a 3-second H.264/AAC file that an independent full decode accepts.
5. **A Plasma login** (`tests/rig/plasma.sh`, KWin's virtual backend, no device): the package's autostart starts the tray and the signer; the session's host lists our `StatusNotifierItem`; the System Settings page and the Dolphin menu are captured, in English and Portuguese.

## Traps

- **Symptom:** the installer's certificate step fails on the real ZIP ("the key store digest does not match") although the generated stand-in passed.
  **Cause:** `pjeoffice.jks` inside the jar is a PKCS#12 store (DER, `30 83 ...`), not the JKS format its name suggests; Java 8's loader reads both, a hand-written JKS reader does not. The stand-in was written by the same wrong writer, so the test agreed with the bug.
  **Fix:** merge with the program's own Java: `jre/bin/jjs` (Nashorn, in every Java 8 JRE) runs a short script (`merge-trust.js`) that loads the store with its detected type, adds the system's certificates, writes the same type, reads it back and checks every original's DER encoding. The test reads the result with `keytool`, a second reader.
  **Found by:** installing the real ZIP, then the first bytes of the resource.
- **Symptom:** two signers at login, the first one silently gone ("Tentativa de shutdown da porta 8800", "Porta 8800 já está sendo utilizada" in the log).
  **Cause:** the tray's autostart and the menu entry both started the program; a second instance shuts the first down.
  **Fix:** the launcher checks and starts under one `flock` and waits until the signer answers, so the second start finds it answering (`tests/rig/twostarts.sh`: one process; red without the lock: two).
- **Symptom:** the signer dies at start with `InvalidPathException: Malformed input or input contains unmappable characters: /usr/lib/opensc/opensc?pkcs11.so`.
  **Cause:** the program's own driver list holds an en dash; a Java whose locale is not UTF-8 cannot map it. The cause includes a `LANG` that names a locale the system has not generated (a container, a fresh account), which `locale charmap` shows as ANSI.
  **Fix:** the launcher runs the program with `LC_ALL=C.UTF-8` when `locale charmap` is not UTF-8, and writes that line in the program's log.
- **Symptom:** the page of a System Settings module shows English although its catalogue is installed and the session is in Portuguese.
  **Cause:** QML's `i18n` reads the catalogue named like the plugin (`kcm_sparkystereo_pjeoffice`), not the program's domain; the tray (C++) reads `sparky-pjeoffice`. In a C locale `LANGUAGE` does not reach it either: generate the locale (`locales` package, `locale-gen`) before judging.
  **Fix:** ship the same strings under both names.
- **Symptom:** the Java dialogs ignore `xdotool windowfocus` in a bare Xvfb ("Informe a senha" stays empty).
  **Cause:** no window manager hands out the focus; typing goes nowhere.
  **Fix:** move the pointer into the field (about 62 % down the dialog), click, type the generated PIN, press Return; "Autorização de site" is answered by clicking "Sim desta vez" (13 % across, 85 % down). `tests/rig/drive.py` writes a picture of every dialog it answers and a list of window names when a new one appears, so an unknown dialog is found, not guessed.
- **Symptom:** the person's session cannot read KWin's output buffer, `/proc/PID/environ` is refused even for root.
  **Cause:** KWin has file capabilities; reading another user's process needs `CAP_SYS_PTRACE`, which a container drops.
  **Fix:** run the session as the person and the capture as root with `--cap-add SYS_PTRACE`, on request through a file (`plasma.sh`, `capture-daemon.sh`).
- **Symptom:** the program's JavaFX probe hung once without an error on the first start after Xvfb (no READY in 60 s); five later runs passed. The cause was not found.
- **Symptom:** CNJ's ZIP unpacks with every file mode 0, so nothing runs. **Fix:** directories 0755, files 0644, and 0755 for `jre/bin/*`, `ffmpeg.exe` and `pjeoffice-pro.sh` (what CNJ's own script does with `chmod`).
- **Symptom:** the accepted milestone 1 report printed FFmpeg 5.1.10's SHA-256 as `7b2a6630...`; the recipe that pinned it stopped. **Cause:** the prose digest was wrong; the milestone's own evidence file holds `392306d6fc45dab0e9e0ea55381e071842e83a2fb31d320aeda40477a7766293`, which is today's file and carries a valid signature of release key `FCF986EA15E6E293A5644F10B4322F04D67658D8`. **Rule:** pin from the evidence and the fetch, never from a report's prose.

## Facts about CNJ's server, for the letter

The ZIP's response carries `x-amz-meta-sha256` equal to its SHA-256 (it is S3 object metadata): the digest CNJ's own server states, which the milestone 1 study had not seen. The server answers `Accept-Ranges: bytes` (a partial download resumes) and plain `curl` is served (no pinned user agent needed).
It is a fact for the reviewer, never a trust anchor: the catalogue's digest is the reviewed one.
