# A vendor-signed download entry

**For app center maintainers:** establish the vendor's trust anchor and verify its release before connecting the entry to installation.
Read with [edition-packaging](../SKILL.md).

Check freshness first: the release checks below were measured on 2026-11-18 against OpenLogi v0.9.0.
The application entry, metered notice and package qualification remain separate acceptance checks.

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

## Entry acceptance requirements

These are requirements, not claims of an implemented or tested app center entry.
Use the app center's existing entry-tools owner for minisign and the shared sparky-stereo-apt install-downloads reader for size and metered notices.
Do not add minisign to the app center package's dependencies.
Refuse an unsupported architecture before downloading.
Say a network failure, wrong checksum, rejected signature, missing tool or busy apt in the person's language.
Test the authentic release, a tampered copy, a wrong key, network disabled and an architecture without an asset.
For every refusal, inspect the installed package state and dpkg log; an error exit alone does not prove that nothing was installed.

## Trap: the app center clone has no stereo directory

**Symptom:** checking out `origin/master` from a local clone loses the `stereo/` directory.
**Cause:** cloning a source whose HEAD is detached copies its local `master`, which can trail its remote-tracking `origin/master`.
**Fix:** inspect the source's branch and remote-tracking commits, then explicitly fetch the intended fork commit before creating the work branch.
**How found:** the local `master` was `bc0f0fe`, while the fork's remote-tracking master and checked-out source were `b4b9dec`.
The corrected clone contained `stereo/VERSION` 0.1.16.
