# A vendor-signed download entry

**For app center maintainers:** establish the vendor's trust anchor and verify its release before connecting the entry to installation.
Read with [edition-packaging](../SKILL.md).

Check freshness first: the release checks below were measured on 2026-11-18 against OpenLogi v0.9.0.
The signed-deb entry and its shared notices were implemented and tested in the app center 0.1.18 candidate. Recheck release assets and the fork master before updating it.

## Reconcile before implementing

1. Read the vendor's release API and record the tag, asset names, byte sizes and digests.
2. Check out the exact release commit and locate the public key in that source.
3. Download each supported architecture's package, detached signature and checksum manifest from the vendor's own release.
4. Verify both the signature and the exact file's checksum entry before invoking apt.
5. Read the package's control fields, file list and maintainer scripts; simulate its installation against the edition's published pins.
6. Keep the vendor's application out of the edition's source and packages when its unmodified release serves the task.

## OpenLogi trust anchor

The release is [v0.9.0](https://github.com/AprilNEA/OpenLogi/releases/tag/v0.9.0), commit `a5b507ec8802e0ecb7ef3de61ce7868609c9b533`.
The key comes from [packaging/linux/install.sh, line 12](https://github.com/AprilNEA/OpenLogi/blob/a5b507ec8802e0ecb7ef3de61ce7868609c9b533/packaging/linux/install.sh#L12):

```text
RWRRkFtw+rqkvTlCTGKUszSE5dX9CK1teaQD45jO4P9rYlWLO4/nHVUF
```

The amd64 Debian package is 21,742,764 bytes, SHA-256 `a53d485ba25db1dc71c3d49f82eee0ce9ba8b449f05a50f110895b310ef2cefb`.
The arm64 Debian package is 19,002,416 bytes, SHA-256 `5cc68f026bcf7791dc459399212017b1769c3b5e681f96561a6450d9f217248c`.
Each has a same-name `.minisig` and a `SHA256SUMS` entry.
Both passed the following commands in Debian testing:

```sh
minisign -Vm openlogi-v0.9.0-linux-amd64.deb -P RWRRkFtw+rqkvTlCTGKUszSE5dX9CK1teaQD45jO4P9rYlWLO4/nHVUF
grep '  openlogi-v0.9.0-linux-amd64.deb$' SHA256SUMS | sha256sum -c -
```

The first prints `Signature and comment signature verified`; the second prints the file name followed by `OK`.
Repeat for arm64.
An entry must additionally enforce exactly one matching manifest record and pin the expected digest; a loose substring match is insufficient.
The package installs through apt and removes through ordinary package management.
Its post-installation script reloads udev rules when `udevadm` exists and prints the command for enabling its user agent; it does not enable the agent itself.

## The implemented owner and order

The app center's `stereo/signeddeb.py` owns authentication; `tools.py` owns apt-authenticated verifier staging and installation; `mainpages.py` uses the shared `sparky-stereo-apt` install-downloads reader.
The OpenLogi entry lives under Accessories, Devices, beside the mouse and keyboard tools.
The package recipe copies the new module; it gains no minisign dependency.

1. Select `dpkg --print-architecture` from the entry's explicit asset map. Refuse an unsupported architecture before planning tools or downloading.
2. Show the selected package size plus its 326-byte signature and missing entry-tool download size, with the shared metered notice, before the install button.
3. Check the actual apt frontend and dpkg locks before starting the action.
4. Fetch only HTTPS, including redirects, with bounded curl timeouts. Compare the package's exact byte size and pinned SHA-256.
5. Invoke minisign with the pinned public key and detached signature. Refuse a rejected signature with a localized sentence.
6. Only after authentication, let the existing tools owner install minisign if needed, then use `apt-get --no-remove --no-install-recommends --no-allow-unauthenticated install PATH`.
7. Remove with ordinary `apt-get remove openlogi`; do not create a separate uninstall path.

When minisign is absent, `tools.staged_command` downloads its apt-authenticated dependency closure into the standard apt cache, extracts the exact planned package versions and native/all architectures into a private temporary directory, and invokes that verifier with its extracted libraries.
It does not run maintainer scripts or install those packages before vendor authentication.
The normal tools installation then reuses the apt cache; it does not download them twice.
An entry that fails verification must leave both `dpkg-query` state and `dpkg.log` unchanged, including when the verifier was initially absent.
Do not replace apt's authenticated archive owner with a second downloader for Debian dependencies.

## Tests and build qualification

In the app center source, run `python3 stereo/tests/signed-deb.py` inside the edition's test container with `OPENLOGI_FIXTURE_DIR` pointing to a directory containing the named release `.deb` and `.deb.minisig`.
Vendor fixtures stay outside the repository.
The suite covers the authentic file, a tampered file, a newly generated wrong key, failed network, an unsupported architecture, ten-language entry metadata, a real frontend lock in a fresh process, the shared size/metered notice and unsupported-architecture page rendering.
Expected: nine tests pass; removing the signed-deb owner fails the old-tree run and omitting native apt initialization fails the lock regression.

Also test the installed candidate: upgrade from the previous package adds no dependencies; rejected digest/key and actual `--network none` leave package state and dpkg log unchanged; authentic installation and ordinary apt removal succeed.
Use a private umockdev sysfs when exercising the vendor's udev reload/trigger maintainer script; never let a test trigger the host's devices.
Build both lc1 and HR packages from a committed recipe with the complete build record, rebuild the `.dsc`, compare both packages byte for byte, and compare every payload/control file with the previous package before the frozen-universe link/start gate.
No vendor application, signature, fixture or brand asset belongs in the edition's source package or stage.

## Trap: a real apt lock is missed

**Symptom:** the app center proceeds while `/var/lib/dpkg/lock-frontend` is actually held, although its configured-path lock unit test passes.
**Cause:** in a fresh Python process, `apt_pkg.init_config()` leaves `Dir::State::status` empty. Deriving native dpkg lock paths from it finds the wrong directory.
**Fix:** call `apt_pkg.init_system()` after `init_config()`, then derive the native paths; preserve explicit configured-path support.
**How found:** a separate process held the actual frontend lock while an installed entry was invoked. The old code missed it; inspecting apt's configuration before and after `init_system()` identified the empty status path. The fresh-process regression fails before the fix and passes after it.

## Trap: the app center clone has no stereo directory

**Symptom:** checking out `origin/master` from a local clone loses the `stereo/` directory.
**Cause:** cloning a source whose HEAD is detached copies its local `master`, which can trail its remote-tracking `origin/master`.
**Fix:** inspect the source's branch and remote-tracking commits, then explicitly fetch the intended fork commit before creating the work branch.
**How found:** the local `master` was `bc0f0fe`, while the fork's remote-tracking master and checked-out source were `b4b9dec`.
The corrected clone contained `stereo/VERSION` 0.1.16.
