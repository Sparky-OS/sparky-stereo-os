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
