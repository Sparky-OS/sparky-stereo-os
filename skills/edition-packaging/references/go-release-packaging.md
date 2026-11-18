# Reconcile a Go release before packaging it

## Working recipe

1. Read upstream's latest release and tags separately, record the selected tag's commit, and start the packaging branch there.
   Fetch its source archive from upstream, record its SHA-256, check any published signature, and compare every archive file with the checkout.
2. Read `go.mod`, including `go`, `toolchain`, every `require` block and every `replace` directive.
   Record declared and effective dependency versions separately.
3. Refresh the target Debian suite in an isolated container and save `apt-cache policy` for the toolchain and each candidate development package.
   Compare module repository URLs with package homepages and search package names; record the lookup method and its limits.
4. Choose the dependency route explicitly.
   Use Debian's Go packages where the required modules and compatible versions are available and that route satisfies the task's source contract.
   When the contract requires an unchanged release dependency graph that the archive cannot supply, prepare vendored source and its licence inventory instead.
5. Search the release tree for `*_test.go`, build workflows and compatibility scripts.
   Record which tests actually exist before promising a test-suite result.
6. Keep the dependency inventory and commands with the build record.
   Stop this reconciliation milestone before claiming a built package; vendoring, offline builds, reproducibility, installed smoke checks, lintian and the edition's release gate need their own evidence.

The [Go module reference](https://go.dev/ref/mod#vendoring) describes `go mod vendor` and the `-mod=vendor` build mode.
The [Debian Go packaging guide](https://go-team.pages.debian.net/packaging.html) describes Debian's package conventions and `dh-golang`.
Dependency preparation is separate from the package build, which must not fetch source from the network.
Keep upstream's module files unchanged when the task requires an unmodified tagged release.
If vendoring asks to update them, retain the failure and reconcile it with upstream before changing the release.
Review dependency licences as well as the top-level licence.

Run `go mod download`, `go mod verify`, then `go mod vendor` in the disposable source tree.
Set `GOTOOLCHAIN=local` and `GOFLAGS=-mod=readonly` when the build contract requires the packaged module files unchanged.
Check their hashes before and after preparation.
Repeat vendoring with `GOPROXY=off` in a container with networking disabled before calling the dependency input complete.
Successful module downloads and checksum verification alone do not establish that all imports can be built.

## Traps found during release reconciliation

- **Symptom:** an inventory lists `golang.org/x/crypto v0.45.0`, but the release selects v0.38.0.
  **Cause:** the inventory read `require` and skipped `replace`.
  **Fix:** carry both declared and effective versions into the dependency inventory.
  **Found by:** reading the final two directives in edgetk v1.5.21's `go.mod`.
- **Symptom:** `apt-cache dumpavail` contains no `Go-Import-Path` fields.
  **Cause:** that archive's binary package records do not expose module paths through this field.
  **Fix:** compare upstream homepages and normalized package names, then verify candidates with `apt-cache policy`.
  Report an unmatched lookup as such; it does not prove that no differently named Debian source carries the code.
  **Found by:** checking all 70,958 binary records in a Forky amd64 archive snapshot during lane edgetk-package-511.
- **Symptom:** a release has compatibility scripts but no Go test cases.
  **Cause:** examples and cross-tool scripts were mistaken for a unit test suite.
  **Fix:** inventory the actual test files, run available checks in a container, and state the separate scope of installed smoke checks.
  **Found by:** the edgetk v1.5.21 tree had 38 files and no `*_test.go` or Actions workflow.

- **Symptom:** `go mod verify` prints `all modules verified`, then `go mod vendor` reports `no required module provides package`.
  **Cause:** edgetk v1.5.21 imports curupira2, m511, smaz, snow2 and sosemanuk without a requirement in the resolved module graph.
  **Fix:** when the contract requires that release's exact dependency graph, stop packaging and retain the missing-module diagnostics for upstream's next complete release.
  Do not follow the diagnostic's `go get` suggestion or invent dependency versions.
  **Found by:** Go 1.27.3 in Forky, first with network access and then with `GOPROXY=off` and `--network none`; both vendoring attempts failed on the same five imports while go.mod and go.sum hashes stayed identical.
- **Symptom:** removing a Go module cache with an ordinary recursive deletion leaves directories behind or reports `Directory not empty`.
  **Cause:** downloaded modules have read-only directories; changing a file's mode alone does not make its parent directory writable for deletion.
  **Fix:** use `go clean -modcache` inside the build container with its task-owned GOMODCACHE, or make directories writable before removing that known cache tree.
  Never apply the cleanup to a shared cache.
  **Found by:** a failed Python cache cleanup during lane edgetk-package-511; making the cache directories writable allowed complete removal.

## Measured reconciliation

On 2026-11-11 UTC, edgetk v1.5.21 declared 117 modules.
Six matched the Forky package lookup above; five of those archive versions differed from the effective pinned versions.
This supports a vendored build route for that unchanged release; it does not establish module download success, an offline build or cryptographic correctness.

## Check the complete toolchain contract after vendoring

1. Check the APIs the command actually calls before pinning a newly declared module.
   A higher semantic version can omit aliases the caller still uses.
   In m511, v0.0.0-psi provides ParsePrivateKey and MarshalPKCS8PublicKey, while v0.0.0-rho does not.
   That compatibility distinction was established from the tagged source, not inferred from the version names.
2. For an upstream dependency fix that has merged but has no tag, verify tag ancestry and ask Go for the canonical pseudo-version of the exact merge commit.
   For example, `go mod download -json MODULE@COMMIT` returns Version and Origin.Hash; retain those fields and the checksums.
   Do not construct the timestamp by hand or assume `@latest` includes an untagged fix.
3. Run the actual command build in a clean container with networking disabled and only vendored dependencies available.
   Keep application source unchanged while assessing a module-only proposal.
   Separate a successful vendor input from a successful command build and an installed-package test.

- **Symptom:** download, tidy, verification and vendoring succeed, but compilation says `package crypto/go.cypherpunks.su/gogost/v6/gost3410 is not in std`.
  **Cause:** this edgetk source names a package below the standard-library crypto namespace; module reconciliation cannot supply it.
  A diagnostic import substitution then exposed EncryptAsn1/DecryptAsn1 calls missing from standard crypto/ecdsa types.
  **Fix:** obtain upstream's reproducible standard-library/toolchain input, or prepare a separately reviewed source adaptation with its encryption behavior established first.
  Never silently substitute a different encryption implementation to make a dependency-only PR compile.
  **Found by:** clean offline Forky builds of both dependency branches with Go 1.27.3, followed by the compiler output from a disposable one-line diagnostic substitution and `go doc crypto/ecdsa.PublicKey` / `PrivateKey`.

That block was upstream's to lift, and it was: on 2026-11-13 the author replaced the modified standard-library packages with an ordinary module (`gitverse.ru/uzer_007/gogost/v2`) and dropped the calls stock Go lacks, so commit a8e445b ("v1.5.22") builds with standard Go.
The section below is the package that followed.

## The vendored build, with modules hosted outside GitHub (edgetk 1.5.22, ORDER 511)

1. **Where the modules come from.** Run the download once with a new, empty `GOMODCACHE` and `GOPROXY=https://proxy.golang.org` (no `,direct`): if it succeeds, every module, whatever host its path names, came from the Go module proxy and no version-control host was contacted.
   edgetk's 126 modules did, the two on gitverse.ru and the one on gitee.com included, so the build container needs neither `git` nor access to those hosts.
   Record each module's source as its proxy address (`https://proxy.golang.org/MODULE/@v/VERSION.zip`, capitals written as `!x`) with the `h1:` line of upstream's own `go.sum`; `go mod verify` is the integrity check, and `sum.golang.org` is never asked for a module `go.sum` already names.
   A module the proxy does not hold would fail here by name: that one needs `GOPROXY=...,direct`, `git` in the container and its host reachable, and is recorded as such.
2. **Keep upstream's module files unchanged.** Take the SHA-256 of `go.mod` and `go.sum` before `go mod download`, `go mod verify`, `go mod vendor` and check them after (`sha256sum -c`), with `GOFLAGS=-mod=readonly`.
   Never build with `-mod=mod`: it rewrote edgetk's `go.mod` (six requirements lost `// indirect`) without saying a word.
3. **The vendor tree is an upstream tarball of its own** (`NAME_V.orig-vendor.tar.xz`, a component of a 3.0 (quilt) source, unpacked in `vendor/`), made with `tar --sort=name --format=gnu --mtime=@COMMIT_TIME --owner=0 --group=0 --numeric-owner` so the same commit gives the same bytes.
   Pin the tree, not the tarball: the SHA-256 of the sorted `sha256sum` list of every file under `vendor/` stays the same across tar and xz versions and across Go patch releases (Go 1.27.1 and Debian's 1.27.4 gave the same tree).
4. **The package build reads no network:** `GOTOOLCHAIN=local GOPROXY=off GOFLAGS="-mod=vendor -trimpath -buildvcs=false" CGO_ENABLED=0`, `GOCACHE` and `HOME` inside `debian/`, `dh $@ --buildsystem=none` with `go build -o debian/.build/NAME ./cmd/NAME`.
   Use Debian's Go when it is at least the `go` line of `go.mod` (`apt-cache policy golang-go golang-1.NN-go` in the build image; Forky had 1.27.4 for `go 1.27.1`); `GOTOOLCHAIN=local` then stops Go from fetching another toolchain.
5. **Licences come from the module cache, one row per module.** For each module of `vendor/modules.txt`, read the licence files at the module's root in the cache (`GOMODCACHE/MODULE@VERSION/`), classify the text, and when there is none read the first lines of its Go files for a statement.
   Generate `debian/copyright` from that table and let the build stop when the committed file differs from the generated one (`cmp`), so the file cannot go stale when a module changes.
   Name what is missing as it is: edgetk vendors 123 modules, 63 of them (all in the author's own account) have no licence file, 22 of those state a licence in their sources, and 41 state nothing; they are listed as `not-stated`, never guessed.
   One copyleft module decides the binary: `github.com/pedroalbanese/gogost` is GPL-3 (Sergey Matveev's GoGOST), so the static program is distributed under GPL-3 terms though edgetk itself is ISC; say so in the header of `debian/copyright`.
6. **Lean Code: preserve `vendor/`.** The toolkit's source projection reads `.h` and `.c` as C. In a Go vendor tree the `.h` files are Go assembler headers (`#include`d by `.s` files, read by `cmd/asm`) and the `.c` files are for gccgo.
   Ship `debian/sparky-lean-preserve.json` with the one pattern `vendor/*` and its reason, in the form `lean.debian_prepare` writes (`json.dumps(plan, indent=2)` and a newline); `release/build-dh-lean.sh` has no option for `--preserve-source`, and a plan already in `debian/` is the one the build reads.
7. **Tests at build time.** When the tree has a Go test, `override_dh_auto_test` runs it; with a `main.go` that `go vet` objects to, that is `go test -count=1 -vet=off ./cmd/NAME/`.

### Traps

- **Symptom:** the build stops in `execute_before_dh_auto_configure` with `vendor/.../mul_amd64.h: check failed: GCC sees different tokens or directives`. **Cause:** a Go assembler header taken for a C header by the Lean Code source projection. **Fix:** the preserve plan of step 6. **How found:** the file's first lines are Plan 9 assembler macros, and only `.s` files include it.
- **Symptom:** `dwz: debian/NAME/usr/bin/NAME: Unknown debugging section .debug_addr`, then `dh_dwz: error`. **Cause:** dwz does not read the DWARF 5 sections a Go binary carries. **Fix:** an empty `override_dh_dwz:` in `debian/rules`, as dh-golang does for every Go package. **How found:** the build and its test had passed; the error names the tool and the section.
- **Symptom:** `make: Warning: File 'debian/rules' has modification time 1431 s in the future`. **Cause:** the changelog entry's date was later than the clock, and the source is dated by its newest changelog entry. **Fix:** date the entry at or before the moment it is written (`date -u -R`).
- **Symptom:** a wrapper prints "exit 0" for a build that failed. **Cause:** `(time build) > log; echo $?` followed by `tail` reports the last command. **Fix:** write the build's own status into the log (`build > log 2>&1; echo "BUILD EXIT $?" >> log`) and read that line.
- **Symptom:** a licence scan of `vendor/` finds fewer licence files than the module cache. **Cause:** `go mod vendor` copies only the packages a build needs, with the legal files beside them; a module's other folders stay behind. **Fix:** scan the module's root in the cache, which holds the whole module as published.
- **Symptom:** lintian reports `license-problem-undefined-license bsd-unspecified` on a generated `debian/copyright`. **Cause:** a made-up short name that begins like a real licence family is taken for a reference to a licence with no text. **Fix:** name such a stanza by what the file says (`licence-file-says-only-BSD`), with its own paragraph. **How found:** the two lines lintian named were the stanza and its paragraph.
- **Symptom:** a licence classifier calls a GPL text "GPL and LGPL". **Cause:** the GPL's own text names the Lesser GPL. **Fix:** decide GNU licences by the title in the first lines, not by a phrase anywhere in the text.

### Measured on edgetk 1.5.22 (a8e445b), 2026-11-13

The source package is 278 KB of upstream and 2.97 MB of vendored modules (1,874 files, 26 MB unpacked); the binary package is 4.5 MB with one static program of 18 MB.
One build through `release/build-dh-lean.sh` takes about four and a half minutes on four cores, the Go compile twice (the program, then its test binary).
The Lean Code gates pass with nothing projected in the source (the seven eligible files are all in `vendor/` and preserved) and nothing to project in the payload.
lintian 2.143.0 leaves two errors that belong to the edition's toolkit on every package (`gcc` in Build-Depends without a version, the lc record in the debug package) and `no-manual-page`, since upstream ships no manual.

## A second program, with cgo, a service and a state folder (OpenLinkHub 0.9.4, ORDER 108 milestone 7)

OpenLinkHub (Nikola Jurkovic; the Corsair iCUE LINK web interface; GPL-3.0) is the first Go program here that is a **service with cgo**: libpipewire-0.3 and libudev through cgo, seven vendored modules (`vendor/modules.txt` has 43 lines), `go vet` as its only check (no `*_test.go`), a web page on 127.0.0.1:27003. The recipe is `sparky-os/packages/openlinkhub`; everything above applies, and the differences are these.

1. **Pin the tag by four things, not one.** `make-orig.sh` checks the codeload tarball's SHA-256, the commit the tarball names (a tar `pax` global header `comment`), the **git tree id** of the unpacked files (`git add -A -f` into a bare index, `git write-tree`) against the commit's tree, and then the vendor tree's sorted-hash fingerprint. The tarball's bytes may change when GitHub's compressor does; the tree id cannot. A rerun gave byte-identical `orig` and `orig-vendor` archives once `umask 022` was set in the script: a container user's default umask 002 had put mode 0775 on every directory.
2. **cgo in a Debian build.** Build-depends `libpipewire-0.3-dev libudev-dev pkgconf` and Debian's `golang-go`; `CGO_ENABLED=1`, `CGO_CFLAGS` and `CGO_LDFLAGS` from `dpkg-buildflags` so the hardening flags reach the C part, `-buildmode=pie`. Do not list `gcc` or `libc6-dev` in Build-Depends: build-essential has them, and lintian calls each an unversioned build-essential dependency, an error (the toolkit adds `gcc` itself, so that one error stays as for edgetk; `libc6-dev` did not).
3. **`CGO_CFLAGS_ALLOW` (trap).** *Symptom:* `go build: invalid flag in pkg-config --cflags: -fno-strict-overflow`. *Cause:* libpipewire-0.3's `.pc` file asks for `-fno-strict-overflow`, and cgo accepts only the compiler flags it knows unless told. *Fix:* `export CGO_CFLAGS_ALLOW = -fno-strict-overflow` in `debian/rules` (an exact-match regular expression; never `.*`). *Found by:* the first measured build in a container, after the earlier failure for lack of `libc6-dev` (cgo needs the C headers: `gcc` alone is not enough).
4. **A program that reads its own working folder.** OpenLinkHub finds `config.json`, `database/`, `web/` and `static/` relative to `os.Getwd()`, and writes `config.json`, `dashboard.json`, `display.json`, `audio.json`, `scheduler.json`, `stdout.log` and its profiles there. The program is not changed. Filesystem hierarchy: `/usr/bin/OpenLinkHub`; the page's files and default database in `/usr/share/openlinkhub`; `WorkingDirectory=/var/lib/openlinkhub` with `StateDirectory=openlinkhub`; an `ExecStartPre` helper (`openlinkhub-seed`, run as the service's user) links `web` and `static` and copies the default database **by a manifest of hashes**: a file not there is copied, a file still byte for byte as the helper copied it is replaced by a newer default, a file changed (by the person or by the program) is never touched, a file the person deleted is not brought back. Proof: 108 files copied at the first start, then "1 copied, 1 replaced, 106 left as they are" after an upgrade that changed three defaults and added one.
5. **The toolkit owns `execute_before_dh_auto_configure`.** *Symptom:* `Existing execute_before_dh_auto_configure: preserve and integrate its behavior explicitly` and the build stops before compiling. *Cause:* `lean.debian_prepare` adds its own hook of that name and refuses a recipe that has one. *Fix:* the copyright `cmp` goes into `override_dh_auto_build`.
6. **`debhelper-compat (= 14)` for sysusers.** With compat 13 `dh_installsysusers` does not run: the file is not installed and the user is never made, the unit then fails to start as `openlinkhub`. At 14 the helper installs `usr/lib/sysusers.d/openlinkhub.conf` and adds the `systemd-sysusers` call to `postinst` before the recipe's own lines.
7. **The unit's enable and the person's disable.** `override_dh_installsystemd:` is empty and `postinst` carries dh's own snippet (`deb-systemd-helper unmask`, `was-enabled` then `enable` or `update-state`, then `daemon-reload` and `deb-systemd-invoke start` on a first install or `restart` on an upgrade), because the stock snippet would also stop and restart a service of the same name that upstream's own scripts installed in `/etc/systemd/system`. Proved under systemd: installed enabled and active; `systemctl disable --now` then an upgrade leaves it disabled and inactive; a purge and a new install is enabled again (the helper's record goes with the purge).
8. **`cpu-baseline.py` cannot pass a Go program, and what proves it instead.** *Symptom:* `6620 instructions above the amd64 baseline, of 86 kinds` on a binary built with `GOAMD64=v1`. *Cause:* Go's standard library and `x/crypto` carry AES-NI, AVX2, SHA-NI, CLMUL, POPCNT and SSE4.1 assembly that the runtime chooses by CPUID (`crypto/internal/fips140/aes/gcm`, `chacha20poly1305`, `sha256.blockAVX2`, `internal/runtime/gc/scan`), and the compiler's own `POPCNT` and `ROUNDSD` sit behind a `test flag; je` on the CPU-feature byte (`runtime.x86HasPOPCNT`, `x86HasSSE41`), also in the program's own functions. The check counts instructions, not reachability. *Proof:* (a) `go version -m` / the binary's build info says `GOAMD64=v1`; (b) a control program with `aesenc` dies on `qemu-x86_64 -cpu qemu64` (exit 132) and runs on `-cpu max`; (c) the real program runs on `-cpu qemu64`, serves its web page (200 after 3 s) and logs no illegal instruction. The recipe keeps (b) and (c) as `tests/baseline-qemu.sh`. Mapping hits to functions needs the unstripped symbols: `nm -n` of the `-dbgsym` package's `.debug` file against `objdump -d` of the stripped program (the stripped binary has no `.symtab`, and `go tool objdump` refuses it).
9. **Licences with a bundled project.** `vendor-licences.py` reads the module cache (not `vendor/`) and records, per module, the legal files with their SHA-256, the licence the files state (a module that offers a choice, freetype's "FreeType License or GPL 2 or later", is named as such, and the stanza takes the one the whole program's licence allows), and for go-hid the licence its bundled hidapi C headers state (GPL v3, a BSD-style licence or the original HIDAPI licence; go-hid's own LICENSE is BSD-2-Clause). A directory called `licenses/` counts as legal files. The legal files are installed in `/usr/share/doc/openlinkhub/vendor-licences/` and `debian/copyright` quotes them.
10. **lc1 on a Go program with a little C.** The language plan found `c` for `src/audio/audio.c` and `audio.h` (the header is projected: 17 comments removed, and the program built from it), and `vendor/*` is preserved as for edgetk. The Go files have no adapter yet: they stay authored, the build record's `preserve` names the vendor tree and the changelog names the Go files, and the Go adapter is the next piece of work.

### Measured on OpenLinkHub 0.9.4 (a08204cf), 2026-11-17

Source package: 2.97 MB of upstream (861 files) and 0.75 MB of vendored modules. Binary package 9.5 MB with one dynamically linked PIE of 33 MB (libpipewire-0.3, libudev, libc, libm). One build through `release/build-dh-lean.sh`: about two and a quarter minutes on four cores. Lintian leaves the toolkit's own two errors (`no-changelog` for the `-lc-hr` package, a non-debug file in the `-dbgsym` package), and warnings for upstream's bundled jQuery and fonts (`embedded-javascript-library`, `font-in-non-font-package`: the web page's files, not changed), `no-manual-page` and `national-encoding` for freetype's verbatim legal text.
