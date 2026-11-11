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
