# The edition's apt repository

**For maintainers who add, sign and publish packages:** the development repository, the published one, its key, and how a change reaches https://repo.sparkyos.org.

The tools are in `sparky-os/repo/` of [the build tree](https://github.com/Sparky-OS/sparky-stereo-os-build/tree/main/sparky-os/repo).
Local paths, the server and the keys come from the local configuration, whose keys [build.conf.example](https://github.com/Sparky-OS/sparky-stereo-os-build/blob/main/sparky-os/config/build.conf.example) lists; the real file stays outside every repository.

## Development

- A flat repository on the maintainer's machine (`SPARKY_REPO_DIR`), origin `Sparky Stereo OS`, indexed by `make-repo.sh`. The development VM reads it as a `file:` source.
- Staged packages go in with `update-repo.sh STAGED...`.
  Each staged folder carries a `SHA256SUMS`, which is checked first.
  Superseded versions move to `SPARKY_REPO_SUPERSEDED`, source packages go to `source/`, and `make-repo.sh` reindexes; nothing already in the repository is overwritten.
- `carried/` holds unmodified packages we carry for a while, such as deb-multimedia's keyring. `source/` holds the source packages, indexed as `Sources`.
- The pin `sparky-os/apt/sparky-stereo` puts `o=Sparky Stereo OS` at 1001, the way Paweł pins `o=SparkyLinux`.
  The `sparky-stereo-apt` package is its one owner on an installed system, as `/etc/apt/preferences.d/sparky-stereo`; the development VM copies the same file.
  Edition-wide apt policy files sit in `sparky-os/apt/`.

## The repository sits on deb-multimedia

Our FFmpeg, and so everything that pulls `libavcodec63` (Qt Multimedia and Karton, for example), needs deb-multimedia's codec libraries: `libaom3 (>= 1:3.15.1)`, its x264, x265, dav1d and SVT-AV1.
An installed edition has them, because `sparky-stereo-apt` adds deb-multimedia's `forky` source.
A test image or rig that installs from our repository adds the same source too, with `ca-certificates` and deb-multimedia's keyring from `carried/`.
Measured on 2026-10-09 with Karton in a clean `debian:testing`: without the source, apt reports "libavcodec63 Depends libaom3 (>= 1:3.15.1) but none of the choices are installable"; with it, it resolves.
Such an image also needs the edition's pin at 1001, or apt takes deb-multimedia's FFmpeg instead of ours (2026-10-22).

## The published repository

Daniel, 2026-10-05: SparkyLinux's shape, with our names.

- `dists/mashtabba`, whose `Release` says `Origin: Sparky Stereo OS`, `Label: Sparky Stereo OS`, `Suite: testing` and `Codename: mashtabba`.
  Origin and Label are the distribution, the Codename is the edition's version tied to a Debian, and the Suite is its role.
- Component `main`, with `binary-amd64`, `binary-i386`, `binary-arm64`, `binary-all` and `source` (the live `Release`, checked 2026-10-23).
  `Release`, `InRelease` and `Release.gpg` are signed with the edition's own key.
- **A new Debian means a new codename of the same edition** (Sparky Stereo OS 10 on Debian 15, say), as SparkyLinux moves from one codename to the next.
  The old codename's Suite then becomes `stable`, and the new one is `testing`.
- Never reuse Paweł's key or codenames.
- Two packages, in the shape of `sparky-keyring` and `sparky-apt`:
  - `sparky-stereo-keyring` ships only the key, as `/etc/apt/trusted.gpg.d/sparky-stereo-repo.asc`.
  - `sparky-stereo-apt` ships `/etc/apt/sources.list.d/sparky-stereo.sources` (`Signed-By:` that key), deb-multimedia's source and the pin. It depends on `sparky-stereo-keyring` and on `sparky-apt`, so SparkyLinux's repository, key and pin come with it: we use their repository, and we never copy their key or files.
- Every published package has its source package (the `.dsc` and the files it names), so the repository offers `deb-src` as SparkyLinux's does and our changed GPL sources ship beside the binaries.
- The address follows SparkyLinux's naming, and the edition's own key signs the repository, so moving it to another server changes only the address in `sparky-stereo-apt`.

## The key

The repository's signing key exists since 2026-10-05: Ed25519, signing only, with no expiry, like SparkyLinux's own key.
Its fingerprint is `10DF D38D AD1E 4808 BC68 8E5A 945E 5D07 9A2A 0B9C`.
Its public part is `sparky-os/packages/sparky-stereo-keyring/sparky-stereo-repo.asc`, which that package's `build.sh` uses by default and the repository serves at its root.

- Never create another key: a second key, or a lost one, means every installed system needs a new keyring package by hand.
- Tests and proofs use a throwaway key, passed to the builds and to `publish-tree.sh`.
- The private part stays in its own GnuPG home, named by the local configuration (`SPARKY_REPO_GNUPG`); only the pipeline step that signs reads it.

## Publishing a change

1. **Build and stage** through the Lean Code pipeline ([the lc package contract](../../../docs/lean-code-packages.md)): provenance, then the projection, the final checksums and the archives, staged with a `SHA256SUMS`.
2. **Start from the live tree.** The base is the local copy whose `dists/mashtabba/InRelease` has the same SHA-256 as the server's (`curl -s https://repo.sparkyos.org/dists/mashtabba/InRelease | sha256sum`). If no local tree matches, stop: something was published after it.
3. **Copy it** and run `SPARKY_REPO_KEY=<fingerprint> SPARKY_REPO_GNUPGHOME=<home> publish-tree.sh SRC DEST` on the copy.
   It keeps unchanged pool files, removes versions that are no longer the newest, keeps recent by-hash files for clients in the middle of an update, and leaves the signed `Release` as it was when nothing changed.
4. **Prove the copy** (the `lean` package lives in `sparky-os/`). Every index lists what the pool holds; `gpgv` accepts `InRelease` and `Release.gpg`; `python3 -m lean.release check-repo DEST` passes; a container installs the changed packages from the copy and `python3 -m lean.release check-link` passes, with the previous build as the control; and a diff against the live tree touches only the changed packages and `dists/`.
5. **Dry run.** `sync-to-server.sh DEST` without `--go` lists what each step would send.
   It sends in an order that keeps the repository consistent while it changes: `pool/` first, then the by-hash files and the `Packages` indexes, then the key, the page, `Release`, `Release.gpg` and, last of all, `InRelease`, and only then the deletions.
6. **Send** with `--go`, after review, by the maintainer who holds the server's access.
   The server, its path and the access key come from the local configuration (`SPARKY_SYNC_HOST`, `SPARKY_SYNC_PATH`, `SPARKY_SYNC_SSH_KEY`), never from a repository.
7. **Check it online:** `sparky-os/release/verify-online-repository.py` compares the published tree with its signed local copy.
