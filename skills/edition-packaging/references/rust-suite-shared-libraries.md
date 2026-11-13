# A Rust suite as shared libraries

Learned on storytold's Craft suite in November 2026 (PhotoCraft 0.23.1 and LightCraft 0.21.1, Rust 1.99.1): about twenty Rust applications that share most of their dependencies and each ship as one or two statically linked programs.
Daniel asked for the suite "the debian way - shared libraries", so the code the apps have in common is installed once.
This page is the recipe that worked on two apps, with its numbers, and every trap met on the way.
It began as a proof on two apps in test packages; [the suite as a source package](#the-suite-as-a-source-package) is the real recipe on three apps, through the Lean Code gates, with the edition's own Rust toolchain.

## What Rust allows, in four facts

1. **Rust has no stable ABI.**
   The Debian Rust team's policy says so and draws the consequence for Debian: "At the time of writing, Rust does not have a stable ABI. So, we can't reasonably ship compiled versions of Rust libraries", and "library packages ship source code, and application packages build all the library crates they use from source" ([Debian Rust packaging policy](https://wiki.debian.org/Teams/RustPackaging/Policy), read 2026-11-12).
   Debian's `librust-*-dev` packages are source, and Debian's `libstd-rust-1.97` holds only the compiler's own `librustc_driver`; no package puts the standard library where a program can load it.
2. **A Rust dynamic library exists (`crate-type = ["dylib"]`) and loads only with the exact compiler and the exact dependency resolution that built it.**
   So every package of one release is built by one compiler in one build, and the library's name must say which build it is.
3. **A crate may appear once in a program** ([Rust reference, linkage](https://doc.rust-lang.org/reference/linkage.html)): "if dynamic libraries B and C were each statically linked to library A, then a crate could not link to B and C together because there would be two copies of A".
   Shared libraries therefore form layers, and each crate lives in exactly one of them.
4. **Cargo builds a crate once per resolve.**
   Two apps built in two workspaces never share a compiled crate, even at the same version: features and the versions of what the crate depends on enter its identity.
   Sharing needs one workspace, one `Cargo.lock`, one `cargo build` for all the apps.

## Recipe

The scripts of this first proof are in this skill's [`scripts/`](../scripts) folder; the generator the source package uses, which also pins sibling checkouts and closes the libraries' lists, is in the build tree's recipe ([the suite as a source package](#the-suite-as-a-source-package)).

1. **Make one workspace out of the apps' checkouts**, without changing upstream's files:
   `scripts/rust-suite-tree.py tree OUT photocraft=SRC/photocraft:photocraft,photocraft-cli lightcraft=SRC/lightcraft:lightcraft,lightcraft-cli`.
   It copies each checkout to `OUT/<app>`, expands every `workspace = true` in the member manifests from that app's own root manifest (so two apps may pin one dependency differently), drops dev-dependencies and lints, and writes `OUT/Cargo.toml` (the members, the union of the `[patch]` tables, the release profile) and `OUT/Cargo.lock` (the union of upstream's locks, one version per compatible range).
   Expect a line such as `59 members, 1086 locked packages`.
2. **List what each program really links**: `scripts/rust-suite-trees.sh OUT OUT/trees FEATURES BIN...` (run it before the generated crates exist) runs `cargo tree -e normal --target x86_64-unknown-linux-gnu --prefix depth -f '{p}|{f}'` once per program and once for all of them, then `cargo metadata --format-version 1 --filter-platform x86_64-unknown-linux-gnu --features FEATURES > OUT/metadata.json`.
3. **Generate the libraries**: `SUITE_ABI_SEED="$(rustc -vV)" PER_APP=1 scripts/rust-suite-tree.py shared OUT OUT/metadata.json OUT/trees photocraft,photocraft-cli lightcraft,lightcraft-cli`.
   It writes one generated crate `OUT/shared` (`craft-suite-shared`, `crate-type = ["dylib"]`) that depends on every library crate two or more apps link, each pinned to the resolved version, source and feature list, with one `extern crate` line per crate.
   With `PER_APP=1` it writes one more per app (`photocraft-shared`): what two or more programs of that app link and no other app does, the app's own crates included.
   Each program's package gains the dependency and its `main.rs` gains `extern crate craft_suite_shared;` (and the app's own library): without that line the compiler never loads the library and links everything statically again.
   Each generated crate has a `build.rs` that prints `cargo::rustc-link-arg=-Wl,-soname,libcraft-suite-shared-0.<id>.so`, where `<id>` is a hash of the compiler's `rustc -vV` and of every crate, version, source and feature in the library.
4. **Build everything in one run, link-time optimisation off**: `cargo build --release -p photocraft -p photocraft-cli -p lightcraft -p lightcraft-cli --features photocraft/heif,... --bins`.
   Check: `readelf -d target/release/photocraft | grep NEEDED` names the app's library, the suite's library and `libstd-<hash>.so`.
5. **Package** the files under their SONAME: the suite's library in `libcraft-suite-shared-0.<id>` (the package name carries the ABI, like `libllvm22` or `libstd-rust-1.97`), each app's own library inside the app's package, the standard library in a package of the edition's own Rust toolchain whose name carries its hash.
   Each library package ships a `shlibs` file with an exact dependency (`libcraft-suite-shared 0.<id> libcraft-suite-shared-0.<id> (= VERSION)`), so `dpkg-shlibdeps` writes the apps' `Depends`; give it `-x<package>` for the app's own library and add the libraries the programs open at run time (Wayland, X11, xkbcommon, Vulkan or EGL) by hand, as upstream's own package does.
   Nothing builds against these libraries outside the suite's own source package, so there is no `-dev` package.
6. **Prove it installed**, in a clean container: apt installs the packages; each program's output file equals the static build's byte for byte; each window maps under a headless X server; `LD_BIND_NOW=1 PROGRAM --version` exits 0 and `ldd -r` shows no undefined symbol; with the library removed by force the program exits 127 and names it.
   Then the upgrade: release 1 installed, one app of release 2 installed alone (apt brings the new library beside the old one and the other app keeps working), then the rest, then `apt-get autoremove` takes the old library.

## The numbers of the proof (two apps, four programs, stripped, x86-64)

| Build | Installed bytes | Against static |
|---|---|---|
| Static, as upstream builds | 330,651,472 | |
| One library for what both apps link (313 crates) | 282,707,912 | 14.5 % less |
| That, plus one library per app (144 and 131 crates) | 203,129,144 | 38.6 % less |
| Every program inside one library with a C interface (`cdylib`), four 14 kB launchers | 159,099,952 | 51.9 % less |

The one-library shape is smaller because the linker keeps only what the programs reach and shares the generic code too, but it is one package: installing one app installs every app's code, and any app's update replaces all of it.
A Rust dynamic library keeps every public item of every crate in it, used or not, and generic code is still compiled into each user.
Starting a program costs 4 to 6 ms static and 12 to 19 ms with the libraries (the loader binds the symbols); a filter chain, a WebP encode and a raw render took the same time within the machine's noise (0 to 7 %, load average 4 to 8).

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: `error: failed to select a version for arboard ... all possible versions conflict with previously selected packages` on the merged lock.
  Cause: the union of two lock files holds two versions of one compatible range (3.6.1 and 3.7.0) and locked edges to both; one resolve holds one.
  Fix: keep the highest version of each compatible range and leave the edges out, cargo writes them again; then compare the result with each upstream lock (here 13 and 11 crates moved, all within their ranges or to a version the other app already used).
  Found by: the resolver's own message, which names both requirements.
- Symptom: `error[E0050]: method on_exit has 1 parameter but the declaration in trait eframe::App::on_exit has 2`.
  Cause: Cargo features are meant to add, but this one changes a signature: one app enables eframe's `glow` feature, the other does not, and one resolve gives both the feature.
  Fix: a one-line patch in the copy of the app that lacked the feature (`fn on_exit(&mut self, _gl: Option<&eframe::glow::Context>)`); never by switching the feature off, which would take a renderer from the other app.
  Found by: the compiler's note prints the trait's signature with the feature on.
- Symptom: `error: objc2 only works on Apple platforms` once the generated crate exists.
  Cause: the graph in `cargo metadata` over-states features (it does not run the per-target feature resolver), so the generated crate asked for features only macOS turns on.
  Fix: take crates and features from `cargo tree --target`, which runs the real resolver.
  Found by: `grep objc` in the generated crate list, then comparing its size with the tree's (380 crates against 313).
- Symptom: the shared library carries `syn`, `quote` and `proc-macro2` for nothing.
  Cause: a flat `cargo tree -e normal` listing includes what procedural macros use, which runs in the compiler.
  Fix: read the tree with depths and never walk into a `(proc-macro)` node.
  Found by: the per-crate size listing of the library.
- Symptom: `error[E0463]: can't find crate for craft_suite_shared`, although the generator said it added the dependency.
  Cause: the generator tested for the dependency with a plain substring, and the build folder's own path contained the crate's name.
  Fix: test for the manifest line (`\ncraft-suite-shared = `).
  Found by: `grep -n '^craft-suite-shared' */apps/*/Cargo.toml` printed nothing.
- Symptom: `dpkg-shlibdeps` cannot give a dependency for `libcraft_suite_shared.so`.
  Cause: rustc names a dylib after its crate, with no version, and dpkg reads a version only from `NAME.so.VERSION` or `NAME-VERSION.so` with a digit first.
  Fix: the generated `build.rs` sets the SONAME with a link argument (the last `-soname` wins), and the package installs the file under that name; no `patchelf`.
  Found by: reading how `Dpkg::Shlibs` splits a SONAME, then `readelf -d` on the result.
- Symptom: the same `dpkg-shlibdeps` run makes an app depend on itself.
  Cause: the app's own library is in the app's package and has a `shlibs` line.
  Fix: `dpkg-shlibdeps -x<package>`, as debhelper does.
- Symptom: with thin link-time optimisation in the profile the dynamic build cannot link.
  Cause: rustc refuses dynamic linking together with link-time optimisation.
  Fix: `lto = false` in the suite's profile (the generator writes it); the static build it is compared with used upstream's profile.
- A container name still in use stops the next build at once (`Conflict. The container name ... is already in use`) while the failed one is "waiting for other jobs to finish": wait for it to leave before starting again, and copy a log before the next run truncates it.

## What decides the design

- **One source package for the suite.**
  One resolve and one build mean one source package (each app's source as a component) that produces every binary package; a release of any app is a new build of that source.
- **The library's name is its ABI.**
  The id must cover the compiler, every crate version, source and feature, and any patch the edition applies to a crate (hash the patched source, not only its version); the same id then means the same library, and an app's dependency on it is exact.
  A new id is a new package beside the old one, so an upgrade never leaves an app without its library.
- **A compiler update rebuilds everything**, in order: the toolchain, then the suite.
  The standard library's file name changes with the compiler, so the dependency itself forces the order.
- **What upstream could change to make it cheaper** (a separate offer, never a condition of our build): one craft-libs revision for all apps of a release (here the two apps pinned five different revisions, so only one craft-libs crate was shared), features that only add, and the fonts and translations loaded from a shared folder (each program of upstream's PhotoCraft release is 46 to 53 MB larger than the same program built without them).

## The edition's Rust toolchain

Learned in November 2026 on rustc 1.98.1 and 1.99.1.
Rust's dynamic libraries load only with the compiler that built them, so the suite needs one pinned compiler, and the edition builds it from source: Debian's `rustc` source package as Debian has it, plus one binary package, through Lean Code.
The recipe is `sparky-os/packages/rustc` in the [build tree](https://github.com/Sparky-OS/sparky-stereo-os-build); its README has the commands.

### Recipe

1. **Look in Debian's archive first.** `https://api.ftp-master.debian.org/madison?package=rustc&f=json&a=source` lists every suite; on 2026-11-12 testing had 1.97.1, unstable 1.98.1 and experimental 1.99.1, so both links of the chain were Debian's own source packages, fetched with `apt-get source --download-only rustc=VERSION` (deb-src lines for unstable and experimental, apt checks them against the signed archive).
2. **The chain, no downloaded compiler.** Debian's `README.source`: "The system rustc has to be either the previous or the same version as the rustc being built". The first link is built by Debian testing's compiler, the next by ours: `build.sh versions/1.98.1.env WORK SRC`, then `build.sh versions/1.99.1.env WORK2 SRC2 WORK/out`.
   The versions file names the seed (`SEED_VERSION`), and the build stops when apt offers another compiler.
   The dependencies are installed in one container with the network, the result is committed as an image, and the compile runs from that image with `--network none`.
3. **The runtime package.** Debian's rules delete the standard library's shared object (`rm .../rustlib/$(DEB_HOST_RUST_TYPE)/lib/libstd-*.so`), and Debian's rustc then answers `-C prefer-dynamic` with a statically linked program and exit 0.
   The recipe moves the file into the public library folder, in a package named `libstd-rust-HASH` after the 16 hex digits of the file's name (Debian Policy 8.1: "The run-time shared library must be placed in a package whose name changes whenever the SONAME of the shared library changes"), with a link left in the sysroot and a dependency from `libstd-rust-dev`.
4. **The first build of a version finds the hash.** `STD_HASH=discover` compiles, stops at the install step with the library's real name, makes the source package again and packages the compiled tree with `dpkg-buildpackage -nc`; then record `STD_HASH=...` in the versions file.
5. **Lean Code.** `lean.debian_prepare` with a preserve plan: only `compiler/rustc_llvm`'s seven C++ files are native inputs of the build; `rust-src` stays as authored in the package stage.
6. **Gates and proof.** `lean.release check-debs` on the archives (it writes the build record), `check-link` on the finished packages, then in a clean container: `rustc -C prefer-dynamic` gives a program whose `NEEDED` names exactly `libstd-HASH.so`, it starts without `LD_LIBRARY_PATH`, `dpkg-shlibdeps` writes `libstd-rust-HASH (= VERSION)`, and with the package removed by force it exits 127 and names the file.

### Measured (four CPUs, a busy machine)

- rustc 1.98.1 built by Debian's 1.97.1: the compile 2 h 01 min with Debian's settings (stage 2, debug information level 2, documentation, the wasm32 and bpf standard libraries, tests not run); the dependencies step 4 min; one packaging pass 36 min.
- rustc 1.99.1 built by our 1.98.1: the compile 1 h 54 min, the packaging pass 44 min, 2 h 42 min in all.
- The build tree: 39 GB each; the 28 archives 966 MB and 887 MB, of which about 600 MB are debug symbols.
- `libstd-rust-HASH`: 0.6 to 0.7 MB as an archive, 1,586 and 1,627 KiB installed; its symbols file lists 1,825 symbols and `dpkg-shlibdeps` prints no symbol warning.
- The source packages: three runs under three clocks, zones, umasks and checkout times give the same sums, equal to the built source's, when `SOURCE_DATE_EPOCH` is the build's; recording the hash is a commit in the recipe's folder, so the recipe's own date moves after it.
- A compiler update with apt: the new toolchain installs `libstd-rust-NEWHASH` beside the old one, the suite built by the old compiler keeps starting, `autoremove` does not take the old runtime package while the suite depends on it, and takes it (with the old suite library and `libstd-rust-1.98`) once the rebuilt suite is installed.

### Traps: the symptom, the cause, the fix, how it was found

- Symptom: `lean.debian_prepare` says "Not a conventional dh rules file; integrate its builder explicitly".
  Cause: Debian's rules call `$(SYSTEM_WORKAROUNDS) dh $@`, and the check wanted `dh` first on its line.
  Fix: since toolkit 0.1.29 the check accepts one make variable before `dh`.
  Found by: the message, then the rules file's `%:` target.
- Symptom: the build stops at once with "Source preservation pattern matches no eligible file: src/doc/*".
  Cause: the preserve plan was written from a count with more extensions than the source walker reads.
  Fix: list the files with the walker's own rule (`.h .hh .hpp .hxx .c .cc .cpp .cxx .inl .S .sx`, folders named `build` and `debian` skipped) before writing a pattern; here 172 files, 7 of them the compiler's.
  Found by: the message names the pattern.
- Symptom: a program's package has no dependency on the standard library's package, and `dpkg-shlibdeps` prints "cannot extract name and version from library name 'libstd-fee3606a4e1e729c.so'".
  Cause: from a `shlibs` file dpkg reads a version out of a SONAME only as `NAME.so.VERSION` or `NAME-VERSION.so` with a digit first; a hash that starts with a letter gives a warning and no dependency.
  Fix: a `symbols` file, which is matched by the SONAME as it is, with the exact dependency as its template; `dpkg-gensymbols` writes the symbol list, so no "found in none of the libraries" warning is left.
  Found by: a toy library built twice, with a SONAME hash that starts with a letter and one that starts with a digit.
- Symptom: the package stage stops with `lean.package.Invalid: /usr/src/rustc-1.98.1/src/tools/rustc-perf/.../bench-branches.py: check failed: the authored file does not parse: Missing parentheses in call to 'print'`.
  Cause: `rust-src` ships the whole compiler source, benchmark inputs included, and one of them is a Python 2 script.
  Fix: `rust-src` is source for other builds (cargo checks `library/vendor` against `.cargo-checksum.json`, rust-analyzer and `-Zbuild-std` read it), so its payload is kept byte for byte through the toolkit's preservation plan, with the reason in the lc1 manifest.
  Found by: the message names the file.
- Symptom: a second packaging pass stops with "already marked; use a fresh staging tree, never project MR again".
  Cause: the first pass had sealed the staging trees of the packages it finished.
  Fix: before `dpkg-buildpackage -nc`, remove every package's `debian/PACKAGE` and `debian/.debhelper/PACKAGE`, `debian/files`, `debian/tmp` and the install stamp; the compiled tree stays.
  Found by: the message; 24 archives had been written before the first pass failed.
- Symptom: the changelog of the same recipe commit names another seed compiler a week later.
  Cause: the text came from `apt-cache policy rustc` in the build container.
  Fix: the versions file names the seed, and the dependencies step checks apt against it.
  Found by: reading the source step while preparing the reproducible-source proof.
- Symptom: `cargo build` of the generated workspace says `failed to read .../suite-198/lightcraft/crates/catalog/Cargo.toml`.
  Cause: the generated library crates name their member crates by the absolute path of the folder they were generated in, and the build mounted the tree at another path.
  Fix: generate the tree at the path it is built at.
  Found by: the path in the message is the generation folder.
- Symptom: lean tests fail in a container with `git show ...` exit 128 and a failed `gpg --quick-generate-key`.
  Cause: the tree was a git worktree whose repository was not mounted, and the scratch path made gpg-agent's socket longer than 108 bytes.
  Fix: mount the folder that holds the repository at its own path, and give the tests a short `HOME` and `TMPDIR`.
  Found by: the two commands in the failure output; both pass on a plain clone.

## The suite as a source package

Learned on 2026-11-13 on three apps of the suite at their stereo edition branches (PhotoCraft 0.20.1, LightCraft 0.21.0, FilmCraft 0.17.0), built by the edition's rustc 1.99.1.
The recipe is `sparky-os/packages/craft-suite` in the [build tree](https://github.com/Sparky-OS/sparky-stereo-os-build); its scripts are named below.
It is one source package, `craft-suite`, whose build has no network: every crate, font and catalogue is in the original archive.

### Recipe

1. **Pin everything in one file** (`suite.json`): each app's repository revision, version, programs, features, the revision of each sibling checkout it builds against, and the font and catalogue revisions its gates ran with; the compiler's package version and its runtime package; which apps are built and why the others wait.
2. **Fetch and vendor, the only step with the network** (`fetch.sh OUT`): `git archive` of each pinned revision, the author names of each app's commits, then per app a copy with its sibling path dependencies rewritten to git dependencies on the pinned revision (`suite-source.py rewrite`, then `lock`), `cargo vendor --locked --versioned-dirs`, and `suite-source.py merge`, which sorts the vendored crates into `vendor/registry` and `vendor/git/<repository>-<revision>`, one folder per source.
   Expect a line per folder; here 1,243 registry crates and 15 git folders, 1.5 GB, and the lock of each app unchanged by cargo after the rewrite.
3. **Make the two source packages in the build container** (`build.sh WORK SOURCES SEED deps`): the original archive holds `apps/`, `vendor/`, `fonts/` and `i18n/`; `debian/` holds the generators, and `suite-generate.sh` is run once there with the build's compiler to learn the libraries' names, which go into `debian/control`, `debian/suite-sonames.txt` and the pinned `debian/suite-Cargo.lock`.
   `lean.debian_prepare` then makes the `+lc1` source, with `["c", "rust"]` as its languages.
4. **Build without network** (`build.sh WORK SOURCES SEED build`, or `all`): the rules project the tree, bind the vendored checksum manifests to the projection, generate the workspace, stop unless the libraries' names equal the source's, and build (`suite-build.sh`).
   Expect `the libraries' names equal the source's: 4 libraries` and `the common library is the same file after every run`.
5. **Stage each app with its own upstream packaging script** (`debian/suite-stage.sh`): `packaging/linux/package.sh --skip-build --formats tar` gives the desktop file, icons, MIME types, AppStream data, documents and font licences as upstream ships them, and runs upstream's own `--version` smoke test against the libraries under their final names.
   The programs then move to `/usr/lib/craft-suite/` behind a launcher, and each library is installed under its SONAME.
6. **Gates**: `lean.release check-debs` writes the build record; `lean.release check-link` runs on the finished packages with the archive, the runtime package of the standard library as a sibling and the recipe's `smoke.tsv`.
7. **Prove it installed** as in the first recipe above, with the static build of the same sources as the reference for the files the command-line programs write.

### Vendoring several revisions of one workspace

- One vendor folder cannot hold two git revisions of a crate at one version, and here eleven revisions of one library repository are in use at once, so each git source is replaced by a folder of its own:
  ```toml
  [source."git+https://github.com/OWNER/REPO?rev=REV"]
  git = "https://github.com/OWNER/REPO"
  rev = "REV"
  replace-with = "suite-git-REPO-REV8"

  [source.suite-git-REPO-REV8]
  directory = "/path/vendor/git/REPO-REV8"
  ```
  `suite-source.py config` writes it from the merge's `sources.json`.
- A dependency on a sibling checkout (`path = "../craft-libs/crates/x"`) becomes `git = ..., rev = ...` in the generated copy, and the lock entries of those crates gain the matching `source` line: two path packages of one name and version cannot both be written to one lock, two git revisions can.
- Vendor per app and merge by the lock's `source`, checking that the same crate from the same source is the same bytes in every app.

### What the package is

| Package | Holds |
| --- | --- |
| `craft-suite-common` (all) | `/usr/share/craft-suite/versions.json` |
| `libcraft-suite-shared-0.ID` | the crates two or more apps link, and every crate those depend on |
| one per app | the launchers, the programs in `/usr/lib/craft-suite/`, `libAPP-shared-0.ID.so`, desktop file, icons, MIME types, AppStream data, documents |

Each app depends on exactly its common library, its compiler's `libstd-rust-HASH` and `craft-suite-common`, all written by `dh_makeshlibs -V"PACKAGE (= VERSION)"` and `dh_shlibdeps`.

**The app's own updater.** Each app checks its project's releases at start and, in a `.deb` install, would download and install upstream's package over the edition's.
The updater has its own switch for an app kept by something else: a version choices file, named by `CRAFT_VERSIONS_FILE`, in which an app pinned to a version "follows the launcher's choice" and neither asks a server nor offers anything.
The package ships that file with each app pinned to its packaged version, and the launcher exports the variable unless the person set one.
Check: with `RUST_LOG=info` the app logs `follows the launcher's choice (Managed(Pinned("0.20.1"))); no update offered here`.

### Measured (three apps, six programs, stripped, x86-64, four CPUs, load average 4 to 10)

- Static build of the same sources, upstream's profile, the same compiler and fonts: 718,388,976 bytes of programs.
- The packages: 390,053,320 bytes of programs and libraries with the standard library, 45.7 % less; `Installed-Size` 382,036 KiB in all; the archives 147.2 MB; the original archive 310 MB.
- The build: 6 min for the sources and build dependencies, 48 min for the build (about 15 min of projection, 31 min 46 s of cargo, then staging and the payload pass), a 7.7 GB tree.
- The files the command-line programs write (a PSD, a JPEG, a PNG frame) have the same SHA-256 as the static build's.

### Traps: the symptom, the cause, the fix, how it was found

- Symptom: the common library is compiled again in a later `cargo build`, after programs were already linked to it.
  Cause, first form: a crate inside the library that its list does not name (reached only through a unified feature, such as `rand` through `half`'s `rand_distr`, or `resvg` through `egui_extras`' `svg`) takes its features from the apps a cargo run selects.
  Fix: close each library's list over its dependencies in the all-apps resolve (here 341 named crates and 45 more).
  Cause, second form: the build side resolves per run too: a procedural macro's dependency (`serde_json` for `rmcp-macros`) had other features in another app's run, the macro was rebuilt, and with it a crate of the library.
  Fix: every cargo run selects every program of every app with every feature, so there is one resolve; apps with the same pinned fonts and catalogues share one run, and an app with other inputs gets a run of its own from which only its files are taken.
  The build script keeps the library's SHA-256 after the first run and stops when a later run changes it.
  Found by: `Compiling craft-suite-shared` appearing twice in the log, then `cargo tree -f '{p}|{f}'` per selection compared with the all-apps listing.
- Symptom: `error: failed to select a version for alsa-sys ... links to the native library alsa, but it conflicts with a previous package`.
  Cause: two apps need two major versions of a crate that links one native library (`cpal` 0.16 and 0.18), and one resolve holds one crate per `links` key.
  Fix: none in packaging; one app must move to the other's version, or it gets a workspace of its own and shares nothing.
  Found by: cargo's message, which names both chains.
- Symptom: `the source git+https://... requires a lock file to be present first before it can be used against vendored source code`.
  Cause: upstream's `[patch]` table names crates no app uses (its lock lists them under `[[patch.unused]]`), and cargo cannot look an unlocked git patch up in a folder.
  Fix: leave a git patch out of the generated root when no app's lock holds the crate; keep a patch on the app's own path crate, with an absolute path.
  Found by: the message names the patched crate.
- Symptom: `error: no source location specified for source.suite-git-winprint`.
  Cause: a repository name with a dot split the table name.
  Fix: write the replacement source's name with letters, digits and hyphens only.
- Symptom: a vendored crate "is in no source of the app".
  Cause: `cargo metadata` without `--all-features` leaves out optional dependencies that `cargo vendor` copies.
  Fix: map vendored crates to their sources from `Cargo.lock`.
- Symptom: a context patch for the generated copy applies to the authored tree and not to the projected one.
  Cause: its context holds a plain comment, which the projection removed.
  Fix: `suite-fixups.json` names the whole line to change and its replacement, and stops unless the line is there exactly once.
- Symptom: `error[E0050]: method on_exit has 1 parameter` in a second app.
  Cause and fix: the same unified `eframe` feature as in the two-app proof; every app without the feature gets the fixup.
- Symptom: `dpkg-buildpackage -nc` on a tree that failed after its compile stops with `FileExistsError: .../suite`.
  Cause: debhelper runs the configure override again.
  Fix: build again from the source; a compiled tree is not continued.
- Symptom: two source runs at two recipe commits give two original archives.
  Cause: the archive was dated by the recipe.
  Fix: date it by the release it names; `debian/` keeps the recipe's date.
- Symptom: the build stops in `override_dh_builddeb` on the link gate.
  Cause: the compile container has no network to resolve run-time dependencies.
  Fix: as in the compiler's recipe, the gate runs on the finished packages.
- Symptom: upstream's packaging script says an app's man pages and completions "are left out".
  Cause: they are written by an example that needs the app's development dependencies, which the one workspace drops.
  Fix: none yet; the recipe records it under `not_packaged`.

### Not proven here

The two other apps of the first five (one waits for the `links` conflict, one for its build and proofs), arm64, the suite on a quiet machine, lintian, and a publication with the generated pin against Debian's compiler.

## Not proven here

The whole suite (three of about twenty apps are packaged); timing on a quiet machine; the compiler's own test suite, which the compiler's recipe does not run; the compiler's Rust sources through the Rust adapter; arm64.
Two builds of the same tree by the same compiler gave byte-identical programs and libraries.
