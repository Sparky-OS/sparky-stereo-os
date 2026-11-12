# A Rust suite as shared libraries

Learned on storytold's Craft suite in November 2026 (PhotoCraft 0.23.1 and LightCraft 0.21.1, Rust 1.99.1): about twenty Rust applications that share most of their dependencies and each ship as one or two statically linked programs.
Daniel asked for the suite "the debian way - shared libraries", so the code the apps have in common is installed once.
This page is the recipe that worked on two apps, with its numbers, and every trap met on the way.
It is a proof on two apps, in test packages; the whole suite, the Lean Code gate and the edition's own Rust toolchain are still to do.

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

The scripts are in this skill's [`scripts/`](../scripts) folder.

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

## Not proven here

The whole suite; the Lean Code gate and the link and start gate on real `+lc1` packages; a second build giving the same library for the same id; timing on a quiet machine; the edition's Rust toolchain built from source.
